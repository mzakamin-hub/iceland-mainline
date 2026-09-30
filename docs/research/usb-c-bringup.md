# USB-C bring-up plan: host / OTG / PD, accessories, DisplayPort (OnePlus Pad 4)

Status 2026-09-30: prepared offline (the user's request: "prep ... usb host/otg/pd, usb accessories (headsets,
keyboards,etc) and display port usb-c"). Rule 13 applies: board values from Pad 4 stock only.

## 1. What the queue already has

| Piece | State in the queue (0001-0061) |
|---|---|
| Type-C port manager | `pmic-glink` (`oneplus,iceland-pmic-glink`, Kaanapali data = battery + **alt mode** + **UCSI** clients), `usb-c-connector` with `power-role = "dual"`, `data-role = "dual"`, orientation GPIO 60 |
| Data role | dwc3 `usb@a600000` with `usb-role-switch` (UCSI drives host/device); HS endpoint → dwc3, eUSB2 repeater with stock's tuning |
| SuperSpeed + DP lanes | Kaanapali USB3+DP combo PHY (queue 0087/0088), connector SS endpoint → `usb_dp_qmpphy_out` |
| SBU / analog audio | WCD9395 USB-SS mux (`qcom,wcd9395-usbss`, mode + orientation switch, 0085) on the connector's SBU endpoint; WCD939x Type-C mode changes (0114) |
| DisplayPort controller | Kaanapali DP (0105-0108), `mdss_dp0` in kaanapali.dtsi — **disabled on the Pad 4** (the OnePlus 15 DTS enables it) |
| Kernel config | TYPEC, TYPEC_UCSI, UCSI_PMIC_GLINK, QCOM_PMIC_GLINK, USB_ROLE_SWITCH, DWC3 dual-role, xHCI, PHY_QCOM_QMP_COMBO, DRM_MSM_DP, DRM_AUX_HPD_BRIDGE, TYPEC_MUX_WCD939X_USBSS (y); TYPEC_DP_ALTMODE, USB_HID, HID_GENERIC, SND_USB_AUDIO, USB Ethernet (r8152, ax88179, cdc_ether), USB_SERIAL (m); USB_STORAGE (y); **USB_UAS not set** |

## 2. What stock says (read locally from the private stock DTs, not committed)

- Stock enables the DP controller on this SoC (`qcom,dp_display@9ad2000`): pixel clock up to **675 MHz**, HBR2/HBR3
  tables (so up to **8.1 Gbps/lane**), DSC, FEC and widebus on, an AUX switch (the USB-SS mux).
- The Pad 4 overlay (all iceland variants) **retunes the DP PHY for HBR/RBR**: its own voltage-swing and
  pre-emphasis 4×4 tables (they differ from the SoC base in two entries). Mainline's combo PHY takes its tables from
  the driver (per PHY version), so the Pad 4 values need a board-level override or a check that the driver's
  Kaanapali tables match.

## 3. Gaps and the prepared changes

1. **Kit: accessories can't autoload.** The RAM rootfs carries only the kit's 38-module subset for the running
   kernel, so udev can't load `usbhid`/`hid-generic` (keyboards, mice), `snd-usb-audio` (USB headsets),
   `typec_displayport`, USB Ethernet or serial drivers (the Wi-Fi run area-wifi-1 hit the same wall with modprobe).
   Prepared: `build/mk-modfull.sh` packs the full stripped module tree (q28: 949 modules, 12.5 MB); a probe unpacks it
   into `/lib/modules/<kver>`, runs `depmod` and replays udev (`udevadm trigger --action=add`). The installed system
   ships all modules anyway; this is only the RAM kit.
2. **DP enable (DT candidate):** `&mdss_dp0 { status = "okay"; }` and `&mdss_dp0_out` with
   `link-frequencies = /bits/ 64 <1620000000 2700000000 5400000000 8100000000>` (stock's HBR3 tables), then compare
   the combo PHY's Kaanapali swing / pre-emphasis tables with stock's Pad 4 HBR/RBR override.
3. **UAS** for fast USB storage: `CONFIG_USB_UAS=m` (Fedora's own kernel has it).

## 4. Tests

**A. Automated, no user (the PC's USB port is the partner in every kit run):** full modules + depmod + udev replay
(what autoloads); `/sys/class/typec/port0` (roles, `port_type`, orientation, PD revision), the partner and the PC's
source capabilities (`/sys/class/usb_power_delivery`), the UCSI power supply, the DP connector appearing as `DP-1`
(disconnected) with the DT candidate, the port's alt modes (DP SVID 0xff01), the WCD USB-SS mux bound. Faults: 0.

**B. With the user (deferred; one session, 10 min):** host mode needs the port, and the kit's control link is that
same port, so a script on the tablet logs to RAM while the PC cable is out and the probe fetches the log when the
PC is plugged back. In order: a USB keyboard and mouse (HID), a USB stick (storage), a USB-C digital headset
(snd-usb-audio: playback + mic), a USB-C to 3.5 mm adapter (analog audio accessory mode through the WCD USB-SS mux and
the WCD939x headset detection), a hub with a PD charger passing power through (sink while host), a USB Ethernet
adapter, and a DP monitor or dock (alt mode: 4 lanes, or 2 lanes + USB3 behind a dock; resolution and refresh read
back). Each item is judged from the logs (enumeration, the driver bound, audio levels, DRM modes); the user only
plugs.

**C. PD (with the charger tests, power.md T2-T6):** the PD contract as a sink (9 V, never 12 V) and as a source
(OTG VBUS to a device), both through UCSI's power supplies.
