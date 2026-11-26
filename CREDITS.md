# Credits

The OnePlus Pad 4 (`iceland`) port stands on the work of many people. This page lists every developer, project and
public tree whose code, patches, files or findings the project uses, and what was taken from each. Names are public
names or GitHub handles as the authors publish them.

How the credit is kept:

- **Imported code keeps its author.** The kernel ([iceland-linux](https://github.com/mzakamin-hub/iceland-linux)) and
  U-Boot ([iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot)) are patch queues on upstream tags: every
  commit keeps its original author, and picked patches say where they come from in the commit message. Package
  patches keep their `From:` line; copied or adapted files keep their licence header and say what they were adapted
  from.
- **"Re-implemented"** marks a change whose idea, analysis or measurement comes from the named person while the code
  was written here (usually because the source had no Signed-off-by). **"Reference only"** marks a source that was read
  or compared, with nothing copied.
- **The project's own work** is by mzak, written with Claude (Anthropic) as an AI coding assistant; the commits that
  Claude helped write carry a `Co-Authored-By: Claude` trailer. The placeholder identities `iceland-dev`,
  `iceland project`, `Iceland packaging` and `DexHid project` in some commits and patches are the project itself. No
  third-party work listed here is claimed as our own.

## Linux kernel

### Upstream Linux

- **[Linux](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git)** (Linus Torvalds and the kernel
  community): the base of the queue (v7.4-rc4).
- **The Qualcomm SoC maintainers and contributors** (linux-arm-msm: the `arm64/qcom` device tree, clock, interconnect,
  pinctrl, remoteproc, power, DRM/MSM, Iris video, CAMSS, ath12k, sound and UFS subsystems), including Qualcomm's
  upstream team and Linaro. The Kaanapali (SM8850) SoC support upstream is theirs.
- **Patches picked before they reached Linus' tree**, each named in its commit message: from the mailing lists
  ([lore.kernel.org](https://lore.kernel.org/linux-arm-msm/), patchwork.kernel.org, patchwork.linuxtv.org),
  [qualcomm-linux/kernel-topics](https://github.com/qualcomm-linux/kernel-topics) and
  [qualcomm-linux/kernel](https://github.com/qualcomm-linux/kernel) `qcom-next` (FROMLIST picks), drm-misc-next and
  linux-next.
- Named among many: **Rob Clark** (21 Adreno A8xx / DRM MSM patches), **Dmitry Baryshkov** (16, display), **Bartosz
  Golaszewski**, **Konrad Dybcio**, **Krzysztof Kozlowski**, **Neil Armstrong**, **Abel Vesa**, **Akhil P Oommen**,
  **Sibi Sankar** and **Pragnesh Papaniya** (SCMI vendor extensions), **Vishnu Reddy** and **Vikash Garodia** (Iris),
  **Peter Chen** (the USB `snps,resume-hs-terminations` setting), **Xilin Wu** (Iris decoder fixes), and the authors in
  the full list below.
- **[Sashiko](https://sashiko.dev)**: automated review reports, credited as `Reported-by` in the fixes they led to.

### Gunyah hypervisor drivers

- **The Android Common Kernel** (Google and Qualcomm, the Gunyah authors): the Gunyah driver stack
  (`drivers/virt/gunyah`, the arm64 hypercall wrappers, the UAPI) is imported unchanged from tag
  `android17-6.18-2026-06_r1` of [android/kernel/common](https://android.googlesource.com/kernel/common) and then
  adapted to mainline in separate commits.

### Kaanapali (SM8850) device ports

- **[infiniti-mainline/linux](https://github.com/infiniti-mainline/linux)**, **Victor Fuentes** (OnePlus 15, same SoC):
  the Kaanapali base the queue started from: 70 commits (device tree: DisplayPort, modem, firmware carveouts, RPMh
  stats, PMK8850 reboot mode, the OnePlus 15; drivers: qrtr, ath12k, Iris, ...), authors kept.
- **[map220v/sm8850-mainline](https://github.com/map220v/sm8850-mainline)**, **map220v**: the first OnePlus Pad 4 port:
  15 commits (the Pad 4 device tree, panel, touchscreen and sound nodes, the NT36536 touch, KTZ8869 backlight and
  TFA9865 amplifier drivers, the memory reservations), plus the panel's init sequence, modes and DSC parameters and the
  basic battery-manager support, which our drivers are based on.
- **[SuperTurtleDev/iceland-mainline-kernel](https://github.com/SuperTurtleDev/iceland-mainline-kernel)**,
  **SuperTurtleDev**, with commits by **Yibo Wang**: the SCMI quirk for the CPUCP's first notification, the RTC 64-bit
  offset, `power_now` on Kaanapali, an ath12k scan fix and the Gunyah GuestAccept ioctls (picked, authors kept); the
  RTC offset kept in SDAM, L2F always on, the panel's 50 / 48 Hz values and the in-kernel Horae shell-temperature
  estimator follow their findings (re-implemented).
- **[joonhoekim/tb323fu-linux](https://github.com/joonhoekim/tb323fu-linux)**, **Joonhoe Kim** and contributors
  (Lenovo Legion Tab Gen 5 / TB323FU, same SoC): 27 commits (DisplayPort and the USB-C mux, DSI PHY runtime suspend,
  UCSI, the NT36536 pen reports, ...), the memlat DVFS series, and ported fixes such as DP stream clocks.

### Related Snapdragon ports

- **[yzddmr6/linux-sm8750-piano](https://github.com/yzddmr6/linux-sm8750-piano)**, **yzddmr6** (Xiaomi Pad 8 Pro,
  SM8750): the bonded-DSI slave teardown fix picked (author kept); the CPU latency limit during
  GPI DMA is re-implemented from this tree.
- **[slwyts/Project-SunUEFI](https://github.com/slwyts/Project-SunUEFI)**, **slwyts**: three patches picked (the DSP
  sleep notification, freezable FastRPC waits, the SM8750 bonded-slave clock restore); the DSP sleep protocol follows
  [MiCode/Xiaomi_Kernel_OpenSource](https://github.com/MiCode/Xiaomi_Kernel_OpenSource) (reference only).
- **[armada-os/armada](https://github.com/armada-os/armada)**, **the Armada contributors**: kernel patches picked (SMP2P
  inbound state on restart, Iris decoder power, the tsens lower-threshold mask by **virtudude**); the
  DSPP LUTDMA port and the thermal-model idea of PR 662 are reference only. Mesa patches below.
- **[portare-ch/portareos](https://github.com/portare-ch/portareos)**: patches picked (UFS RX LineCfg and hibern8 by
  **jaewun**, UFS clock gating across system PM by **gh123man**, an ath12k sleep warning by **Edouard Durand**).
- **[TheMojoMan/oneplus-erhai-linux](https://github.com/TheMojoMan/oneplus-erhai-linux)**, **TheMojoMan** (OnePlus Pad
  3, SM8750): the Iris capture-buffer and decode-order fixes are re-implemented from their findings and measurements.
- **[denialwm/linux-perpetua](https://github.com/denialwm/linux-perpetua)**, **Doctor Logix** (denialwm): the Perpetua
  kernel's analyses and ideas (GPU preemption reset and HFI interrupts, thermal sensors and CPU cooling backstops,
  Wake-on-WLAN, the CSI PHY reset, ramoops, battery-manager request matching), re-implemented.
- **[Reixo0/linux](https://github.com/Reixo0/linux)** and **[Reixo0/nx809j-mainline](https://github.com/Reixo0/nx809j-mainline)**,
  **Reixo0** (RedMagic 11 Pro, SM8850): the DisplayPort PHY and runtime-PM findings, the Iris firmware error report,
  the MDP SS clock, the GPU devfreq threshold and PCIe measurements, re-implemented.
- **[Osilvfe/linux](https://github.com/Osilvfe/linux)**, **Osilvfe**: the UCSI notification quiesce over sleep
  (branch `caihong-v7.3`), re-implemented. Their libcamera patches are below.

### Charging

- **[dappermint/iceland-supervooc](https://github.com/dappermint/iceland-supervooc)**, **dappermint** (git identity
  "millia ampora"): the SuperVOOC driver, its VOOC frame engine, host tests and thermal guards, imported with the
  original commits unchanged (GPL-2.0), plus the battery-manager charger hold. Details in the driver's `CREDITS` file in
  iceland-linux.
- **DocZ13**: the SC8547D charge-pump driver and facts (iceland-linux issue #2) that the SuperVOOC handover builds on.
- **OnePlus**: the open-source `oplus_chg` charging code
  ([OnePlusOSS](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8850)) that the frame
  engine follows (OnePlus copyright lines kept in derived code), and the stock 9 V USB-PD request (reference).
- **[jstockdale](https://github.com/jstockdale)**: the CPU-latency observation behind the SuperVOOC session setting.

### All authors of picked kernel commits

Every non-project author of a commit in the current queue (q92d on v7.4-rc4), alphabetical; the commits themselves
carry the details. Co-developers named in `Co-developed-by` trailers are included.

Abel Vesa, Abhinaba Rakshit, Ajay Kumar Nandam, Akhil P Oommen, Alice Ryhl, Amir Vajid, Anandu Krishnan E,
Ananthu C V, Andrey Karelin, Anjelique Melendez, Anna Maniscalco, Anup Vishwakarma, Armada, Arun Iyengar,
Atiya Kailany, Atul Akella, Baochen Qiang, Bart Van Assche, Bartosz Golaszewski, Bibek Kumar Patro, Birk Skyum,
Cen Zhang, Changyul Lee, Chrispine Tinega, Christian Schmidbauer, Christopher Griffin, Connor Abbott,
Daniel Lezcano, David Vornholt, Dmitry Baryshkov, Edouard Durand, Elson Serrao, Fabricio Akio, Fenglin Wu,
François Roux, Fuad Tabba, Gaole Zhang, gh123man, Gianni Spadoni, Gopi Chandra Sekhar Reddy Kanala,
Griffin Kroah-Hartman, Guangshuo Li, Guo Chen, Hangtian Zhu, Hangxiang Ma, Haobo Cheng, Haoxiang Li, HOYOUNG SEO,
Hungyu Lin, Ian Rogers, Igor Borodin, Igor Opaniuk, Ingo A. Kubbilun, Iranna Mundaganur, jaewun,
Jan Sebastian Götte, Jean-Francois Bobier, Jesse Casco, Jeuk Kim, Jia Yang, Jianping Li, Jie Zhang, Jingyi Wang,
Jishnu Prakash, Jiwoo Kim, Jizhou Tong, Jonathan Wolf, Joonhoe Kim, Jorge Ramirez-Ortiz,
Jose Ignacio Tornos Martinez, Julius Bairaktaris, Jun Nie, Kaiqian Zhu, Kenneth Kabogo, Konrad Dybcio,
Krishna Chaitanya Chundru, Krishna Kurapati, Krzysztof Kozlowski, Kuldeep Singh, Lee Jones, Loic Poulain,
Lorenzo Bianconi, Luiz Augusto von Dentz, Manivannan Sadhasivam, map220v, Marek Szyprowski, Matthew Brost,
Maulik Shah, Miaoqing Pan, Michael Burch, Michael McAllister, millia ampora (dappermint), Mohammed AlHashim,
Mohammed Alquraini, Muhammad Huda Nugroho, Mukesh Kumar Savaliya, Neil Armstrong, Nick Rogers,
Nico Angelo Dela Cruz, Nitin Rawat, Oleg Keri, Oleksandr Suvorov, Perry Dale, Peter Chen, Philip Radford,
Philipp Stanner, Pragnesh Papaniya, Prakash Gupta, Prashanth K, Praveen Talari, Qiang Yu, Qianhui Xu,
Rafael J. Wysocki, Rahul Pon, Ramakrishna Gottimukkula, Ramón Jesús Miranda, Rob Clark, Rupesh Majhi, Saim Shujah,
Salendarsingh Gaud, Sam Day, Sarannya S, Shawn Guo, Shawn Lin, Shenghan Gao, Shirong Zhao, Shivendra Pratap,
Sibi Sankar, slwyts, Sreeraj S Kurup, Stanley Jhu, Tapas Rana, Teguh Sobirin, Thomas Fourier, Tvrtko Ursulin,
Val Packett, Venkata Siva Pavan KumarVenkatapatigari, Victor Fuentes, Vikash Garodia, Viken Dadhaniya, virtudude,
Vishnu Reddy, Vitor Soares, Vladyslav Tymoshchuk, Vsevolod Nevorotov, Wang Haoran, Wangao Wang, Wentao Liang,
Xi Zhang, Xilin Wu, Xin Liu, Xu Qianhui, Xu Rao, Yaohan Li, Yibo Wang, Yongxing Mou, Yu Zhang, yzddmr6, Zhao Feng,
Zhao Li.

## Boot

- **[U-Boot](https://github.com/u-boot/u-boot)** (the U-Boot community): the base of iceland-u-boot
  (v2026.10-rc5).
- **[infiniti-mainline/u-boot](https://github.com/infiniti-mainline/u-boot)**, **Victor Fuentes**: 14 commits (Kaanapali
  clocks, eUSB2, the PMIC arbiter, the ABL memory map, EFI from `userdata`, the OnePlus 15), authors kept; the boot
  path (ABL, U-Boot in `boot`, EFI) is the OnePlus 15's.
- **AOSP `mkbootimg`** (Apache-2.0), fetched at build time from the
  [LineageOS mirror](https://github.com/LineageOS/android_system_tools_mkbootimg).
- **[GRUB](https://www.gnu.org/software/grub/)**, **systemd** (`kernel-install`, the boot loader spec) and
  **[dracut](https://github.com/dracut-ng/dracut-ng)**: the rest of the boot chain.

## Firmware

- **Qualcomm Technologies / Qualcomm Atheros, Novatek and OnePlus (OPLUS)**: the proprietary firmware the tablet
  needs, redistributed unmodified from stock 11.A.38 in
  [iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware) with the vendors' notices. The optional GMU
  5.3.33 / SQE pair comes from another Kaanapali vendor image (Lenovo TB323FU, ZUI 18.0.12.104).
- **[SuperTurtleDev/iceland-mainline-kernel-firmware](https://github.com/SuperTurtleDev/iceland-mainline-kernel-firmware)**:
  the file-by-file sha256 comparison (`superturtle-compare.tsv`), the copy of Qualcomm Atheros' WCN7860 notice, and a
  byte-identical cross-check of the GMU 5.3.33 pair.
- **[map220v/iceland-firmware](https://github.com/map220v/iceland-firmware)**: the firmware file names the drivers ask
  for, and a cross-check of the GPU files (its other files differ from 11.A.38 and are not used).
- **[joonhoekim/tb323fu-linux](https://github.com/joonhoekim/tb323fu-linux)**: the TB323FU firmware manifest, the
  third cross-check of the GMU 5.3.33 pair.
- **[troikoss/gts9wifi-fedora](https://github.com/troikoss/gts9wifi-fedora)**: lessons on firmware families and early
  firmware in the initramfs (reference only).
- **[linux-firmware](https://gitlab.com/kernel-firmware/linux-firmware)**: the distribution's generic firmware files.

## Userspace packages (packaging/arch)

- **[Mesa](https://gitlab.freedesktop.org/mesa/mesa)** (the freedreno / turnip / ir3 developers): `mesa-iceland` is a
  Mesa staging/26.3 snapshot with merge requests picked ahead of release, by Armada, Artem Peshkov, Birk Skyum, Connor
  Abbott, Danylo Piliaiev, Dhruv Mark Collins, Emma Anholt, Fabricio Akio, Job Noorman, Karmjit Mahil, Lakshman Chandu
  Kondreddy, Nicholas Iquan Gaspard, Sahitya Kandru, tobias, Valentine Burley and Vamsi Chitta; plus the
  **[Armada](https://github.com/armada-os/armada)** A8xx GL hang fixes 0016 / 0017 (PR 894, MIT, see
  `NOTICE-armada-patches.txt`).
- **[libcamera](https://libcamera.org/)** (the libcamera developers): 0.7.2 with Fedora's two patches and the autofocus
  patches 0001-0003 by **[Osilvfe](https://github.com/Osilvfe/libcamera)** (manual focus, the soft-ISP focus metric,
  contrast-detect autofocus).
- **[iio-sensor-proxy](https://gitlab.freedesktop.org/hadess/iio-sensor-proxy)** (Bastien Nocera and contributors), with
  patches by **Jan-Michael Brummer** and **Michael McAllister**.
- **[libssc](https://codeberg.org/DylanVanAssche/libssc)**, **Dylan Van Assche**: the Qualcomm sensor-hub client.
- **[hexagonrpc](https://github.com/linux-msm/hexagonrpc)** and **[qbootctl](https://github.com/linux-msm/qbootctl)**
  (linux-msm), and **[audioreach-topology](https://github.com/linux-msm/audioreach-topology)** (Linaro): the FastRPC
  daemon, the A/B slot tool and the AudioReach DSP topology our sound topology is built from.
- **[UPower](https://gitlab.freedesktop.org/upower/upower)**, **[NetworkManager](https://networkmanager.dev/)** (with two
  nm-1-58 backports by **Josephine Pfeiffer**), **[power-profiles-daemon](https://gitlab.freedesktop.org/upower/power-profiles-daemon)**,
  **[PipeWire](https://pipewire.org/)** and **WirePlumber**: the upstream projects our packages and settings build on.
- **[jstockdale/ubuntu-oneplus-pad-4](https://github.com/jstockdale/ubuntu-oneplus-pad-4)**, **jstockdale** and the
  Ubuntu OnePlus Pad 4 port contributors: the PipeWire / WirePlumber clock and compressed-offload settings, adapted
  (BSD-3-Clause, `LICENSE.BSD-3-Clause.ubuntu-iceland`), and the measurements on the same sound card.
- **[joonhoekim/tb323fu-linux](https://github.com/joonhoekim/tb323fu-linux)** userspace (MIT, Joonhoe Kim and
  contributors): the speaker protection chain, the raw speaker sink and the DMA-heap rule, adapted.
- **[samyn92/omarchy-pad](https://github.com/samyn92/omarchy-pad)** (MIT): the power-key hold logic, the Bluetooth agent
  drop-in and browser settings of the optional `iceland-device-hypr` package (Omarchy / Hyprland; not used on the
  project's tablet).

## Android and virtual machines

- **[DroidLoom](https://github.com/denialwm/droidloom)** (denialwm): Android apps on the tablet, installed from its own
  pacman repository; `iceland-device` adds only launchers that call its own commands.
- **[DroidVM](https://github.com/Droid-VM)**: from its [crosvm fork](https://github.com/Droid-VM/crosvm) the
  simple-framebuffer display, the VNC display and the pseudo-unprotected memory mode with its boot shim (ported, with
  DroidVM's headers and additional permissions), the [edk2-gunyah](https://github.com/Droid-VM/edk2-gunyah) UEFI
  firmware, the guest kernel's `gunyah_guest` driver, and the GuestAccept share design; details in iceland-gvm's
  `crosvm/CREDITS`.
- **[crosvm](https://chromium.googlesource.com/crosvm/crosvm)** (the ChromiumOS authors, BSD-3-Clause) with its Gunyah
  backend, **[virglrenderer](https://gitlab.freedesktop.org/virgl/virglrenderer)** (with four upstream Venus fixes),
  **[QEMU](https://gitlab.com/qemu-project/qemu)** with the Gunyah accelerator of
  **[qemu-gunyah/qemu-android-gunyah](https://github.com/qemu-gunyah/qemu-android-gunyah)** and
  [edk2-gunyah-qemu](https://github.com/qemu-gunyah/edk2-gunyah-qemu), and **LibVNCServer**: the VM stack of
  iceland-gvm and iceland-vms.
- **[LineageOS](https://lineageos.org/)**: the Android side's device and vendor trees follow its structure; its
  [sm8850-common](https://github.com/LineageOS/android_device_oneplus_sm8850-common) tree was the reference for the
  Android partition layout, and LineageOS on the tablet was the stock-DSP reference for speaker measurements.

## Distributions, desktop and tools

- **[Arch Linux ARM](https://archlinuxarm.org/)** and **[Arch Linux](https://archlinux.org/)**: the system the tablet
  runs; the libcamera and NetworkManager PKGBUILDs start from Arch's packaging.
- **[Fedora](https://fedoraproject.org/)**: the project's earlier base; the Mesa, libcamera and NetworkManager builds
  keep options and patches of Fedora's packages.
- **[KDE](https://kde.org/)**: KDE Plasma 6.8, KWin, Plasma Login Manager, plasma-keyboard and PowerDevil.
- **[postmarketOS](https://postmarketos.org/)**: the USB network convention of the RAM-boot tools and the patch-queue
  approach to kernel packaging.
- **stock OnePlus software** (OxygenOS 11.A.38 and the OnePlusOSS sources): the reference for stock limits, the
  thermal model, the PMIC power-on log layout and charging behaviour (reference only; no vendor code is in this
  repository).

If something you made is used here and is missing or wrongly credited, please open an issue.
