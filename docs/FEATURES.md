# OnePlus Pad 4 mainline: feature matrix

Status 2026-09-29 (morning). Everything is tested by **RAM boot**; nothing is installed on the tablet yet (the
install is the last step). Kernel: Linux 7.3-rc4 + infiniti (138) + Pad 4 queue 0001–0045.
Legend: ✅ done · 🟡 partly working / in progress · ⬜ pending · ❌ out of scope / not planned.
Details: [TODO.md](TODO.md), [PLAN.md](PLAN.md), [KNOWLEDGE.md](KNOWLEDGE.md) §13, `relay/results/`.

## Boot and platform
| Feature | Status | Notes |
|---|---|---|
| ABL RAM boot of U-Boot | ✅ | nothing written; header v4, gzip(u-boot.bin) |
| U-Boot: display, USB fastboot, UFS read, EFI | ✅ | fastboot flash compiled out |
| U-Boot dual-boot boot command (`fedora` partition, else `userdata`) | ✅ | built; used at install |
| Linux boot via EFI, 7.3-rc4 | ✅ | |
| Fedora 44 in RAM (systemd as PID 1, dnf through the PC) | ✅ | pc-024 |
| **GNOME Shell 50** (gdm autologin) | ✅ | in RAM |
| Firmware extractor (modem_a, bluetooth_a, persist; read-only) | 🟡 | `super` (vendor/odm) not mapped yet |
| Installed system (Fedora on UFS) | ⬜ | final step; needs the user's decisions and OK |
| Dual boot Android + Fedora (U-Boot in recovery) | ⬜ | planned (4-DB); helper script ready |

## Display, input
| Feature | Status | Notes |
|---|---|---|
| Boot splash kept → native MSM DRM | ✅ | INT2 GDSC fix |
| Panel 3392x2400, dual DSI + DSC | ✅ | |
| Refresh 120 / 90 / 60 / 30 Hz; **144 Hz** | ✅ | 144 Hz after the DPU clock-factor fix |
| Backlight (KTZ8869) | ✅ | brightness range and curve from stock: audit pending (relay 013) |
| **GNOME pink/blocky glitches** | 🟡 | new bug; isolation running (relay 011: UBWC / 144 Hz / Mesa) |
| Touchscreen (NT36536, SRAM firmware) | 🟡 | driver + firmware + libinput OK; a real touch not confirmed by a person |
| Pen input | 🟡 | tablet capabilities fixed, libinput accepts it; strokes not confirmed |
| Lid switch | 🟡 | DT + debounce done; closing not tested |
| Power / volume keys | ✅ | |
| Pogo keyboard | ⬜ | private UART protocol (P3) |
| Screen rotation (sensors) | ⬜ | needs the SSC sensors |

## Graphics, compute
| Feature | Status | Notes |
|---|---|---|
| GPU Adreno 840 (freedreno, Mesa 26.2) | ✅ | GLES 3.2, kmscube 120 fps, glmark2 1836 |
| Wayland compositing on the GPU | ✅ | cage and GNOME |
| GPU validation (dEQP, WebGL, stress, devfreq) | ⬜ | relay 012 B |
| Vulkan (turnip) | ⬜ | waiting for Mesa a840 support |
| Hardware video decode (Iris) | ⬜ | driver in the tree; firmware known |
| **NPU** (Hexagon NSP on the CDSP, FastRPC) | ⬜ | DT and driver present; bring-up is relay 012 C |

## Connectivity
| Feature | Status | Notes |
|---|---|---|
| Wi-Fi (WCN7860, ath12k) | ✅ | NetworkManager, scan; `qdss.cfg` needed |
| Wi-Fi 5/6 GHz, regulatory domain | 🟡 | regulatory domain **US** (the user's choice; the firmware refuses EG): 2.4/5/6 GHz enabled; a 5/6 GHz connection not tested yet (no AP in range) |
| Bluetooth (hci_qca) | ✅ | the tablet's own address applied |
| Bluetooth pairing under GNOME | ⬜ | |
| USB device mode / USB network | ✅ | |
| USB host / OTG, PD hub, reverse charging | ⬜ | OTG glink message (relay 007) |
| DisplayPort over USB-C | ⬜ | |

## Audio
| Feature | Status | Notes |
|---|---|---|
| ADSP + AudioReach sound card | ✅ | |
| **Speakers** (6× TFA9865 on primary TDM) | ✅ | play at the ALSA level (0038, 0041–0045) |
| **Microphones** (2 analog mics, WCD9395) | ✅ | capture works; mixer settings, no kernel change |
| UCM profile for PipeWire/GNOME | 🟡 | worked inside the S9 probe only; **the user still sees Dummy Output and no mic on a normal boot** (profile not in the rootfs, routes not set before WirePlumber, no alsa-utils): answer user-report-dummy-output |
| Speaker volume caps + stock channel layout | 🟡 | cap in kernel + topology + UCM (−12 dB placeholder, answer pc-026-s8-s9); stock value and channel layout pending |
| Speaker protection (TFA9865 `tfa98xx.cnt`) | ⬜ | very hard (closed); volume capped until then |
| Headset (USB-C analog) | ⬜ | no 3.5 mm jack; WCD paths noted |

## Power and thermals
| Feature | Status | Notes |
|---|---|---|
| Battery % / voltage / current / temperature / health | ✅ | battmgr over SoCCP; units fixed; design capacity from DT |
| UPower / GNOME battery | ✅ | |
| Charging (firmware basics, 5 V / PD) | 🟡 | works; **the inherited code used OnePlus 15 limits (12 V / 3 A / 4 A)**: fixed to the Pad 4 stock per-type inputs (PD 13.5 W: 1.5 A at 9 V) in relay 015, verified in research/battery-guard-verification.md |
| Charging safety (derating, termination, dual cells) | 🟡 | `iceland-battery-guard` with stock limits written and tested offline; the tablet test and charge-inhibit knob are next (relay 015) |
| Charge limit (80 %) in GNOME | ⬜ | |
| Fast charging (SuperVOOC / PPS / UFCS) | ❌ | OnePlus kernel stack; PPS maybe later |
| Pen charging (MT5806) | ⬜ | new driver needed (P3) |
| CPU frequency scaling (stock tables), cpuidle | ✅ | |
| CPU thermal (stock 105/112/114 °C) | ✅ | held at 105 °C under load |
| Board + flash thermistors | ✅ | |
| **Skin + XO thermal zones** | 🟡 | patch in relay 009; skin limits to be replaced by stock gear values |
| GPU thermal cooling | 🟡 | maps present in the SoC DT; load test pending |
| Low-battery protection (BCL) | ⬜ | P0 |
| **Suspend (s2idle)** | 🟡 | worked with the WAKE# fix (0040) on queue ≤0040; **regression on 0045 + PipeWire: hard reset on the first cycle** (pc-026 S10), isolation in answer pc-026-s10 |
| Deep-sleep proof, 20/20 resumes, overnight drain ≤ ~1 %/h | ⬜ | |
| Wake sources (power key, lid, keyboard, charger) | 🟡 | RTC/power key seen; others to test |
| Power tuning (EAS, 60 Hz on battery, CDSP off) | ⬜ | Wi-Fi power save is in iceland-device |

## Other hardware
| Feature | Status | Notes |
|---|---|---|
| Rear flash LEDs | ✅ | |
| Sensors (accel, compass, ALS/proximity via SSC) | ⬜ | hexagonrpcd + libssc (P3) |
| **Cameras** (SC1320CS rear, SC820CS front) | ⬜ | plan written (PLAN 5-CAM); step C0 is relay 014 |
| Haptics | ❌ | the Pad 4 has none (disabled in stock) |
| Modem, NFC, fingerprint, IR | ❌ | not on this device |

## Software and packaging
| Feature | Status | Notes |
|---|---|---|
| `kernel-iceland` rpm + DTB kernel-install hook | ✅ | test-built (aarch64, 948 modules, DTB, kernel-install hooks + source rpm); install test on Fedora pending |
| `iceland-device` rpm (settings) | ✅ | built with rpmbuild; grows as the hardware lands |
| Full GNOME app set (Files, Software + Flathub, …) | ⬜ | RAM rehearsal is relay 008 |
| Fedora upgrades / kernel updates via dnf | 🟡 | policy in iceland-device; offline-update test pending |
| Automated fix loop on the PC | ✅ | relay 012 A policy |
| Stock-values audit (rule 13) | ⬜ | relay 013 |
| Upstreaming | ⬜ | only with the user's OK |
| Other distros (Arch ARM, pmOS, Debian, Kali, Ubuntu) | ⬜ | Phase 7, optional |
