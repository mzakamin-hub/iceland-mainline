#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Boot an arm64 Linux Image as a protected Gunyah VM through /dev/gunyah (1 vCPU, lent memory, one process).

usage: gh_boot.py IMAGE [RAM_MiB] [TIMEOUT_s]     (default 64 MiB, 60 s)
       gh_boot.py --dtb OUT.dtb [RAM_MiB]          (write the guest device tree only; needs no /dev/gunyah)

The guest console is an emulated 16550 UART at GPA 0x10000000 (32-bit registers, reg-shift 2): every guest access
is an MMIO exit that this tool answers (THR writes go to stdout, LSR reads say "transmitter empty"). The kernel
needs a built-in initramfs (the guest kernel of build-guest.sh). PASS = the guest powers off (PSCI SYSTEM_OFF) with an
EXITED status. Based on gh_vmtest.py (SuperTurtleDev's smoke-test VMM); never forks while it holds lent memory.
"""
import ctypes, fcntl, mmap, os, signal, struct, sys, time


def _IOC(d, t, nr, size): return (d << 30) | (size << 16) | (ord(t) << 8) | nr
def _IO(t, nr): return _IOC(0, t, nr, 0)
def _IOW(t, nr, size): return _IOC(1, t, nr, size)


GUNYAH_CREATE_VM = _IO("G", 0x0)
GUNYAH_VM_SET_DTB_CONFIG = _IOW("G", 0x2, 16)
GUNYAH_VM_START = _IO("G", 0x3)
GUNYAH_VM_ADD_FUNCTION = _IOW("G", 0x4, 16)
GUNYAH_VCPU_RUN = _IO("G", 0x5)
GUNYAH_VCPU_MMAP_SIZE = _IO("G", 0x6)
GUNYAH_VM_SET_BOOT_CONTEXT = _IOW("G", 0xa, 16)
GH_VM_ANDROID_LEND_USER_MEM = _IOW("A", 0x11, 32)
GUNYAH_FN_VCPU = 1
MEM_RWX = 0x7
REG_SET_X = 0 << 8      # GUNYAH_VM_BOOT_CONTEXT_REG_SET_X (reg index in the low byte)
REG_SET_PC = 1 << 8

RAM_BASE = 0x80000000
UART = 0x10000000
UART_SIZE = 0x1000
GICD, GICR = 0x3FFF0000, 0x3FFD0000
BOOTARGS = "earlycon=uart8250,mmio32,0x10000000 console=ttyS0 rdinit=/init panic=-1"


class FDT:
    def __init__(self):
        self.struct = bytearray(); self.strings = bytearray(); self.stroff = {}
    def _str(self, s):
        if s not in self.stroff:
            self.stroff[s] = len(self.strings); self.strings += s.encode() + b"\0"
        return self.stroff[s]
    def _pad(self):
        while len(self.struct) % 4: self.struct += b"\0"
    def begin(self, name):
        self.struct += struct.pack(">I", 1) + name.encode() + b"\0"; self._pad()
    def end(self): self.struct += struct.pack(">I", 2)
    def prop(self, name, val=b""):
        self.struct += struct.pack(">III", 3, len(val), self._str(name)) + val; self._pad()
    def s(self, name, *vals): self.prop(name, b"".join(v.encode() + b"\0" for v in vals))
    def u32(self, name, *vals): self.prop(name, struct.pack(">%dI" % len(vals), *vals))
    def u64(self, name, *vals): self.prop(name, struct.pack(">%dQ" % len(vals), *vals))
    def blob(self):
        self.struct += struct.pack(">I", 9)
        hdr = 40; rsv = hdr; st = rsv + 16; strs = st + len(self.struct); total = strs + len(self.strings)
        return struct.pack(">IIIIIIIIII", 0xd00dfeed, total, st, strs, rsv, 17, 16, 0,
                           len(self.strings), len(self.struct)) + b"\0" * 16 + bytes(self.struct) + bytes(self.strings)


def build_dtb(ram_size):
    """The smoke test's RM-accepted layout (gh_vmtest.py) plus a 16550 UART node and the console bootargs."""
    f = FDT()
    f.begin("")
    f.u32("#address-cells", 2); f.u32("#size-cells", 2)
    f.s("compatible", "linux,dummy-virt"); f.u32("interrupt-parent", 1)
    f.begin("gunyah-vm-config")
    f.s("image-name", "iceland-guest"); f.s("os-type", "linux"); f.s("vm-type", "aarch64-guest")
    f.begin("memory"); f.u32("#address-cells", 2); f.u32("#size-cells", 2)
    f.u64("base-address", RAM_BASE); f.u64("size-max", 0x40000000); f.end()
    f.begin("interrupts"); f.s("config", "/intc"); f.end()
    f.begin("vcpus"); f.s("affinity", "proxy"); f.end()
    f.begin("vdevices"); f.s("generate", "/hypervisor"); f.end()
    f.end()
    f.begin("cpus"); f.u32("#address-cells", 1); f.u32("#size-cells", 0)
    f.begin("cpu@0"); f.s("device_type", "cpu"); f.s("compatible", "arm,armv8"); f.u32("reg", 0)
    f.s("enable-method", "psci"); f.u32("phandle", 0x100); f.end()
    f.end()
    f.begin("memory"); f.s("device_type", "memory"); f.u64("reg", RAM_BASE, ram_size); f.end()
    f.begin("intc"); f.s("compatible", "arm,gic-v3"); f.u32("#interrupt-cells", 3); f.prop("interrupt-controller")
    f.u32("#address-cells", 2); f.u32("#size-cells", 2); f.u64("reg", GICD, 0x10000, GICR, 0x20000)
    f.u32("phandle", 1); f.end()
    f.begin("psci"); f.s("compatible", "arm,psci-1.0", "arm,psci-0.2"); f.s("method", "hvc"); f.end()
    f.begin("timer"); f.s("compatible", "arm,armv8-timer")
    f.u32("interrupts", 1, 13, 0x108, 1, 14, 0x108, 1, 11, 0x108, 1, 10, 0x108); f.prop("always-on"); f.end()
    f.begin("uart@10000000"); f.s("compatible", "ns16550a"); f.u64("reg", UART, UART_SIZE)
    f.u32("reg-shift", 2); f.u32("reg-io-width", 4); f.u32("clock-frequency", 1843200); f.end()  # no IRQ: polled
    f.begin("chosen"); f.s("bootargs", BOOTARGS); f.s("stdout-path", "/uart@10000000"); f.end()
    f.end()
    return f.blob()


def uart_read(off):
    reg = off >> 2
    if reg == 5:
        return 0x60      # LSR: THR empty, transmitter empty
    if reg == 2:
        return 0x01      # IIR: no interrupt pending
    return 0


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--dtb":
        ram = (int(sys.argv[3]) if len(sys.argv) > 3 else 64) << 20
        open(sys.argv[2], "wb").write(build_dtb(ram))
        print("wrote %s" % sys.argv[2]); return 0
    if len(sys.argv) < 2:
        print(__doc__); return 2
    image = open(sys.argv[1], "rb").read()
    ram_size = (int(sys.argv[2]) if len(sys.argv) > 2 else 64) << 20
    timeout = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0
    if len(image) < 64 or struct.unpack_from("<I", image, 56)[0] != 0x644D5241:
        print("FAIL not an arm64 Image (no ARM\\x64 magic)"); return 1
    text_offset, image_size = struct.unpack_from("<QQ", image, 8)
    dtb = build_dtb(ram_size)
    dtb_off = ram_size - 0x200000                       # DTB 2 MiB below the end of RAM, 8-byte aligned
    if text_offset + max(image_size, len(image)) > dtb_off:
        print("FAIL image (%d B, image_size %d) does not fit below the DTB at +%#x" % (len(image), image_size, dtb_off))
        return 1

    dev = os.open("/dev/gunyah", os.O_RDWR)
    vm = fcntl.ioctl(dev, GUNYAH_CREATE_VM)
    mem = mmap.mmap(-1, ram_size, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS, prot=mmap.PROT_READ | mmap.PROT_WRITE)
    mem[0:ram_size] = b"\0" * ram_size
    uaddr = ctypes.addressof(ctypes.c_char.from_buffer(mem))
    mem[text_offset:text_offset + len(image)] = image
    mem[dtb_off:dtb_off + len(dtb)] = dtb
    print("[1] guest RAM %d MiB @ %#x, Image %d B @ +%#x, dtb %d B @ +%#x" % (ram_size >> 20, RAM_BASE, len(image),
          text_offset, len(dtb), dtb_off))
    fcntl.ioctl(vm, GH_VM_ANDROID_LEND_USER_MEM, struct.pack("<IIQQQ", 0, MEM_RWX, RAM_BASE, ram_size, uaddr))
    fcntl.ioctl(vm, GUNYAH_VM_SET_DTB_CONFIG, struct.pack("<QQ", RAM_BASE + dtb_off, 0x10000))
    fcntl.ioctl(vm, GUNYAH_VM_SET_BOOT_CONTEXT, struct.pack("<IIQ", REG_SET_PC, 0, RAM_BASE + text_offset))
    fcntl.ioctl(vm, GUNYAH_VM_SET_BOOT_CONTEXT, struct.pack("<IIQ", REG_SET_X | 0, 0, RAM_BASE + dtb_off))
    print("[2] LEND_USER_MEM, SET_DTB_CONFIG, boot context pc=%#x x0=%#x ok" % (RAM_BASE + text_offset, RAM_BASE + dtb_off))
    vcpu_arg = ctypes.c_uint32(0)
    vcpu = fcntl.ioctl(vm, GUNYAH_VM_ADD_FUNCTION, bytearray(struct.pack("<IIQ", GUNYAH_FN_VCPU, 4,
                       ctypes.addressof(vcpu_arg))), True)
    run = mmap.mmap(vcpu, fcntl.ioctl(vcpu, GUNYAH_VCPU_MMAP_SIZE), flags=mmap.MAP_SHARED,
                    prot=mmap.PROT_READ | mmap.PROT_WRITE)
    fcntl.ioctl(vm, GUNYAH_VM_START)
    print("[3] VM_START ok; guest console follows", flush=True)

    class Timeout(Exception):
        pass

    def on_alarm(_sig, _frm):
        raise Timeout()
    signal.signal(signal.SIGALRM, on_alarm)       # a guest idling in WFI keeps VCPU_RUN in the kernel
    signal.setitimer(signal.ITIMER_REAL, timeout)
    t0 = time.monotonic(); exits = 0; result = "TIMEOUT"
    while True:
        try:
            fcntl.ioctl(vcpu, GUNYAH_VCPU_RUN)
        except Timeout:
            break
        except OSError as e:
            result = "VCPU_RUN errno %d (%s)" % (e.errno, e.strerror); break
        exits += 1
        reason, = struct.unpack_from("<I", run, 8)
        if reason == 1:                                          # MMIO
            pa, data, ln, is_w = struct.unpack_from("<Q8sIB", run, 16)
            if UART <= pa < UART + UART_SIZE:
                if is_w and (pa - UART) >> 2 == 0:
                    c = data[0]
                    sys.stdout.write(chr(c) if c in (9, 10, 13) or 32 <= c < 127 else "?")
                    if c == 10: sys.stdout.flush()
                elif not is_w:
                    struct.pack_into("<Q", run, 24, uart_read(pa - UART))
            else:
                print("\n[4] MMIO %s outside the UART: pa=%#x len=%d" % ("write" if is_w else "read", pa, ln))
                if not is_w: struct.pack_into("<Q", run, 24, 0)
            struct.pack_into("<B", run, 37, 0)                   # resume_action = HANDLED
        elif reason == 2:                                        # STATUS
            st, ty, _pad, rsz, why = struct.unpack_from("<IHHI8s", run, 16)
            result = "STATUS %s exit_type=%d reason=%s" % ({1: "LOAD_FAILED", 2: "EXITED", 3: "CRASHED"}.get(st, st),
                                                           ty, why[:rsz].hex()); break
        elif reason == 3:                                        # PAGE_FAULT not resolved by the kernel
            pa, attempt = struct.unpack_from("<Qi", run, 16)
            result = "PAGE_FAULT pa=%#x attempt=%d" % (pa, attempt); break
        else:
            result = "exit_reason %d" % reason; break
    sys.stdout.flush()
    print("\n[5] %s after %d exits, %.2f s -> %s" % (result, exits, time.monotonic() - t0,
          "PASS" if result.startswith("STATUS EXITED") else "FAIL"))
    run.close(); os.close(vcpu); os.close(vm); os.close(dev)
    return 0 if result.startswith("STATUS EXITED") else 1


if __name__ == "__main__":
    sys.exit(main())
