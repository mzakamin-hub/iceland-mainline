#!/usr/bin/env python3
# The "known issues / fixed in this build" tables (docs workflow, 3 Oct 2026; final-build edition reads the ledger).
# Base: an/r2g-logs/FIX-LIST.md (F1-F23, the main session's consolidated list of the r2g logs).
# Status: refreshed from the team's records when they exist (TEAM-PLAN.md section 2-3):
#   wf/<agent>/fixes/F<nn>.json (fix record, "status"), wf/fedtest/verdicts/F<nn>.json, wf/review/verdicts/F<nn>.json,
#   wf/builder/manifest-<tag>.json (G2), an/ledger/errors.json (G3 / benign), an/ledger/LEDGER.md.
# Read only. Prints Markdown to stdout (or writes it with --out FILE). Never prints log lines (they may be private).
import glob, json, os, sys

B = os.path.expanduser("~/mainline/build/")

# F-id, area, user-visible effect (plain words), owner, kind (installed system / rehearsal only / test only / log only)
ITEMS = [
    ("F1", "Cameras", "GNOME Camera (Snapshot) crashes when it starts (SIGBUS in PipeWire's device monitor inside the app); the cameras themselves work", "fedtest", "installed system"),
    ("F2", "Cameras", "the CMA dma-heap (32 MB) was too small for full-resolution frames (13 MP rear, 8 MP front), so the largest photo modes failed; the final build no longer exports CMA as dma-heaps, full-size buffers come from the system heap", "camfix", "installed system"),
    ("F3", "Cameras", "the acceptance check read the wrong tuning-file line (libcamera loads the right file for each camera)", "install", "test only"),
    ("F4", "Cameras", "the debugger's own camera probes (arguments, missing tool)", "fedtest", "test only"),
    ("F5", "Cameras", "libcamera has no sensor data for SC1320CS / SC820CS (generic gain model, assumed delays, no flip controls): exposure and gain less exact than stock", "camfix", "installed system"),
    ("F6", "Cameras", "camss warns that its test-pattern entities have no function set", "camfix", "log only"),
    ("F7", "Install rehearsal", "the rehearsal's guard took the probe's extension as its limit (625 s instead of 1500 s) and ended the session early", "install", "rehearsal only"),
    ("F8", "First-boot setup", "in rehearsals the acceptance step's test user replaces GNOME's first-boot setup (and its greeter logs a crash); the installed system must show the setup", "install", "rehearsal only"),
    ("F9", "System", "\"Failed to preset all unit ... Read-only file system\" lines", "fedtest", "log only"),
    ("F10", "System", "the system user / group `tss` is missing (tpm2-tss sysusers not applied): tmpfiles and udev warnings", "install", "installed system (cosmetic)"),
    ("F11", "Wi-Fi", "the regulatory country request is refused and `setregdomain` cannot determine a country; the firmware's US stays (owner decision 10)", "klog", "installed system"),
    ("F12", "Power / thermal", "irqbalance cannot receive thermal messages (CONFIG_THERMAL_NETLINK not set)", "klog", "log only"),
    ("F13", "Boot", "the initramfs' udevd cannot resolve the bpf system call (libseccomp missing in the initramfs)", "install", "log only"),
    ("F14", "Storage", "\"Failed to write bfq to queue/scheduler: Device or resource busy\" on sda-sdd", "install", "installed system (the disk scheduler: 3-5 of the 6 UFS disks kept the old one at random)"),
    ("F15", "Kernel / DT", "reserved-memory overlap between `cpucp` and `pdp` at 0x81200000", "klog", "log only (memory map)"),
    ("F16", "Power", "gcc / gxclkctl / gpucc reach sync_state only by the timeout (the trace NoC stays deferred): unused clocks may stay on", "klog", "installed system (power)"),
    ("F17", "Audio", "SoundWire 7630000 port counts differ from the controller (din 4 vs 6, dout 0 vs 1)", "klog", "log only (microphone path)"),
    ("F18", "Audio", "bus clashes on the headset codec's SoundWire bus, a codec parity error, the headset-detection -16 burst", "klog", "installed system (headset detection)"),
    ("F19", "Bluetooth", "two \"Frame reassembly failed (-84)\" lines at power-on", "klog", "log only"),
    ("F20", "Wi-Fi / PCIe", "PCIe supplies not described (dummy regulators) and about 11 probe attempts before Wi-Fi binds", "klog", "installed system (boot time)"),
    ("F21", "Kernel / DT", "other dummy or missing supplies (GPU vdd / vddcx, pwrseq vddant, UFS vdd-hba / vccq2)", "klog", "log only (to prove optional)"),
    ("F22", "USB-C", "pmic-glink \"Failed to create device link\" warnings", "klog", "log only"),
    ("F23", "Audio", "\"MultiMedia2 Playback: no backend DAIs enabled\" and a quiet loopback share", "fedtest", "log only"),
    ("F24", "Boot / power", "the device package said `iceland-cmdline` adds clk / pd / regulator `_ignore_unused` to every boot entry, but its call ran before the kernel's boot entry existed and failed silently, so every rehearsal booted without them - and worked fully, in the better power state. Decision (install workflow, 3 Oct): no flags; `iceland-cmdline` now removes them from every entry and `/etc/kernel/cmdline`; README, guides and package agree", "install", "installed system (power, documentation)"),
]
NIGHT = (
    "\n### Fixed during the night of 2-3 October (proven in the rehearsal boots R2-final / r2g)\n\n"
    "| What | Before | Now | Proof |\n|---|---|---|---|\n"
    "| Clock at first boot | the tablet started at systemd's built-in date (March 2026): package signatures looked \"not yet valid\" | `iceland-clock` keeps a time stamp; the first boot starts at the image's build time, NTP takes over with Wi-Fi | r2f / r2g clock PASS |\n"
    "| Sound on the installed system | no sound card: alsa-lib's install hook called a sequencer module the kernel did not have | `CONFIG_SND_SEQUENCER=m` + a modprobe softdep | r2f / r2g sound PASS (speaker sink, playback running) |\n"
    "| Auto-rotate under SELinux | SELinux denied iio-sensor-proxy's QRTR socket | a small SELinux module `iceland_sensors` | r2g rotate PASS; the owner saw the screen turn |\n"
    "| Firewall | firewalld could not start (nftables features missing in the kernel) | nftables config set in the kernel | r2f / r2g firewall PASS |\n"
    "| First-boot presets | Fedora's preset would have disabled our units | `50-iceland.preset` | r2f presets PASS |\n"
    "| Touch after a refresh-rate change | the touch firmware re-download failed after modesets | a kernel follower on the panel's enable / disable | r2f touch PASS, 0 firmware errors |\n"
    "| Cameras in the image | the sensor driver was private and outside the queue | in-tree in the private kernel queue (owner, 3 Oct), stock-derived tuning in the device package, `libcamera-tools` in the image | r2g: libcamera lists 2, 10 frames each, PipeWire 2 sources |\n"
    "| Kernel package verify | `rpm -V` flagged depmod's generated files | `%ghost` + depmod in `%posttrans` | r2f verify PASS |\n"
    "| Forbidden package in the image | `uboot-images-armv8` came in with a dependency | excluded | r2f packages PASS |\n"
    "| First sleep after boot | the pen charger's interrupt woke the first suspend | the driver waits for its start sequence before suspend | run 104 |\n"
    "| Charger input cut at a hot USB-C connector | the guard could only stop charging; the system load still flowed through the connector | a stock-exact input-suspend lever, used by the guard; v3.1 in the final build | run 103 (v1 flaw found), kit 106 (v3.1: lever, guard, restore PASS) |\n"
    "| U-Boot boot header values | U-Boot carried old Android version / patch values | header and AVB footer copy today's `boot_b` (17 / 2026-09) | Part A PARTA: READY FOR C0 |\n"
    "| Rehearsal watchdog | never armed (the driver's maximum is 31 s) | 30 s in rehearsals; the installed system arms none (a later decision) | r2g watchdog PASS |\n")

BENIGN = ("wireplumber IPC \"Connection refused\" at 62 s (the greeter user's session stopping); alsactl without asound.state "
          "(first boot); colord \"EDID length is too small\" (DSI panel); gsd-usb-protection (no USBGuard); offline dnf / "
          "GNOME Software; gnome-shell JS errors; gsd-media-keys grabs; upstream nits (ALSA control name truncated, "
          "rx_macro unsorted reg_defaults, ITS table sizes, arm-scmi fast channels, SELinux checkreqprot, simple-framebuffer "
          "memory-region, kauditd suppressed). Each is to be confirmed benign with its evidence in the ledger.")


def norm(fid):
    """'F02' / 'f2' / 2 -> 'F2', 'B08' -> 'B8' (the records use zero-padded names, the list does not)."""
    t = str(fid).strip()
    p = t[:1].upper() if t[:1].upper() in "FB" else "F"
    r = t[1:] if t[:1].upper() in "FB" else t
    return p + str(int(r)) if r.isdigit() else t


def load(pattern):
    out = {}
    for p in glob.glob(B + pattern):
        try:
            d = json.load(open(p, encoding="utf-8"))
            out[norm(d.get("id", os.path.basename(p).split(".")[0]))] = d
        except Exception:
            pass
    return out


LEDGER_DIR = B + "wf/ledger/"

# The main session's G3 review of r2h (3 Oct, after the final build was proven and queued as 0175-0185).
OVERRIDE = {
    "F5": "deferred: libcamera sensor data for SC1320CS / SC820CS comes later (the cameras work with the generic model)",
    "F18": "**fixed in this build** - queue 0186-0188 (kernel q85); kit 110 and r2i PASS; the USB-C jack mode (k5) stays an opt-in",
    "F1": "**fixed in this build** (r2h PASS; on r2i the app started 6 times without a crash - the suite's Snapshot step failed on F44)",
    "F2": "**fixed in this build** (r2h PASS; on r2i the kernel side passed - system heap only, full-size frames; the suite missed its line by an index bug)",
    "F31": "benign; its probe passed on r2i; a new WirePlumber line in its subsystem (F50) is being classified",
    "F42": "seen in r2g / r2h, not in kit 110 or r2i (no bus clash or parity error there); being classified (G0)",
    "F43": "**known issue of RC1** - fix k9 in loop 3 (docs/guide/RC1-NOTES.md, section 3a)",
    "F44": "**known issue of RC1** - loop 3 (camfix; docs/guide/RC1-NOTES.md, section 3a)",
    "F8": "benign, rehearsal only (the installed system shows the first-boot setup); a new WirePlumber line on r2i (F50) is being classified",
    "CHGSAFE-V3": "**fixed in this build** - proven in kit 106 (v3.1: the lever, the guard and the restore PASS; 219 unit checks)",
    "SLEEP-Q84": "**fixed in this build** - proven in kits 106 and 108 (q84) and 110 (q85)",
}
GATE = {"CHGSAFE-V3": "G3 (kit 106)"}
EXTRA_TEXT = {  # plain words for records the original r2g list did not have
    "F16a": ("Power", "gcc / gxclkctl / gpucc reach sync_state only by the timeout, held by the GPU's GMU node (no driver of its own, by design); power-benign", "log only"),
    "F16b": ("Kernel / DT", "the CoreSight trace NoC stays in deferred probe (its driver is not built)", "log only"),
    "chgsafe-v3": ("Charging", "the charger input cut at a hot USB-C connector (kernel lever + battery guard) and its desktop notice", "installed system (safety)"),
    "F25": ("Tests", "the debugger suite's own false alarms (units, a serial-number read, a truncated command, a watchdog line)", "test only"),
    "F30": ("Bluetooth", "bluetoothd cannot set its default system configuration for hci0", "log only"),
    "F38": ("Desktop", "the on-screen keyboard raised an error in a modal dialog (e.g. a password prompt)", "installed system"),
    "F39": ("Cameras", "camera I2C bus: one GPI DMA error (-5) per boot - the camera module's EEPROM (0x58) does not answer at power-up in GPI mode", "log only"),
    "F40": ("GPU", "the GPU's GMU logs a delay in a fenced register write", "log only"),
    "F42": ("Audio", "the headset codec's SoundWire RX bus logged a bus clash and a codec parity error (r2g, r2h)", "log only"),
    "F43": ("Wi-Fi", "on the owner's network the connection drops after about 110 s and every reconnect (2.4 and 5 GHz) fails until a reboot: the Wi-Fi firmware's 802.11d scan is re-armed at every disconnect; stock switches 802.11d off", "installed system"),
    "F44": ("Cameras", "the Camera app can fail to start a camera when another camera program used the other camera since login (a stale link in the camera pipeline)", "installed system"),
    "F45": ("Desktop", "GNOME Software can abort after a network change (an upstream GTK 4 accessibility assertion)", "log only"),
    "F41": ("Desktop", "gnome-session asks for the screensaver state before GNOME Shell offers it, once at a fresh login (GNOME behaviour)", "log only"),
    "sleep-q84": ("Sleep", "s2idle on the consolidated kernel q84, incl. the pen charger's first-sleep fix", "installed system"),
}


def board():
    """F-id rows of wf/ledger/LEDGER.md: id -> (title, owner, gate, detail)."""
    out = {}
    try:
        lines = open(LEDGER_DIR + "LEDGER.md", encoding="utf-8").read().split("\n")
    except OSError:
        return out
    on = False
    for l in lines:
        if l.startswith("## F-ids"):
            on = True; continue
        if on and l.startswith("## "):
            break
        if on and l.startswith("| ") and not l.startswith("| F |") and not l.startswith("|---"):
            c = [x.strip() for x in l.strip("|").split("|")]
            if len(c) >= 5:
                out[norm(c[0]) if c[0][:1] in "FB" and c[0][1:2].isdigit() else c[0].upper()] = (c[1], c[2], c[3], c[4])
    return out


def checks():
    """Verdicts of wf/ledger/check-r2i.md (release candidate 1), over check-r2h.md and check-k106.md; an r2i "n/a"
    keeps the older verdict."""
    v = {}; head = ""
    for name in ("check-k106.md", "check-r2h.md", "check-r2i.md"):
        try:
            text = open(LEDGER_DIR + name, encoding="utf-8").read()
        except OSError:
            continue
        for l in text.split("\n"):
            if name == "check-r2i.md" and not head and "records:" in l:
                head = l.split(". FAIL =")[0]
            if l.startswith("| ") and not l.startswith("| id ") and not l.startswith("|---"):
                c = [x.strip() for x in l.strip("|").split("|")]
                if len(c) >= 3:
                    k = norm(c[0]) if c[0][:1] in "FB" and c[0][1:2].isdigit() else c[0].upper()
                    if c[1] == "n/a" and k in v:
                        continue
                    v[k] = (name.split("-")[1].split(".")[0], c[1], c[2])
    return v, head


def benign_ids():
    try:
        d = json.load(open(LEDGER_DIR + "fids.json", encoding="utf-8"))
    except Exception:
        return {}, {}
    ben = {}; titles = {}
    for k, x in d.items():
        if k.startswith("_") or not isinstance(x, dict):
            continue
        n = norm(k) if k[:1] in "FB" and k[1:2].isdigit() else k.upper()
        titles[n] = x.get("title", "")
        ben[n] = bool(x.get("benign")) or "benign" in x.get("title", "").lower()[:40]
    return ben, titles


def final_status(fid, title, gate, ver, ben, kind="", detail=""):
    if fid in OVERRIDE:
        return OVERRIDE[fid]
    both = "dbg confirmed" in detail and "rev confirmed" in detail
    bnote = ("benign (debugger + reviewer confirmed)" if both or not detail else
             "benign (fix record; debugger / reviewer to confirm)" if kind == "benign" else
             "benign (proposed by the ledger; debugger / reviewer to confirm)")
    if ver is None:
        return "being classified (G0)" if gate == "G0" else "gate " + (gate or "?") + "; not checked in r2i"
    run, verdict, gone = ver
    if verdict == "await":
        return ("benign; " if ben else "") + "awaits the next run (its probe lines were updated after " + run + ")"
    if verdict == "PASS":
        if ben or kind == "benign":
            return ("benign, confirmed by the debugger and the reviewer (" + run + ")") if both else ("benign (" + run + " PASS; the debugger / reviewer to confirm)")
        if kind == "tooling":
            return "resolved: the test or suite was corrected / the line explained (" + run + " PASS)"
        return "**fixed in this build** (" + run + " PASS)"
    if verdict == "n/a":
        if ben or kind == "benign":
            return bnote
        if gone and gone.split("/")[0] == gone.split("/")[-1] and gone != "0/0":
            return "gone in " + run + " (no positive line to prove it)"
        return "not in the scope of " + run
    return "open (" + run + " " + verdict + ")"


def main():
    if "--night" in sys.argv:
        sys.stdout.write(NIGHT.lstrip(chr(10)) + chr(10))
        return
    bd = board(); ver, head = checks(); ben, titles = benign_ids(); rec = load("wf/*/fixes/*.json")
    plain = {norm(f): (area, what, kind, owner) for f, area, what, owner, kind in ITEMS}
    plain["F16a"] = plain.pop("F16", ("Power", "", "log only", "klog"))
    for k, (area, what, kind) in EXTRA_TEXT.items():
        kk = k if k[:1] == "F" else k.upper()
        plain[kk] = (area, what, kind, plain.get(kk, ("", "", "", "-"))[3])
    ids = [k for k in bd] or [norm(f) for f, *_ in ITEMS]
    order = lambda k: (0, int("".join(ch for ch in k[1:] if ch.isdigit()) or 0), k) if k[:1] == "F" else (1, 0, k)
    lines = []
    if head:
        lines += ["Ledger G3 check of release candidate 1's rehearsal r2i: " + head + " (`wf/ledger/check-r2i.md`; r2i "
                  "itself: INSTALL-ACCEPT 46 PASS, 0 FAIL, 0 CHECK). Statuses below include the main session's review; the "
                  "plain explanations of the FAILs and the known issues are in `docs/guide/RC1-NOTES.md` (sections 2a, 3a).", ""]
    lines += ["| Id | Area | What it is / what you would notice | Where it matters | Owner | Gate | Status in the final build |",
              "|---|---|---|---|---|---|---|"]
    for k in sorted(ids, key=order):
        if k.startswith("B"):
            continue
        title, owner, gate, detail = bd.get(k, ("", "", "", ""))
        area, what, kind, own2 = plain.get(k, ("", "", "", ""))
        if not what:
            t = titles.get(k) or title
            what = t.replace("(proposed, benign)", "").replace("(proposed)", "").replace("(benign)", "").strip()
            kind = "log only (benign)" if (ben.get(k) or "benign)" in title) else (kind or "installed system")
            area = area or "System"
        b = ben.get(k, False) or "benign)" in title
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (k, area, what.replace("|", "/"), kind, owner or own2, GATE.get(k, gate or "-"),
                                                             final_status(k, title, gate, ver.get(k), b, rec.get(k, {}).get("kind", ""), detail)))
    lines += ["", "Benign groups (B-ids; noise that is expected on this hardware or first boot):", "",
              "| Id | What | Status |", "|---|---|---|"]
    dbg = load("wf/fedtest/verdicts/*.json"); rev = load("wf/review/verdicts/*.json")
    for k in sorted([x for x in titles if x.startswith("B")], key=lambda x: int(x[1:])):
        v = ver.get(k)
        both = dbg.get(k, {}).get("verdict") == "confirmed" and rev.get(k, {}).get("verdict") == "confirmed"
        st = ("benign, confirmed in " + v[0]) if v and v[1] == "PASS" else ("benign, confirmed by debugger + reviewer" if both else "benign (expected noise)")
        lines.append("| %s | %s | %s |" % (k, titles[k].replace("|", "/"), st))
    md = "\n".join(lines) + "\n"
    if "--out" in sys.argv:
        open(sys.argv[sys.argv.index("--out") + 1], "w", encoding="utf-8", newline="\n").write(md)
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
