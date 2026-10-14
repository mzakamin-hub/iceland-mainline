#!/usr/bin/env python3
# Docs workflow, 3 Oct 2026: the final-build edition of the three install documents.
#   in : (private build tree) wf/install/proposed/INSTALL-GUIDE.md, INSTALL-PLAN.md (round 7, 01:25), wf/install/DUALBOOT-PLAN.md
#   out: (private build tree) wf/docs/final/INSTALL-GUIDE.md, INSTALL-PLAN.md, DUALBOOT-PLAN.md
# Status 14 Oct 2026: the inputs are private build folders that are not in this repository, so this script cannot run
# from here. Its output is the install documents of release candidate 1 (3 Oct 2026); the installed state is dated in
# docs/INSTALL-GUIDE.md (Fedora installed 13 Oct 2026).
# Adds: the first-boot setup note (F8), the current state of the rehearsal (R1d .. r2g), the corrected initramfs design
# (the SoCCP / ADSP / CDSP stack is IN the initramfs since R1c), no suspend in rehearsals, and a section
# "Known issues and what this build fixes" whose table comes from tools/known_issues.py (refreshed from the ledger and
# the fix records: re-run this script after the final build's proof). Exact-string edits; fails loudly. Read only on
# its inputs; writes only into wf/docs/final/.
import io, os, subprocess, sys

H = os.path.expanduser("~/mainline/build/")
SRC = H + "wf/install/proposed/"; OUT = H + "wf/docs/final/"
os.makedirs(OUT, exist_ok=True)
STAMP = os.environ.get("EDITION", "3 Oct 2026, release candidate 1 (kernel q85 = queue 0001-0188, iceland-device 0.19, rehearsal r2i 46 / 0 / 0)")
KI = subprocess.run([sys.executable, H + "wf/docs/tools/known_issues.py"], capture_output=True, text=True, check=True).stdout
NIGHT = subprocess.run([sys.executable, H + "wf/docs/tools/known_issues.py", "--night"], capture_output=True, text=True, check=True).stdout


def edit(text, pairs, name):
    for old, new in pairs:
        if text.count(old) != 1:
            sys.exit("%s: expected exactly one %r (found %d)" % (name, old[:70], text.count(old)))
        text = text.replace(old, new)
    return text


FIRSTBOOT = (
    "> **First-boot setup.** It asks for language, keyboard, Wi-Fi, privacy and **your user account and password**:\n"
    "> the image has no preset user and no default password (finding F8: the rehearsal-only test user never reaches\n"
    "> the installed system).")


KNOWN_GUIDE = (
    "\n---\n\n## 11. Known issues and what this build fixes\n\n"
    "Status " + STAMP + ". The findings come from the logs of the release candidate's rehearsal (r2g, 3 Oct 02:44:\n"
    "INSTALL-ACCEPT 42 PASS, 1 FAIL, 1 CHECK), consolidated as F1-F23 (`an/r2g-logs/FIX-LIST.md`, private) and grown\n"
    "by the team's error ledger to F50 and B1-B18; the status column is the ledger's G3 check of release candidate 1's\n"
    "rehearsal r2i (the ledger's check is not published) with the main session's review (generator: docs/guide/tools/mk-final-docs.py).\n"
    "What RC1 contains, what each run proved, its known issues (F43 Wi-Fi, F44 Camera app) and the owner's checks:\n"
    "`docs/guide/RC1-NOTES.md`. \"Rehearsal only\" and \"test only\" items do not exist on the installed\n"
    "tablet; \"log only\" items change nothing you would notice.\n\n" + NIGHT +
    "\n### The findings and their status in release candidate 1\n\n" + KI +
    "\n### Long-standing limits (not bugs of this build)\n\n"
    "- Speakers stay volume-capped (-12 dB): speaker protection has no mainline driver.\n"
    "- No fast charging (SuperVOOC / PPS); bypass charging is built and reviewed but deferred (owner, 2 Oct).\n"
    "- No automatic focus (libcamera's simple pipeline); the lens holds stock's start position.\n"
    "- The deepest SoC sleep state (AOSS sleep) is out of reach on mainline; CX collapse is reached (95-98 % of a sleep).\n"
    "- Wi-Fi stays off in sleep (owner, 2 Oct); the Wi-Fi country stays the firmware's US (owner decision 10).\n"
    "- Firefox decodes video in software; GNOME's player and GNOME Web use the hardware decoder.\n"
    "- Running neural networks on the NPU needs Qualcomm's QNN SDK (owner's decision).\n"
    "- Need your hands once: wall chargers, a night unplugged, the pen (90 s on the magnet side), the keyboard cover, a\n"
    "  USB-C monitor, USB accessories, a USB headset, the 5 GHz password.\n")

KNOWN_PLAN = (
    "- **Build-specific known issues** (F1-F23 of the last rehearsal's logs, with their status) are kept in one place:\n"
    "  `docs/INSTALL-GUIDE.md` section 11, `docs/RELEASE-NOTES.md` and `docs/guide/RC1-NOTES.md`.\n")


def guide(t):
    t = edit(t, [
        ("`docs/INSTALL-PLAN.md` (the reasons are there; the steps are here).",
         "`docs/INSTALL-PLAN.md` (the reasons are there; the steps are here). **Edition: " + STAMP + "**: adds the\n"
         "first-boot setup note (Part C step 4) and section 11 (known issues and what this build fixes)."),
        ("| Kernel as an installable package (`kernel-iceland`) | built from test kernel q78 (queue 0001-0162): K2 and a second version K3 for the update rehearsal, 13 checks each | Part B |",
         "| Kernel as an installable package (`kernel-iceland`) | release candidate 1: kernel q85 = queue 0001-0188 (iceland-linux a9b55d4, release 7.3.0-rc4-iceland-00324-ge0373b2308fc); K2 `...00324.ge0373b2308fc-1` and its twin K3 `...ge0373b2308fc.1-1` for the update rehearsal | Part B |"),
        ("| Device package `iceland-device` 0.18 (read-only rule, dracut module, snapshots, trial boots, GPU firmware from Fedora's `qcom-firmware`) | built on the tablet in the B run (runs 93 / 94); rebuilt with the round-7 fixes before the next B run | Part B |",
         "| Device package `iceland-device` 0.19 (read-only rule, dracut module, snapshots, trial boots, GPU firmware from Fedora's `qcom-firmware`, the battery guard v3.1 with the input cut, PipeWire >= 1.6.8, Wi-Fi regdomain US, the camera tuning, no `*_ignore_unused`) | built and checked on the tablet in B runs 109 and 112 (31 PASS, 0 FAIL each) | Part B |"),
        ("| Image builder + rehearsal from RAM over the USB network (G9) | built; B run passed (runs 93 / 94); **the first rehearsal boot R1 is pending** (round 5 fixed its U-Boot stop) | Part B |",
         "| Image builder + rehearsal from RAM over the USB network (G9) | built; B run 112 31 / 0; rehearsal boots up to r2i (46 / 0 / 0) | Part B |"),
        ("| Your decisions (section 0.4) | partly answered |",
         "| Rehearsal boots so far (3 Oct) | R1d: the first complete boot to the desktop (27 / 6 / 4); R2, SELinux enforcing (29 / 4 / 3); R2-final r2f with the release candidate (40 / 2 / 1); r2g (42 PASS, 1 FAIL = an acceptance parse error, 1 CHECK = PCIe probe count); the final build's rehearsal **r2h: INSTALL-ACCEPT 45 PASS, 0 FAIL, 0 CHECK**, the debugger's suite 29 PASS, the Camera app works; release candidate 1's rehearsal **r2i: INSTALL-ACCEPT 46 PASS, 0 FAIL, 0 CHECK** (known issues F43 Wi-Fi and F44 Camera app: section 11) (3 Oct) | Part B |\n"
         "| Your decisions (section 0.4) | partly answered (6 and 10 answered on 3 Oct) |"),
        ("   modes, auto-rotate, suspend and resume, hardware video, both cameras, the default apps start, About shows",
         "   modes, auto-rotate, hardware video, both cameras, the default apps start, About shows"),
        ("so on the installed tablet it is the first screen.)\nThe PC session then runs",
         "so on the installed tablet it is the first screen.)\n\n" + FIRSTBOOT + "\n\nThe PC session then runs"),
        ("- **First hour:** Wi-Fi,",
         "- **First start:** Fedora's first-boot setup creates your user account (see Part C step 4); there is no preset\n"
         "  user or password.\n- **First hour:** Wi-Fi,"),
    ], "guide")
    # Part B: suspend is never part of a rehearsal (the root is on the PC; R2-final 3 Oct)
    anchor = "Part B is complete when section 10 has these values and the date of the passed acceptance list."
    if t.count(anchor) != 1:
        sys.exit("guide: Part B anchor")
    t = t.replace(anchor, "Suspend and resume are tested in the RAM kits and on the installed system, **never in a rehearsal**: the\n"
                  "rehearsal's root comes from the PC over the USB link, and the USB gadget's suspend loses it (R2-final, 3 Oct).\n\n" + anchor)
    return t.rstrip("\n") + "\n" + KNOWN_GUIDE


def plan(t):
    return edit(t, [
        ("`docs/INSTALL-GUIDE.md`.\n",
         "`docs/INSTALL-GUIDE.md`. **Edition: " + STAMP + "** (the initramfs design after R1c, no suspend in rehearsals,\n"
         "the first-boot setup, the rehearsal results to r2g, the known-issues pointer).\n"),
        ("cards, ADSP and CDSP running with no failed firmware request (their drivers stay out of the initramfs, so they load\nthe tablet's firmware from the root),",
         "cards, ADSP and CDSP running with no failed firmware request (since 3 Oct their driver and the tablet's ADSP / CDSP\n"
         "firmware are IN the initramfs, so the charger co-processor (SoCCP), pmic_glink and USB-C come up before the network\n"
         "disk - R1b / R1c showed the USB link dropping when they came later; Wi-Fi, Bluetooth and video stay out and load\n"
         "from the root),"),
        ("estimate, the charge limit end to end (80 / 85 %, GNOME's \"Preserve Battery Health\"), power modes, auto-rotate after a\nboot, suspend and resume,",
         "estimate, the charge limit end to end (80 / 85 %, GNOME's \"Preserve Battery Health\"), power modes, auto-rotate after a\n"
         "boot (suspend and resume are tested in kits and on the installed system, never in a rehearsal: the root is on the\n"
         "PC),"),
        ("  first-boot setup appears, the acceptance list passes again,",
         "  first-boot setup appears (gnome-initial-setup: your user account is created there; in the rehearsals the\n"
         "  acceptance step replaces it with a test user, finding F8), the acceptance list passes again,"),
        ("- Deep sleep: suspend and resume work; the chip's deepest sleep state is not reached yet (CX collapse reached in a\n"
         "  test kernel, run 59), so the tablet drains faster asleep than on stock until the deep-sleep work is queued and one\n"
         "  night unplugged has been measured.\n"
         "- Cameras: everything automated works (both cameras, the Camera app, a browser); automatic focus needs lens support\n"
         "  in libcamera (not there yet); colours and sharpness need your eyes.\n",
         "- Deep sleep: suspend and resume work and CX collapse is reached (queue 0113-0116, 95-98 % of a sleep); the chip's\n"
         "  deepest state (AOSS sleep) is out of reach on mainline; one night unplugged measures the real drain.\n"
         "- Cameras: both cameras capture on the release candidate (driver in the private queue, stock-derived tuning; r2g);\n"
         "  GNOME's Camera app works (F1: PipeWire 1.6.8 or newer) and full-size captures work (F2: no CMA dma-heaps),\n"
         "  both proven in the final rehearsal r2h; automatic focus needs lens support in libcamera (not there yet); the\n"
         "  sensor data for libcamera comes later (F5); colours and sharpness need your eyes.\n" + KNOWN_PLAN),
    ], "plan")


def main():
    g = guide(io.open(SRC + "INSTALL-GUIDE.md", encoding="utf-8").read())
    p = plan(io.open(SRC + "INSTALL-PLAN.md", encoding="utf-8").read())
    d = io.open(H + "wf/install/DUALBOOT-PLAN.md", encoding="utf-8").read()
    for name, text in (("INSTALL-GUIDE.md", g), ("INSTALL-PLAN.md", p), ("DUALBOOT-PLAN.md", d)):
        io.open(OUT + name, "w", encoding="utf-8", newline="\n").write(text)
        print("wrote", OUT + name, len(text.splitlines()), "lines")


if __name__ == "__main__":
    main()
