# Gunyah virtual machines (side package)

The OnePlus Pad 4's firmware runs Linux as a guest of Qualcomm's Gunyah hypervisor. This directory holds the
pieces that let Linux create its own **protected** virtual machines through `/dev/gunyah`: the VM-manager drivers
as out-of-tree modules for a kernel-iceland kernel, a small test VMM and the smoke test that ran on our unit.

This is a side package: the patches are **not** in the iceland-linux kernel queue, kernel-iceland does not build or
ship these modules, and nothing loads them at boot.

## Credit and origin

The drivers are SuperTurtleDev's import of the Gunyah stack of Android's common kernel, from their Pad 4 kernel
[SuperTurtleDev/iceland-mainline-kernel-linux](https://github.com/SuperTurtleDev/iceland-mainline-kernel-linux)
(branch `iceland-7.2`):

| Patch | Origin |
|---|---|
| 0001 virt: gunyah: import Gunyah hypervisor drivers from android17-6.18 | SuperTurtleDev `645096c6bbc1`, unchanged |
| 0002 virt: gunyah: adapt to mainline 7.2 | SuperTurtleDev `91d78aa40296`, unchanged |
| 0003 tools: virt: gunyah: add VM smoke test and record verification results | SuperTurtleDev `56944665c1a3`, unchanged |
| 0004 virt: gunyah: follow the v7.3 rename of the file rmap interval tree | ours (needed to build on Linux 7.3) |
| 0005 tools: virt: gunyah: add a "hello" mode to the VM smoke test | ours |

0001-0003 keep SuperTurtleDev's authorship and messages exactly as in their commits (rebased onto our tree, so the
commit ids in the patch headers differ). Their commits carry **no `Signed-off-by`**; we have not added one for
them. The code comes from the Android common kernel (`android17-6.18`, Qualcomm Innovation Center copyright
headers) and is licensed GPL-2.0 like the kernel. The Gunyah VM manager was posted upstream several times
("Drivers for Gunyah hypervisor") but was never merged; upstream Linux only has the Gunyah watchdog.

## Files

| File | What it is |
|---|---|
| `patches/0001-0005` | the series, on top of the iceland-linux kernel tree |
| `gunyah.config` | config fragment: the Gunyah drivers as modules |
| `build-modules.sh` | builds the 10 modules out of tree for one kernel and packs them with the two tools below |
| `gh_vmtest.py` | the test VMM (python3, one process): builds a guest device tree, lends 4 MiB of memory, starts a 1-vCPU VM and reports its exits; modes `off`, `mmio`, `hello` (and `shared`, see the limits) |
| `gunyah-rehearsal.sh` | the smoke test: `probe` (load the modules, hypervisor and resource-manager checks), `vm` (protected VMs only), `teardown` (unload) or `all` |

## Building

`build-modules.sh` needs the kernel's source and its build results; it applies the patches in a temporary git
worktree and leaves the source tree as it is.

- **Our kernel tree (supported):** an iceland-linux checkout at the commit the kernel was built from and the
  finished build directory of that kernel (`O=`, with its `.config` and `Module.symvers`):

  ```
  ./build-modules.sh --src ~/iceland-linux --rev <kernel commit> --kout ~/iceland-linux/out
  ```

  For kernel 7.3.0-rc7-iceland-00455 (q89n) the rebuilt modules have the same code as the ones we tested (only
  embedded build paths and build ids differ).
- **An installed kernel-iceland:** the package ships `/usr/lib/modules/<kver>/config` and `BUILD_INFO` (it names
  the iceland-linux commit and the clang version) but no build directory and no `Module.symvers` (there is no
  kernel-iceland-devel), so `--kout` is not possible with the installed files alone. Use the config with `--full`,
  which builds all modules once to get `Module.symvers` (slow, especially on the tablet):

  ```
  ./build-modules.sh --src ~/iceland-linux --rev <commit from BUILD_INFO> \
      --config /usr/lib/modules/$(uname -r)/config --full
  ```

Toolchain: clang/lld/llvm as for the kernel (`LLVM=1`; on a PC `ARCH=arm64` is set by the script). On Fedora
aarch64: `dnf install clang lld llvm make bc bison flex elfutils-libelf-devel openssl-devel git-core python3`.
The script stops if merging `gunyah.config` changes anything but toolchain lines of the config, and checks every
module's vermagic against the kernel release. Output: `gunyah-mods-<kver>.tar.gz`, which unpacks to `gunyah/`.

## Running the smoke test

Everything stays in `/run` (RAM): nothing goes to `/lib/modules`, `/etc`, `/boot` or a partition, and a reboot
removes the modules and any VM state.

```
sudo tar -C /run -xzf gunyah-mods-<kver>.tar.gz          # -> /run/gunyah
(cd /run/gunyah && sha256sum -c SHA256SUMS)
sudo /run/gunyah/gunyah-rehearsal.sh installed all
```

The script refuses to run on another kernel than the modules' vermagic names, with a checksum mismatch, with a
block device mounted read-write other than the btrfs root/home/var subvolumes, or (installed mode) below 30 %
battery without a charger. It writes a summary of PASS/FAIL lines to `~/gunyah-test-<time>.txt`. Reboot afterwards.

## Results on our unit (17 Oct 2026)

Kernel 7.3.0-rc7-iceland-00455 (q89n), installed Fedora 44, modules from this directory:

| Check | Result |
|---|---|
| Hypervisor identify | Gunyah 51/v1 |
| `/dev/gunyah`, resource-manager auxiliary device | present, no kernel warnings |
| Resource-manager log query at load | rejected by the firmware (unimplemented, harmless) |
| Protected VM power-off (4 MiB lent memory, 1 vCPU), 5 runs | 4/5 reported EXITED, 1 did not |
| MMIO exit (guest store to an unmapped address) | PASS |
| Hello guest (text written byte by byte as MMIO exits) | PASS: "hello from a Gunyah guest" |
| Kernel messages during the VM runs | none |
| Teardown | 7 of 10 modules unload; `gunyah`, `timer`, `gunyah_hypercall` stay loaded until the reboot |
| Memory after teardown | within 64 MiB of the start |

This matches what SuperTurtleDev reported for their Pad 4.

## Limits

- **Protected VMs only.** The VM's memory is lent to it (taken away from Linux while the VM exists). This
  firmware refuses unprotected VMs (`gh_vmtest.py` without `lend`): the attempt fails and loses a VM id until the
  next reboot, so the smoke test never tries it. The `shared` mode of `gh_vmtest.py` uses such a mapping too; it
  is not part of the smoke test.
- **Power-off 4/5:** one of five power-off runs ended without an EXITED status.
- **Modules not fully unloadable:** `gunyah.ko` has an init function but no exit function, so it cannot be
  removed, and it keeps `timer` and `gunyah_hypercall` (which it uses) loaded too.
- **Never fork() a process that holds lent guest memory:** the host then touches pages it no longer owns and
  hangs (seen by SuperTurtleDev). `gh_vmtest.py` never forks.
- Built as modules, the lent pages stay in the host's linear map (the hypervisor still removes them from Linux's
  stage-2 mapping); a stray host access to them would fault.
- No guest kernel and no full VMM (crosvm) yet: the test guests are a few instructions. Qualcomm's trusted VMs
  (QTVM) need signed images and are out of reach.
