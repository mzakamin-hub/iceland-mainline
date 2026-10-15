# Comparable mainline ports and a roadmap for streamlining (16 Oct 2026)

Research only: GitHub API (`gh`), web search and the project's public repositories. Nothing was
cloned in full, built or run on the tablet. Dates are the repositories' last push as reported by the
GitHub API on 16 Oct 2026. "V" = read in the repository or page; "I" = inferred, check before acting on it.
This document contains no unit data and may be published.

---

## 1. Our system in one paragraph (baseline for the comparison)

Fedora 44 GNOME on the OnePlus Pad 4 (SM8850 "kaanapali", board "iceland"). Boot: stock ABL -> footered U-Boot in
`boot_b` -> EFI (Fedora shim + GRUB, BLS entries) -> `kernel-iceland` -> btrfs root on a loop device over `userdata`.
Kernel: a patch queue on v7.3-rc7 (`iceland-linux`, 436 patches: 132 from the OnePlus 15 "infiniti" tree, 304 Pad 4
patches), verified by tree hashes (`kernel.pin`, `scripts/prepare.sh`). Packages: `kernel-iceland`, `iceland-device`
(settings, guards, thermal, provisioning), `iceland-firmware` (generic stock blobs, sha256 manifest),
`iio-sensor-proxy` + `libssc`. Image: a "B run" builds the golden image from a RAM-booted tablet onto a PC-side NBD
disk; a "rehearsal" RAM-boots that image from the PC and runs the acceptance rows; the user runs the two install
writes (`userdata`, `boot_b`). Updates today: GitHub releases + install scripts + a local dnf repo
(`packaging/repo/make-repo.sh`, not published). Rollback: btrfs snapshots (`iceland-snapshot`) and a kernel trial
boot. CI: one manual-only GitHub Actions kernel build (`workflow_dispatch`, ubuntu-24.04-arm). Status: 85 working
features, all six repositories public.

---

## 2. Comparable projects

### 2.1 Same SoC (SM8850 / kaanapali)

| Project | Last push | Device | What it does well | What we could adopt |
|---|---|---|---|---|
| [SuperTurtleDev/iceland-mainline](https://github.com/SuperTurtleDev/iceland-mainline) (+ [-kernel](https://github.com/SuperTurtleDev/iceland-mainline-kernel), [-kernel-linux](https://github.com/SuperTurtleDev/iceland-mainline-kernel-linux), [-bootloader](https://github.com/SuperTurtleDev/iceland-mainline-bootloader), [iceland-build-container](https://github.com/SuperTurtleDev/iceland-build-container), [-userspace](https://github.com/SuperTurtleDev/iceland-mainline-userspace), [-kernel-firmware](https://github.com/SuperTurtleDev/iceland-mainline-kernel-firmware)) | 15 Oct 2026 | **OnePlus Pad 4** (same device), Ubuntu 26.04 | (V) Meta-repo with submodules; **one GitHub Actions workflow on push / PR / tag** builds bootloader -> kernel -> userspace rootfs -> deploy bundle; **pinned podman build root** (`podman run --rootfs`, provisioned from stock ubuntu:26.04, `build-env.txt` with every package version, reprovisioned when the repo commit changes); `--network=none` builds with `SOURCE_DATE_EPOCH` = commit time, byte-identical rebuilds, `buildinfo.txt` with all hashes; own UEFI BootApp (EDK2) on the ESP; a net-deploy initrd that streams a sparse rootfs over USB NCM. Very active kernel work (camera resource voting 13-15 Oct). | The build container + buildinfo pattern (section 4.2); a CI workflow that builds every artifact on push; keep scanning their kernel for fixes (as in COMPARE-SUPERTURTLE-ICELAND.md). Not their install path (it writes new GPT partitions). |
| [joonhoekim/tb323fu-linux](https://github.com/joonhoekim/tb323fu-linux) | 15 Oct 2026 | Lenovo Legion Tab Gen 5 / Y700 5th gen (TB323FU, SM8850, board "baldur") | (V) Best-organised project of the group. **Kernel is the product; distro integration optional.** Distribution-neutral `userspace/platform/` + packaging for **Debian, Arch and Nix** (`flake.nix`); a D-Bus device helper app with a settings UI; **numbered kernel releases** (`kernel-t51`) with user-facing release notes and a `min_helper` compatibility tag; `PROVENANCE.md` per imported patch; a strict "working only when checked on the device" rule; **GitHub Pages site**, Discussions categories for device reports, issue templates, DCO workflow, `reuse lint` clean (REUSE 3.3), SECURITY / TRADEMARKS / CONTRIBUTING; firmware not redistributed but extracted by a script with a manifest; guided installer for Windows / Linux / macOS; multiboot initramfs. Already a patch source for us (0255-0265). | Release-note format with compatibility tags; REUSE + DCO + SECURITY.md; Pages site; Discussions for device reports; distro-neutral platform files (helps the Debian plan); their known issues (cluster idle reset, 165/144 Hz) as test rows for us. |
| [infiniti-mainline/linux](https://github.com/infiniti-mainline/linux), [u-boot](https://github.com/infiniti-mainline/u-boot), [firmware-oneplus-infiniti](https://github.com/infiniti-mainline/firmware-oneplus-infiniti), [audioreach-topology](https://github.com/infiniti-mainline/audioreach-topology), [minkipc](https://github.com/infiniti-mainline/minkipc), libfprint | 4 Oct 2026 | OnePlus 15 (SM8850) | (V) The SoC base we carry (series 0001, 132 patches); U-Boot base for ours; an org with separate firmware and topology repos. | Coordinate: our 132-patch copy of their tree is the largest duplicated block (section 3.1). |
| [map220v/sm8850-mainline](https://github.com/map220v/sm8850-mainline) | 17 Aug 2026 | "OPPO Pad 5 Pro / OnePlus Pad 3 Pro / OnePlus Pad 4" (repo description) | (V) Origin of the iceland DT and of SuperTurtleDev's fork. Quiet since August. | Nothing new; keep as provenance. |
| [kaanapali-mainline/linux](https://github.com/kaanapali-mainline/linux), [linux-firmware](https://github.com/kaanapali-mainline/linux-firmware) | 6 Aug 2026 | community kaanapali tree (tb323fu's base) | (V) An org name for a shared SoC tree. | The natural home for a **shared SM8850 base** if the ports agree (owner decision, section 5). |
| [FantomTchi7/kaanapali-mainline-linux-firmware](https://github.com/FantomTchi7/kaanapali-mainline-linux-firmware) | 25 Apr 2026 | kaanapali firmware | (I) Early firmware collection. | Nothing. |
| [LeeSiWal/y700-linux](https://github.com/LeeSiWal/y700-linux) | 20 Sep 2026 | TB323FU on the **stock GKI kernel** | (V) Not mainline; Ubuntu userspace on vendor modules, Steam via FEX / ARM64 Proton. Useful as a gaming-stack reference only. | FEX / Steam notes if gaming becomes a goal. |
| Android side: [LineageOS/android_device_oneplus_sm8850-common](https://github.com/LineageOS/android_device_oneplus_sm8850-common), [infiniti-labs/android_kernel_oneplus_sm8850](https://github.com/infiniti-labs/android_kernel_oneplus_sm8850), [Mi-SM8850/android_kernel_xiaomi_sm8850](https://github.com/Mi-SM8850/android_kernel_xiaomi_sm8850) (CodeLinaro `kaanapali` mirror) | Oct 2026 | various SM8850 | Stock values (rule 13) and the CodeLinaro bring-up branch. | Keep as read-only value sources. |

### 2.2 Neighbouring Snapdragon SoCs (SM8750 / SM8650 / SM8550 / SM8450 / SM8250)

| Project | Last push | Device | Notes / what to adopt |
|---|---|---|---|
| [yzddmr6/linux-sm8750-piano](https://github.com/yzddmr6/linux-sm8750-piano) | 15 Oct 2026 | Xiaomi Pad 8 Pro (SM8750P), on linux-7.2.y | Tablet on a **stable** branch rather than an rc: a data point for our base choice. |
| [BigfootACA/linux](https://github.com/BigfootACA/linux) + [liisoya/pad8pro-kernel-build](https://github.com/liisoya/pad8pro-kernel-build) | 30 Sep / 13 Oct 2026 | Xiaomi Pad 8 Pro | A third party builds the kernel **only with GitHub Actions**: an example of a free public CI build of a device kernel. BigfootACA also has [arch-image-builder](https://github.com/BigfootACA/arch-image-builder) and [embloader](https://github.com/BigfootACA/embloader). |
| [renhiyama/pagani-linux](https://github.com/renhiyama/pagani-linux) | 30 Jun 2026 | OnePlus 13s / 13T (SM8750) | Display (DSC 1.2 cmd panel), touch, ath12k. |
| [sm8750-mainline/linux](https://github.com/sm8750-mainline/linux), [sm8450-mainline/linux](https://github.com/sm8450-mainline/linux), [sm8650-mainline/linux](https://github.com/sm8650-mainline/linux), [sm8250-mainline/linux](https://github.com/sm8250-mainline/linux), [pipa-mainline/linux](https://github.com/pipa-mainline/linux) | 2023 to May 2026 | community SoC trees (Xiaomi Pad 6 "pipa" in pipa-mainline) | The "one org per SoC, many devices" model. pipa reached postmarketOS (`linux-xiaomi-pipa`, `device-xiaomi-pipa`, `firmware-xiaomi-pipa` packages, plus a kernel.org-stable variant). Shows the path: shared SoC tree -> distro packages. |
| [FixItFoundry/zenbook-a16-linux](https://github.com/FixItFoundry/zenbook-a16-linux) | 14 Oct 2026 | ASUS Zenbook A16 (X2 Elite "glymur") | (V) AI-assisted like ours; a **"baseline" kernel per date with ordered patches + `verify.py`**, current-boot vs retained checks kept apart. Similar honesty rules; nothing new to adopt. |
| [nfe613920-cmyk/tb520fu-mainline-docs](https://github.com/nfe613920-cmyk/tb520fu-mainline-docs) | 20 Sep 2026 | Lenovo YOGA Pad Pro 12.7 AI (SM8650) | EDK2 UEFI (mu_aloha) -> GRUB -> Arch; documentation-only repo with a "reproduce on another unit" guide. |
| [MeowArch-open/MeowArchMobile_sm8650AB_Bluetooth](https://github.com/MeowArch-open/MeowArchMobile_sm8650AB_Bluetooth) | 15 Sep 2026 | SM8650 phone | WCN7850 BT with a **persistent public address restore**: relevant to our bdaddr provisioning. |

OnePlus Pad 2 (caihong, SM8650) and OnePlus Pad 3: no public mainline port was found (only Android trees); the
caihong-linux-rootfs repository known to the project could not be found again under that name through the API.

### 2.3 Distributions and integrators

| Project | Last push | Scope | What it does well | What to adopt |
|---|---|---|---|---|
| [ROCKNIX/distribution](https://github.com/ROCKNIX/distribution) (+ [abl](https://github.com/ROCKNIX/abl), [u-boot](https://github.com/ROCKNIX/u-boot), [sensor-firmware](https://github.com/ROCKNIX/sensor-firmware), [linux-mdss-dsi-panel-driver-generator](https://github.com/ROCKNIX/linux-mdss-dsi-panel-driver-generator)) | 15 Oct 2026 | Handheld distro; device trees for SM8250, SM8550, SM8650, SM8750 among others | (V) One build system for many SoCs; **monthly releases + nightlies** (separate `distribution-nightly` repo); **OTA through the settings menu**, fallback "copy the update file to the update share and reboot"; a published custom ABL as the boot path; kernel bumps per SoC family (7.2 in Sep 2026). | Release cadence (stable + nightly channels); "update share" fallback is close to our LAN share; their panel driver generator and SSC sensor firmware handling. |
| [shuuri-labs/pocknix-os](https://github.com/shuuri-labs/pocknix-os) and [arcadematicas/pocknix-odin3-support](https://github.com/arcadematicas/pocknix-odin3-support) (CalvOS) | 15 Oct 2026 | Arch Linux ARM for SM8250 / SM8550 / SM8750 handhelds | (V) Updates through `pacman` with **their own signed repository**, pinned to **a tested snapshot** of the upstream packages ("locked by default, rolling if you want it"); btrfs snapshots + rollback docs; in-UI updater; install to internal storage with an uninstall / restore-bootloader path. | The "tested snapshot of upstream + own signed repo" model maps onto Fedora: a COPR project + `dnf versionlock` / a pinned compose for the risky packages (Mesa, libcamera, PipeWire). |
| [hashtagbasit/SteamOS-ARM-Port](https://github.com/hashtagbasit/SteamOS-ARM-Port) | 15 Oct 2026 | SteamOS for Snapdragon handhelds and tablets | (V) Polished docs site (install, devices, downloads, known issues), updates from the settings UI "no reflashing", install next to Android or on microSD, a "how it works" deep dive. | Docs site layout; "Restart into Android" UX. |
| [qualcomm-linux/qcom-deb-images](https://github.com/qualcomm-linux/qcom-deb-images) (+ [kernel](https://github.com/qualcomm-linux/kernel), [meta-qcom](https://github.com/qualcomm-linux/meta-qcom), lava-test-plans, qcom-linux-testkit) | 15 Oct 2026 | Qualcomm's own Debian images for IoT boards | (V) **The CI reference**: debos recipes; workflows for **mainline, linux-next, qcom-next and qcom-7.2 kernel flavours**; static checks; every image **flashed onto real boards in a LAVA lab** with boot then `pre-merge-basic / -bt / -display-gfx` tests; JUnit results published; OpenVEX + Grype vulnerability scanning; a known-failures list. kernel-topics commits must be FROMLIST / FROMGIT / UPSTREAM / BACKPORT, vendor-only ones QCLINUX. | (1) Daily canary builds against linux-next / qcom-next; (2) a known-failures file next to the test plan; (3) patch subject tags for status; (4) JUnit output from rehearsals. SM8850 is not a QLI target, so not a code source (see QUALCOMM-LINUX-KERNEL-2026-10-12.md). |
| Asahi Linux / Fedora Asahi Remix ([AsahiLinux/linux](https://github.com/AsahiLinux/linux), [asahi-installer](https://github.com/AsahiLinux/asahi-installer), [kiwi descriptions](https://git.resf.org/thefossguy/asahi-kiwi-descriptions/), [deviations](https://docs.fedoraproject.org/fr/fedora-asahi-remix/deviations)) | 15 Oct 2026 | Fedora remix for Apple Silicon | (V) **The model closest to ours (a Fedora remix on non-standard hardware)**: images built with **kiwi** from public descriptions (one branch per Fedora release; GNOME / KDE / Server / Minimal profiles); platform packages **delivered through COPR repositories**; a documented "deviations from Fedora" page; an installer that does all device-side work with clear prompts; Fedora's name used as a sanctioned remix; long-term goal: everything in Fedora proper (kiwi in Koji since F40). | kiwi (or osbuild) PC-side image build; COPR; a "deviations" page; Remix naming with Fedora's trademark guidelines checked (our working name "Fedora Remix for OnePlus Pad 4"). |
| [linux-surface/linux-surface](https://github.com/linux-surface/linux-surface) | 18 May 2026 | Surface devices (x86) | (I, well known) A patched kernel delivered for years through **signed apt / dnf / pacman repositories built by GitHub Actions**, with per-release patch sets per kernel series. | The proof that a single maintainer team can run signed multi-distro repos from Actions. |
| postmarketOS (pmaports / pmbootstrap on gitlab.postmarketos.org; [pipa packages](https://pkgs.postmarketos.org/package/main/postmarketos/aarch64/device-xiaomi-pipa)) | active | many Qualcomm phones / tablets | (V) Device = three small packages (`device-*`, `linux-*`, `firmware-*`); SoC-family kernels shared by devices; `pmbootstrap` builds images on the PC; a **CI hook in the initramfs** (`postmarketos-mkinitfs-hook-ci`, maintainer Casey Connolly) and a hardware CI effort since Sep 2024; firmware split into its own package. | Our split already matches (kernel / device / firmware); the initramfs CI hook idea matches our rehearsal; a postmarketOS port is a cheap "second distro" later. |
| Ubuntu Concept for Snapdragon X Elite ([discourse thread](https://discourse.ubuntu.com/t/ubuntu-concept-snapdragon-x-elite/48800)), [aarch64-laptops/build](https://github.com/aarch64-laptops/build), Johan Hovold's sc8280xp work ([Phoronix](https://phoronix.com/news/Two-Years-Improving-ARM-Laptops), [Fedora wiki X13s](https://fedoraproject.org/wiki/Thinkpad_X13s)) | 2025-2026 | Snapdragon laptops | (V) The laptop path: device tree upstream first -> distro kernels boot it -> firmware extracted from the vendor OS (`qcom-firmware-extract`). X13s usable on mainline since 6.5. Ubuntu's 26.04 regressed device support for some laptops (Phoronix, Mar 2026): even distro-backed ports break without device CI. | The end state to aim for: an upstream DT so Fedora's own kernel can boot the Pad 4; until then, CI against each rc. |
| Mobian ([mobian-recipes](https://salsa.debian.org/Mobian-team/mobian-recipes), [porting](https://wiki.debian.org/Mobian/Porting), [image CI](https://ci-images.mobian.org/)) | 2025 | Debian for phones (SDM845, SM7225) | (V) debos recipes; one kernel package for several Qualcomm SoCs; CI-built images. | Reference for the Debian plan (debos). |
| Droidian ([wiki](https://github.com/droidian/droidian)) | 2024 | Halium (Android kernel) | Not mainline; not comparable. | Nothing. |

---

## 3. Our system compared: gaps and redundancies

### 3.1 Kernel: rebase and upstreaming load

Queue composition on `iceland-7.3-rc7-next` (counted from the patch files):

| Block | Patches | Content |
|---|---|---|
| 0001-infiniti | 132 | the OnePlus 15 SoC/board tree (83 touch `drivers/`, 21 DTs); 3 carry a lore / patchwork `Link:` |
| 0002-iceland, other authors | 74 | upstream picks and backports (Victor Fuentes, map220v, Joonhoe Kim, Hangxiang Ma, Bartosz Golaszewski, Akhil P Oommen, Bryan O'Donoghue, ...); 50 carry a `Link:` |
| 0002-iceland, ours | 230 | 66 DT-only, 13 bindings-only, 2 mixed, **149 driver code** (drm 44, power/supply 21, net/wireless 20, media 25, soc/qcom 6, input 10, usb 9, thermal 5, ...) |

Reading of the numbers (I): about 80 of our patches are the board DT and its bindings, which are upstream-bound as
one `arm64: dts: qcom: add OnePlus Pad 4` series once the kaanapali base and its bindings are in mainline. Of the 149
code patches, the generic fixes (drm/msm, ath12k, qcom_battmgr, iris, dwc3, cpuidle) are upstream candidates; the
OPLUS charger / gauge, panel, touch and private-protocol parts are device-only and will stay in the queue longer.
**Gaps:** no per-patch status tag (upstream / sent / device-only / workaround), so every rebase re-judges each
patch by hand; no automatic "dropped because upstream" detection; 132 patches duplicated from infiniti that other
SM8850 ports (tb323fu, SuperTurtleDev) also carry in their own versions; nothing has been sent upstream yet.

### 3.2 Build reproducibility

We verify the *source* exactly (tree hashes per series: better than most ports) but not the *build*: builds run in
a hand-maintained WSL; the kernel rpms up to q89k carried the PC's build host name (from q89l on the kernel and
the rpm record a neutral one). Gap: no pinned build root, no buildinfo, no `SOURCE_DATE_EPOCH`. SuperTurtleDev's container shows the fix is small.

### 3.3 CI

We have one manual-only kernel workflow (its comment cites Actions minutes on private repos: no longer true, all
repositories are public and standard runners, including `ubuntu-24.04-arm`, are free for public repositories (I:
check GitHub's current terms)). Missing: privacy / unit-data scan on every push (today only in the commit scripts),
`checkpatch`, `dt_binding_check` / `dtbs_check` for the iceland DT, rpm builds of `iceland-device` and
`iceland-firmware`, shellcheck / unit tests of the device package (50+ tests exist but run only on the PC), a
linux-next / next-rc canary build.

### 3.4 Image build

The golden image is built by a **tablet-side B run** (the RAM-booted tablet installs packages onto a PC disk over
NBD). It needs the tablet and the cable for every image, and it cannot run while the tablet is in use with the
installed Fedora. Every other project builds images on a PC / CI (kiwi for Asahi, debos for
Mobian / Qualcomm, pmbootstrap, ROCKNIX's build system, SuperTurtleDev's container). With first-boot provisioning
(`iceland-provision`, 0.28-17 candidate) the image no longer needs anything from the unit, so it can be built
PC-side; the B run + rehearsal remain the acceptance test, not the builder.

### 3.5 Distribution of updates and rollback

Today: GitHub releases, install scripts (`install-q89k`-style), a local dnf repo synced over USB / LAN, not
published. Peers use signed repos (pocknix: own pacman repo on object storage; linux-surface: signed repos from
Actions; Asahi: COPR) and in-UI updaters (ROCKNIX, pocknix, SteamOS-ARM). Rollback: we have btrfs snapshots + a
kernel trial boot; an issue scan found the snapshot hook broken (the actions file got log lines on its stdout,
no pre-dnf snapshots) and the slot mark failing every boot; both are fixed in iceland-device 0.28-17 (not yet on
the tablet). Fedora-native options:
snapper + `python3-dnf-plugin-snapper` / grub-btrfs for snapshots, `grub2` boot counting (`boot_success`,
greenboot) for the trial; later bootc / Fedora Atomic for image-based A/B with rollback.

### 3.6 Installer UX

Ours: a Windows PowerShell installer with dry run default, per-write typed confirmation, backup first, a command
whitelist: stricter than every peer (most say "dd this image" or "flash ABL"). tb323fu adds Linux and macOS hosts
and a guided script; ROCKNIX / SteamOS-ARM document "back to stock" prominently. Gap: Windows only; no generic
image yet (B150g pending).

### 3.7 Testing

Our rehearsals (RAM boot of the exact image, 36-64 acceptance rows, no-regression sets, the issue-scan with 126
known patterns) are stronger on the device than any hobby port; tb323fu and Zenbook use manual "checked on the
device" rules, pmOS has a CI hook, only Qualcomm's own project runs a LAVA lab. Gaps: results are prose / logs, not
JUnit / machine-readable; test plans live in generator scripts; two harnesses (kits and rehearsals) still exist
although rehearsals replaced kits on 11 Oct; no scheduled canary.

### 3.8 Power and performance

Peers' tuning worth checking against ours: tb323fu keeps the CPU cluster idle state out of runtime idle because it
reset the tablet (`cpuidle_psci_domain.allow_cluster_off=0`): test our cluster idle under long idle; pocknix tunes
kernel, scheduler and graphics stack for frame pacing; SteamOS-ARM moved the UI off the slow cores and fixed GPU
clocking; ROCKNIX ships per-SoC governor defaults. Our 0.35 %/h deep sleep and 0.83-2.08 W idle are already good;
the open items are the 26-28 s GDM hand-over vblank timeouts and the auto-brightness glitch.

---

## 4. Roadmap

Effort: S (< 1 day), M (1-5 days), L (> 1 week). Benefit / risk: low / med / high. "Owner" = needs the project
owner's decision before work starts. No item publishes unit data; no item writes to the tablet; firmware stays in
`iceland-firmware`.

### 4.1 Now (next 2 weeks)

| # | Item | Effort | Benefit | Risk | Owner | First steps |
|---|---|---|---|---|---|---|
| N1 | **Static-gate CI on all public repos** (privacy / unit-data scan with the existing guard patterns, checkpatch on new patches, shellcheck, the iceland-device unit tests, `rpmbuild -bs` of the specs) on push and PR | S-M | high: guards run on every change, not only through commit scripts | low (read-only jobs) | yes (Actions on public repos) | Move the guard patterns into `tools/privacy-scan` + a `.github/workflows/gates.yml`; keep the masked values out of the repo (the scan reads hashes / patterns, not the values) |
| N2 | **DT checks** (`make dt_binding_check` + `dtbs_check` for the iceland and infiniti DTs) in the kernel workflow | S | med: catches binding drift before upstreaming | low | with N1 | Add a job after `prepare.sh`; record today's warnings as the baseline |
| N3 | **Patch status tags** in the queue: one field per patch (UPSTREAM / FROMLIST / BACKPORT / DEVICE / WORKAROUND, as in Qualcomm's kernel-topics rules) in a `patches/STATUS.tsv`; a rebase helper that drops patches whose patch-id is in the new base (`git cherry`) | M | high: rebases become mechanical; shows the upstream backlog | low | no | Generate the TSV from authors + `Link:` trailers (section 3.1 counts), then hand-check the 230 own patches |
| N4 | **Pinned build root + buildinfo** for kernel and rpms (podman rootfs like SuperTurtleDev's, or a Fedora 44 aarch64 container / mock), `SOURCE_DATE_EPOCH`, `KBUILD_BUILD_HOST/USER` set to neutral values, `buildinfo.txt` (source hashes, toolchain, artifact sha256) attached to each release | M | high: reproducible releases; removes the host-name leak | low | no | Write `build/container/` with a package list; rebuild q89k inside it and compare the rpm payload |
| N5 | **Fix the rollback basics found by the issue scan** (snapshot action syntax, slot mark) and decide on snapper + grub-btrfs vs `iceland-snapshot` | S-M | high: today there are no pre-update snapshots | low | no | Fixed in iceland-device 0.28-17 (not yet on the tablet); add a rehearsal row "dnf update creates a snapshot" |

### 4.2 Next (2-6 weeks)

| # | Item | Effort | Benefit | Risk | Owner | First steps |
|---|---|---|---|---|---|---|
| X1 | **Signed dnf repository (COPR)** for `kernel-iceland`, `iceland-device`, `iio-sensor-proxy`, `libssc`; channels `testing` and `stable` (two COPR projects); the device keeps the kernel trial boot | M | high: `dnf upgrade` / GNOME Software replace bundles and LAN shares | med: a bad push reaches users (mitigate: testing channel, rehearsal before promotion) | **yes** | Owner OK for COPR; build the srpms already published there; `iceland-repo` package with the `.repo` file; check whether COPR accepts `iceland-firmware` (firmware licensing): if not, serve it from a GitHub Pages dnf repo signed with a project key |
| X2 | **PC-side image builder** (kiwi, as Fedora Asahi Remix; or osbuild / image-builder blueprints) on an arm64 runner or in a podman aarch64 container, consuming X1's repo; output the generic image (B150g layout, grown at first boot, unit data provisioned at first boot) | L | high: images without the tablet; CI can build them; B run becomes the acceptance step | med (new toolchain; must reproduce the golden image's package set and partition layout) | yes (generic image publication) | Port the golden image's package list and layout to a kiwi description; diff the package manifest against B149; RAM-boot rehearsal of the kiwi image |
| X3 | **Canary builds**: weekly kernel build of the queue on the next rc and on linux-next / the msm tree (build + DT checks only; boot only in an owner-approved rehearsal) | M | high: rebase pain found early; feeds N3 | low | with N1 | Copy the structure of qcom-deb-images' `linux-next.yml`; report which patches fail to apply |
| X4 | **Machine-readable rehearsal results**: each row emits JUnit / TAP; a `known-failures.tsv` beside the plan (issue-scan already has `known-issues.tsv`); retire the kit harness | M | med: regressions visible at a glance; less code | low | no | Wrap the row runner's PASS / FAIL / CHECK into JUnit |
| X5 | **Upstreaming, first wave** (only after the owner agrees to public mailing-list work): small generic fixes with clear Fixes: tags (drm/msm DPU, ath12k, qcom_battmgr, iris, dwc3) via `b4 prep` / `b4 send`; then the iceland DT + bindings series once the kaanapali base is in | L | high: shrinks the queue for every rebase | med (review rounds, time) | **yes** | Pick 5 self-contained fixes from N3's list; run `checkpatch --strict` and `get_maintainer.pl`; draft cover letters |
| X6 | **Shared SM8850 base with the other ports** (infiniti, tb323fu / kaanapali-mainline, SuperTurtleDev): one common SoC branch, device queues on top | M (talk) / L (do) | high: removes the 132-patch duplicate | med (coordination, different bases: 7.2.9 stable vs 7.3-rc) | **yes** (contact) | Open a discussion / issue on kaanapali-mainline proposing a shared `kaanapali-7.3` branch; compare the three trees' SoC patches by patch-id |
| X7 | **Docs site + community** (GitHub Pages from the public docs, Diataxis split: tutorial = install, how-to = update / rollback / back to stock, reference = features + hardware, explanation = boot chain); Discussions for device reports; SECURITY.md, CONTRIBUTING with DCO, REUSE compliance | M | med: other Pad 4 owners can use and report | low | yes (Discussions) | Start from tb323fu's structure; generate the features page from `features-data.py` |
| X8 | **Installer on Linux / macOS hosts** (Python or bash port of the PowerShell installer with the same whitelist and typed confirmations) | M | med | med (write tool on new hosts) | yes | Reuse the manifest and the command-guard test cases |

### 4.3 Later (6+ weeks)

| # | Item | Effort | Benefit | Risk | Owner | First steps |
|---|---|---|---|---|---|---|
| L1 | **Image-based updates with rollback** (bootc / Fedora Atomic-style image, or kiwi A/B on btrfs): a whole-system update either boots or rolls back | L | high for non-technical users | high (new boot flow, the loop root on `userdata`, U-Boot EFI interplay) | **yes** | Prototype a bootc image in a rehearsal only; keep the mutable Fedora as default |
| L2 | **Second distro** (the existing Debian plan; or a postmarketOS port, cheapest given its device / kernel / firmware split) using distro-neutral platform files as tb323fu does | L | med | low (subvolume install, no partition writes) | **yes** | Split `iceland-device` into neutral files + a Fedora wrapper first |
| L3 | **Fedora proper** (Asahi's path): once the DT is upstream, ask Fedora ARM whether the stock kernel + our device package can boot the Pad 4; the remix shrinks to firmware + device package | L | high long term | low | yes | After X5's DT series is merged |
| L4 | **Power / performance tuning round** with peers' findings: cluster idle under long idle (tb323fu reset), UI on big cores / GPU clock floors (SteamOS-ARM), frame pacing (pocknix), per-mode governor defaults | M | med | med (thermal: stock limits stay) | partly | Add these as rehearsal rows; compare with GOVTUNE-2026-10-14.md |
| L5 | **Hardware CI** (a LAVA-like loop: the PC RAM-boots the image on a schedule and publishes results) | L | high but needs the tablet permanently connected | med (battery, the owner's use of the tablet) | **yes** | Only if a second unit or a fixed bench becomes available |

### 4.4 Decisions the owner is asked for

1. Enable GitHub Actions gates on the public repositories (N1-N2, X3).
2. A public COPR (or a signed GitHub Pages repo) as the update path, and its channels (X1).
3. Publication of the generic install image once built PC-side (X2), and the name "Fedora Remix for OnePlus Pad 4"
   checked against Fedora's trademark guidelines.
4. Upstream submissions under the owner's name (X5) and contact with the other SM8850 ports (X6).
5. Discussions / community intake (X7) and a Linux / macOS installer (X8).
6. Image-based updates (L1) and a second distro (L2).

---

## 5. Five lessons from the other ports

1. **Build everything on the PC / CI, test on the device.** Every mature project (Asahi, ROCKNIX, Qualcomm,
   pmOS, SuperTurtleDev) builds images away from the device; the device only runs acceptance tests. Our B run
   couples the two.
2. **A signed package repository is the update path.** pocknix, linux-surface and Asahi ship updates through signed
   repos with a tested or pinned channel; bundles and LAN shares do not scale beyond one tablet.
3. **Tag the patch queue by upstream status and track linux-next continuously.** Qualcomm's own trees refuse untagged
   commits and build linux-next daily; this is what keeps rebases cheap.
4. **Pin the build environment and record buildinfo.** SuperTurtleDev's byte-identical builds show that a small
   container script removes "works on my WSL" and identifying build metadata.
5. **Shared SoC base, thin device layer, distro-neutral platform files.** pipa, sm8x50-mainline orgs, tb323fu and
   pmOS all separate SoC, device and distro; three SM8850 ports each carrying their own SoC copy is the largest
   duplicated effort in this space.

## Sources

GitHub repositories as linked above (metadata through the GitHub API, 16 Oct 2026). Web:
[Ubuntu Concept X Elite](https://discourse.ubuntu.com/t/ubuntu-concept-snapdragon-x-elite/48800),
[Phoronix Ubuntu 26.04 X Elite](https://phoronix.com/news/Snapdragon-X-Elite-Ubuntu-26.04),
[Phoronix ARM laptops](https://phoronix.com/news/Two-Years-Improving-ARM-Laptops),
[Fedora wiki X13s](https://fedoraproject.org/wiki/Thinkpad_X13s),
[Fedora Asahi Remix deviations](https://docs.fedoraproject.org/fr/fedora-asahi-remix/deviations),
[asahi kiwi descriptions](https://git.resf.org/thefossguy/asahi-kiwi-descriptions/),
[postmarketOS pipa packages](https://pkgs.postmarketos.org/package/main/postmarketos/aarch64/device-xiaomi-pipa),
[postmarketOS mkinitfs CI hook](https://pkgs.postmarketos.org/package/master/postmarketos/aarch64/postmarketos-mkinitfs-hook-ci),
[postmarketOS FOSDEM 2025 post](https://postmarketos.org/blog/2025/02/10/fosdem-and-hackathon/),
[automated phone testing](https://blog.brixit.nl/automated-phone-testing-pt-1/),
[ROCKNIX 20260901 release](https://newreleases.io/project/github/ROCKNIX/distribution/release/20260901),
[Mobian porting](https://wiki.debian.org/Mobian/Porting),
[Mobian FOSDEM 2024 slides](https://archive.fosdem.org/2024/events/attachments/fosdem-2024-3290-towards-a-bright-future-with-mobian-/slides/22436/Mobian_FOSDEM24_uiJwzEa.pdf).
