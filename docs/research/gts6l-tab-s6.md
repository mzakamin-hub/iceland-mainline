# Galaxy Tab S6 mainline (bentlybro): lessons for the Pad 4

Status (14 Oct 2026): research only. The Galaxy Tab S6 (SM8150) is unrelated to the shipped Pad 4 build; none of the
points below is part of the 14 Oct build unless the feature matrix says so.

**Source:** the blog post "Mainline Linux on the Galaxy Tab S6: a 32-byte field and one line of device tree"
(bentlybro.com, blocked from the cloud container) and its repo
[Bentlybro/gts6l-mainline-linux](https://github.com/Bentlybro/gts6l-mainline-linux) (GPL-2.0, read at 41fa9b8,
2026-09-07): `docs/BOOT_METHOD.md`, `DEVLOG.md`, `DISPLAY.md`, `WIFI.md`, `POWER.md`.

**Device:** Samsung SM-T860, SM8150. It runs Fedora 44 + KDE on internal UFS with mainline 6.12. GPU, touch, Wi-Fi,
BT, audio, sensors, s2idle and charging work. The native display pipe does not work yet; simpledrm is used instead.

## What the title means

- **"A 32-byte field":** the `command` field of the Bootloader Control Block in the `misc` partition. It held
  `boot-recovery`, left there by Magisk-in-recovery rooting, so Samsung ABL booted *recovery* on every power-on and
  never ran the `boot` partition. Every one of their boot-image experiments had been ignored.
  - **For us:** not applicable. OnePlus ABL has fastboot, and `fastboot boot` of our images has been verified since
    U-Boot test 1. One general point carries over: when the bootloader seems to ignore your image, prove what it
    actually loaded before building new images.
- **"One line of device tree":** Wi-Fi hard-locked the whole SoC until `wlan_mem` was moved from the upstream dtsi
  address (0x8bc00000, which Samsung's map uses as a firmware carve-out) into HLOS-owned RAM (0xc0000000).
  - The failing `qcom_scm_assign_mem()` (-22) had been papered over with `qcom,msa-fixed-perm`.
  - The first firmware write into ungranted memory then killed the bus with no log.
  - **For us:** the lesson applies directly. Every carve-out the kernel hands to firmware or TrustZone must sit where
    the *stock* map says (68 regions in `device-facts/`). A `-EINVAL` from `qcom_scm_assign_mem` means wrong memory.
    Never work around it with a "fixed-perm" style flag. map220v already hit this class of bug (the llcc_lpi and
    adsp_mhi/global_sync reservations for Gunyah). **To do:** check each carve-out in the infiniti + iceland DT
    against the stock map before enabling remoteprocs and Wi-Fi.

## Boot method: should we drop U-Boot for UEFI?

They boot **Samsung ABL → Project Aloha SM8150 UEFI (Project Mu) → systemd-boot → mainline EFI-stub kernel**. The
UEFI firmware volume is injected into the *stock* Samsung kernel with DualBootKernelPatcher and repacked with
magiskboot.

**Why:** Samsung ABL has no fastboot and only accepts boot images that keep its own container (`UNCOMPRESSED_IMG`,
`SEANDROIDENFORCE`, AVB trailer). There is no lk2nd or U-Boot for SM8150 Samsung. Aloha was the only way in.

**Verdict: keep U-Boot.** The Tab S6 method solves a Samsung-only problem that OnePlus ABL doesn't have.

| | U-Boot (ours) | Project Mu UEFI (Tab S6 / Mu-Silicium) |
|---|---|---|
| Works on the Pad 4 today | **yes**: display, USB fastboot, UFS, EFI boot of Linux (runs 3–6) | no Pad 4 port. Mu-Silicium has an active OnePlus 15 (kaanapali) port, so a port is possible |
| Openness / GPL | fully open, GPL, in our repo | needs proprietary Qualcomm DXE drivers extracted from stock `xbl`/`uefi`; can't be shipped in our repos |
| Firmware-version coupling | none | DXEs must match the device's firmware |
| Kernel to distro path | EFI → systemd-boot/GRUB, same as UEFI | same |
| Memory map to the OS | ABL's `/memory` passed through (infiniti of_fixup), verified | proper UEFI memory map |
| Iteration speed | `fastboot boot` from RAM, about 1 min | the Tab S6 flashes an ESP per iteration |
| Upstreamable | yes (U-Boot board + DTS) | no |

UEFI remains the fallback only if U-Boot hits a wall it can't pass (for example, if a later ABL update refused
it). Plan v3 already dropped Mu-Silicium as a fallback because U-Boot works. Nothing in this project changes that.

## Lessons we take

1. **Display: "never touch the bootloader display pipe" for daily use.** Their working setup:
   - simpledrm on a bare `simple-framebuffer` node (**no clocks, power-domains or regulators**) plus `no-map`
     reserved memory;
   - **`dispcc` disabled**, and no DPU/DSI nodes;
   - `clk_ignore_unused pd_ignore_unused`, and every panel regulator `regulator-always-on`.

   **Update (PC relay results, same day):** on the Pad 4 this lesson is largely overtaken.
   - Test 7b ruled out rails and bandwidth: both images went white with MMCX/MX/MXC at 384.
   - The cause was the **MDSS core INT2 GDSC**. The simple-framebuffer has to hold it too (pc-001, iceland-linux
     05031dc).
   - The **native display then worked** (pc-007: MSM DRM, dual DSI + DSC, 120 Hz, KTZ8869 backlight; iceland-linux
     f9bc5e2).
   - So the Pad 4 doesn't need the "simpledrm forever" architecture. What still carries over: if a future change
     breaks the native pipe, the fallback is simpledrm with the pipe left alone (dispcc/MDSS off, votes held,
     `*_ignore_unused`).
2. **Carve-outs must be HLOS-owned or declared as in stock** (see above). Audit before Wi-Fi and remoteprocs.
3. **Power-off and reboot:** PSCI `SYSTEM_OFF`/`SYSTEM_RESET` hung on their firmware, and they fell back to PMIC
   PS_HOLD. Check both on the Pad 4 early; the HTTP reboot works already. Also check `PS_HOLD_RST_CTL`, because
   "release PS_HOLD" did a warm reset instead of power-off until it was set.
4. **Clocks that lie:** UFS/USB branch clocks needed `BRANCH_HALT_SKIP` because the TZ reported a wrong halt state.
   Keep this in mind if UFS or USB clocks time out.
5. **Start from defconfig, not tinyconfig** (we already do). Their tinyconfig kernel missed `BINFMT_ELF`.
6. **Fedora specifics for Phase 7:**
   - Fedora masks `sleep.target`/`suspend.target`, so logind says "Access denied".
   - PowerDevil ignores its profile, so they used an idle daemon.
   - RPM silently reverts edits to package-owned files, so they re-apply them with a boot service.
   - Remember these for our Fedora packaging.
7. **Never change simpledrm's output mode or scale.** It hard-crashed their SoC. Scale in the compositor instead.
8. **Hardware keys:** volume up was on a different PMIC GPIO than the inherited DT said. Check ours with the stock
   gpio dump.
9. **Method:** rollback boot entry (`tabs6-kernel snapshot/rollback`), USB networking as the lifeline, one subsystem
   per boot, hash before every flash. All of this matches ours.
