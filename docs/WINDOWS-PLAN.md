# OnePlus Pad 4: plan for porting Windows on ARM (planning only)

> **Status 14 Oct 2026: planning only.** No Windows work is recorded in the sources for 10-14 Oct, and the sources show no
> W-phase result (unverified whether any was started earlier). The Linux install does not change the plan. What it adds
> for a later Windows attempt is the boot chain as installed: ABL starts `boot_b`, which is our footered U-Boot, and ABL's
> try counter applies to every slot that is not marked successful (see `INSTALL-PLAN.md`).


Written 2 Oct 2026, late evening. **Nothing in this plan has been done, and nothing in it writes to the tablet.**
Every tablet step is a RAM boot through `fastboot boot`, exactly like the Linux kits, and runs only after you have
connected the tablet and said go. The plan uses what the Linux project has proven (the hardware tables in
`docs/guide/02-HARDWARE.md`, the boot chain in `03-BOOT-AND-PARTITIONS.md`, the install and dual-boot plans, the
WORKLOG lessons) and what other projects have published for this chip and its relatives (checked on the web on
2 Oct 2026; links at the end).

## 0. The plan in ten lines

1. Windows needs three things the tablet does not have: a UEFI firmware that Windows can start from, ACPI tables
   that describe the hardware, and Windows drivers for the chip.
2. **The UEFI exists for our chip.** Mu-Silicium (the UEFI project behind most Windows-on-phone ports) supports
   Kaanapali and the OnePlus 15 since March 2026: display, storage, buttons and USB device mode work, and it boots
   Linux. The Pad 4 is the same chip and the same OnePlus firmware family, so a Pad 4 port is mostly a copy.
3. **The ACPI tables do not exist for our chip.** The OnePlus 15's entry says "Windows Boot: no", and its ACPI line
   is switched off in the build. No Snapdragon 8 Elite or 8 Elite Gen 5 device boots Windows today. Writing the
   tables is our work, and our device tree (every address, interrupt, rail and pin, proven on the tablet) is the
   source for them.
4. **The drivers are the wall.** Qualcomm's Windows drivers are closed and built per chip. No Windows driver set for
   SM8850 has been published. The nearest relative that has one is the Snapdragon X2 Elite ("Glymur", SC8480XP):
   same CPU core generation, same GPU generation, the same PMIC family, and Linux already shares several drivers
   between the two.
5. So the plan is staged, and every stage has a pass line and a stop rule: **W0** facts on the PC, **W1** the UEFI
   from RAM, **W2** Windows PE (the small installer Windows) to a prompt from RAM, **W3** Windows' own generic
   drivers, **W4** the X2 Elite driver experiments, **W5** an install (not planned now).
6. The test method stays the project's: a "Windows kit" image sent with `fastboot boot`, a log stream over the USB
   cable (the Windows kernel debugger takes the place of the kmsg stream), the webcam for the screen, a watchdog
   that returns the tablet to Android by itself, at most 10 minutes per run.
7. My estimate of the chances: UEFI on the screen about 85 %; Windows PE at a prompt about 50 %; Windows PE with the
   internal storage visible about 35 %; touch about 15 %; **a Windows you could use daily (graphics, Wi-Fi, sound,
   battery) under 5 %** until Qualcomm or Microsoft publish drivers for this chip. Section 9 explains the numbers.
8. If what you want is Windows *programs* on the tablet rather than Windows itself, section 10 has two routes
   that are far more likely to work.

## 1. What Windows needs, and what exists today

| Layer | What it is | State for the Pad 4 | Where it comes from |
|---|---|---|---|
| Boot firmware | A UEFI that Windows' boot manager can run on | **exists for the chip**, not for the tablet | Mu-Silicium `KaanapaliPkg` + `infinitiPkg` (OnePlus 15); a new `icelandPkg` for the Pad 4 |
| Firmware drivers inside the UEFI | Qualcomm's own UEFI drivers (storage, PMIC, pins, clocks, USB), taken as binaries from the tablet's stock `uefi` / `xbl` images | to be extracted from **your backup** (private, never committed) | `<pc-path>` |
| ACPI tables | Windows' description of the hardware (Linux uses the device tree instead) | **missing for the whole chip** | to be written from our device tree; the X2 Elite laptops' tables as the model |
| Windows build | The CPU cores are Oryon generation 3 | Windows 11 26H1 (build 28000) is the release made for these cores; older builds may refuse them | Microsoft's ARM64 media |
| Generic Windows drivers | Display on the firmware's picture, the interrupt controller, timers, CPU start (PSCI), UFS and USB by their standards | should work once ACPI describes them | in Windows |
| Chip drivers | Clocks and power (the "PEP"), pins, I2C / SPI, PMICs, GPU, sound, Wi-Fi, battery, sensors, cameras | **none published for SM8850** | section 7 |
| Board drivers | Touch and pen (Novatek NT36536, firmware loaded at every start), backlight, speakers' amplifiers, the keyboard cover | no Windows driver exists anywhere | would be ours to write, from our Linux drivers |

## 2. Reference devices

| Device / chip | Why it matters | State (Mu-Silicium status page, 2 Oct 2026) |
|---|---|---|
| OnePlus 15 "infiniti", SM8850 | Same chip, same vendor firmware. The template for our UEFI | UEFI: display, storage, buttons, USB device, mass storage yes; USB host and USB PD no; **Windows boot no**, Linux boot yes |
| OnePlus 15R, Snapdragon 8 Gen 5 | Sister chip | UEFI yes, Windows no, Linux no |
| OnePlus 13 / 13s / 13R, Xiaomi Pad 7 Pro, SM8750 (8 Elite) | The generation before; first phones with Oryon cores | UEFI yes, **Windows boot no** on all of them |
| Snapdragon 8 Gen 3 phones | The newest generation where Windows starts at all | "Only Windows PE boots": screen and CPU, nothing else |
| OnePlus 12R, Qualcomm QRD8550 (8 Gen 2) | The best Windows on a recent phone chip, because a Windows driver set for that chip got out | storage, battery, touch, Bluetooth; no GPU, Wi-Fi or sound on most |
| Snapdragon X2 Elite "Glymur" laptops, SC8480XP | The only relative of our chip with real Windows drivers. Linux already shares code between the two (our queue 0172 is a Glymur backport; the SPMI, DP, MDSS, pmic-glink and SoCCP drivers match both) | ships with Windows 11 26H1; drivers on Windows Update; the WOA-Project driver collection lists an `8480_CRD` set in its table (the folder was not there when I looked: to be checked) |
| Older ports: OnePlus 6 / 6T, Xiaomi Pad 5, Surface Duo | Show what a finished port looks like, and why: their phone chips were near-twins of laptop chips (SDM845 / SDM850, SM8150 / SC8180X) | usable Windows, built over years |

The lesson of the table: every usable port had a laptop twin with the same silicon. SM8850 and the X2 Elite are
relatives, not twins (different clock, pin and bus layouts), so the laptop drivers will not simply load.

## 3. What our Linux work gives this port

| We have (proven on the tablet) | Use for Windows |
|---|---|
| The device tree: every block's address, interrupts, clocks, rails, pins (`02-HARDWARE.md`, queue 0001-0174) | the source for the ACPI tables; no guessing |
| The boot chain facts: ABL's `fastboot boot`, 805 MB limit, header and device-tree rules (`qcom,msm-id = <0x295 0x20000>`, `qcom,board-id = <8 0>`), the 20-segment memory map with a zero-size segment, the boot header's OS version / patch level (17.0.0 / 2026-09) | the UEFI image is packed and started the same way as our U-Boot |
| ABL leaves the panel running: a 3392x2400 picture at 0xfc800000 | the UEFI's simple framebuffer, then Windows' basic display driver. The panel is landscape-native, so no rotation problem |
| 68 reserved-memory regions (hypervisor, TrustZone, DSPs, splash) | the UEFI memory map; a wrong map is the classic cause of early crashes |
| The CPUs start at EL1 under the Gunyah hypervisor | Windows runs, but without Hyper-V, WSL 2 or virtualisation-based security. Not a blocker |
| UFS: 6 LUNs, 4096-byte blocks, LUN order can change | Windows handles 4K-native disks; anything we build must find partitions by name |
| The never-write list and why (no public emergency-download loader; fastboot in ABL is the floor) | the same list applies; section 4 |
| Our U-Boot: RAM-booted daily, its own fastboot takes 2.5 GB, proven return-to-fastboot on errors | a second way to load a large Windows RAM disk (section 5, option B) |
| Firmware extraction, checked 23 of 23 against the backup | Windows chip drivers need the same signed firmware (ADSP, CDSP, GPU zap, Wi-Fi, Bluetooth, video) |
| The private touch, backlight, pen-charger, keyboard-cover and camera drivers | the only documentation of these parts' protocols; a Windows driver for any of them starts from ours |
| The charger runs on its own processor (SoCCP), started by the boot chain | the battery keeps charging by the firmware's own rules while Windows has no battery driver |
| The kit pipeline, runner whitelist, webcam rule, battery gate, "ask before every tablet action" | reused as they are |
| The freeze lesson (fast USB traffic while CPUs power-collapse hangs the chip, fixed with a latency hold), the TLMM lesson (reading secure-world pins resets the tablet), the regmap lesson | the same traps exist under Windows; ACPI must not expose the reserved pins, and USB debugging needs the CPUs kept out of deep idle |

## 4. Safety rules for the Windows work

All the owner's hard rules stay in force: RAM boot only; never flash, unlock, wipe, switch slots or install; you
alone run any write; ask before every tablet action; tests automated and at most 10 minutes; charging safety
first; private data (the backup, the firmware and the UEFI driver binaries taken from it) never committed.

Windows and a third-party UEFI bring hazards that Linux and our U-Boot did not have:

| Hazard | Why it is real | Rule in this plan |
|---|---|---|
| The UEFI's **mass-storage mode** | Mu-Silicium can show the whole UFS to the PC as USB disks. A Windows PC then mounts what it recognises and may write to it | removed from our build, like fastboot flashing in our U-Boot |
| UEFI writes to storage | Stock UEFI drivers can write blocks, erase, and call the storage **write-protect** and RPMB services (some of those are permanent) | W0 audit of every storage protocol in the build; our build marks every UFS LUN read-only at the UEFI level and leaves the write-protect, erase and RPMB drivers out; no capsule update |
| UEFI variables | Windows' boot manager writes boot variables | variables kept in RAM only (as in our U-Boot); checked in the source before the first boot |
| Windows mounting the firmware partitions | `modem` and `bluetooth` are FAT volumes; Windows would mount them and may write a "System Volume Information" folder | no UFS driver at all until W3; from W3 the image has automount off and the disk policy "offline, read-only" for every internal disk (Windows PE runs from RAM, so no internal disk is its boot disk) |
| Windows Setup | Setup repartitions | Setup is never run on the tablet. Only Windows PE from RAM in W1-W4 |
| No thermal or charge management in Windows PE | Without chip drivers Windows does not read temperatures or control charging | sessions of at most 10 minutes; start only between 40 and 80 % on the PC port; battery temperature read in Android before and after; the hardware trips and the charger firmware's own limits stay active; no CPU load tests |
| A hang with no way back | Windows will not pet the watchdog | a one-shot watchdog armed in our UEFI build ends every session by itself; Power held 15 s remains the manual way |
| Unsigned / altered drivers | W4 needs test-signing | only in the RAM image; nothing on the tablet changes |
| Secure-world pins | ACPI that lists pins in the device tree's `gpio-reserved-ranges` would let Windows touch them (run 30: instant reset) | the ACPI pin tables carry only pins Linux uses |

## 5. How a Windows RAM boot works

```
PC: fastboot boot winkit-N.img       -> ABL loads it into RAM (no write; the same command as every Linux kit)
    Mu-Silicium UEFI for the Pad 4      our build: no mass storage, UFS read-only, variables in RAM, watchdog armed
      RAM disk from the image's ramdisk part (FAT32: boot manager, boot configuration, boot.sdi, boot.wim)
    Windows boot manager -> winload     debugger over USB switched on in the boot configuration
    Windows PE (in RAM)                 startnet.cmd runs the test script, prints the summary on the screen
reboot / watchdog                     -> ABL -> Android (slot b), untouched
```

- **Option A (first choice):** one Android boot image, the UEFI as its kernel and the Windows PE disk as its
  ramdisk. ABL's limit is 805 MB; a Windows PE image is about 450-550 MB.
- **Option B (if A does not fit or ABL will not pass the ramdisk):** our U-Boot first (as today), which takes the
  large image over its own fastboot and starts the UEFI with the RAM disk's address.
- The PC side: `kd` (the Windows kernel debugger) on the USB cable for the log, the webcam for the screen, the
  existing runner with its whitelist (fastboot devices / getvar / boot / reboot only).

## 6. The phases

Each phase ends with a report and a go / stop decision. Tablet runs are RAM-only and need your go each time.

### W0 - facts, PC only (no tablet)

| # | Work | Result |
|---|---|---|
| W0.1 | Extract the UEFI driver set from the backup's `uefi_b` / `xbl_b`; compare it with the list the OnePlus 15 port uses (about 70 binaries: environment, TrustZone, pins, PMIC, UFS, clocks, SPMI, buttons, charger, USB, OnePlus project / extra-GPIO drivers) | which drivers match by name, which are Pad 4 only |
| W0.2 | The stock UEFI's memory and configuration map against ABL's 20 segments and our 68 reserved regions | `MemoryMapLib` and `ConfigurationMapLib` for the Pad 4 |
| W0.3 | Read the open ABL source (already in `wf/install/work/abl`) for how `fastboot boot` hands over the ramdisk and device tree to a non-Linux payload | option A or B |
| W0.4 | **Write-path audit** of Mu-Silicium and of each stock storage / charger driver in the list | the exact list of what our build leaves out; proof that the build cannot write UFS or store variables |
| W0.5 | Get the X2 Elite Windows driver set from Windows Update and one X2 Elite ACPI dump; map each device in it to our device tree | a table: block, Windows hardware ID, same register layout as ours or not |
| W0.6 | Which Windows build accepts the cores (28000 expected); what Mu-Silicium's kernel patch library does at start | the Windows PE version to build |
| W0.7 | With your OK only: ask the Mu-Silicium maintainers what stops Windows on the OnePlus 15 beyond the missing ACPI | fewer unknowns for W2 |

Stop rule: if W0.4 cannot prove a build that never writes, nothing boots on the tablet.

### W1 - the UEFI from RAM

Work: `icelandPkg` from `infinitiPkg` (the chip variant SM8850P, the 3392x2400 framebuffer, the memory map, our
device tree, the boot header values of today's `boot_b`), with the W0.4 removals, the read-only UFS layer and the
session watchdog. Runs (each under 5 minutes):

| Run | Pass |
|---|---|
| U1 | the UEFI's screen appears (webcam); the tablet returns to Android by the watchdog alone |
| U2 | a start-up script lists the disks, the memory map and the tables on the screen; UFS shows 6 read-only LUNs with `userdata` found by name |
| U3 | a write attempt from the UEFI shell to a UFS partition is refused; Android boots afterwards with every partition's checksum-relevant state unchanged (the slot flags and `misc` read before and after, as Part A of the install guide does) |

### W2 - Windows PE to a prompt

Work: the minimal ACPI set from our device tree (CPU and cache topology, the interrupt controller, timers, PSCI,
the USB debug port, the firmware picture), a Windows PE 28000 image with debugging and test-signing on, the
script that prints one summary line. Runs: boot, read the debugger log, judge.

What each failure would mean:

| Seen | Meaning | Next |
|---|---|---|
| The boot manager shows an error screen | the RAM disk or the boot configuration | PC-side fix |
| The debugger never connects, logo stays | the USB debug port description, or a crash before the debugger starts | the firmware-level boot debugger; compare with the OnePlus 15 |
| Stop code for the processor or the hardware layer | cores not accepted by this build, or interrupt controller / timer / PSCI tables wrong | another build; fix tables against the device tree |
| Stop code for ACPI | a table error | fix |
| A prompt on the screen | **W2 passed** | W3 |

Stop rule: three weeks of runs without reaching the kernel debugger, and no hint from the OnePlus 15 side, parks
the Windows work until someone publishes a Windows boot on SM8750 / SM8850.

### W3 - Windows' own drivers

In order: UFS by the standard driver (offline, read-only: a disk list on the screen is the pass), the real-time
clock, the buttons, USB host by the standard xHCI driver (needs you to plug in a keyboard: deferred to you),
processor idle states. No chip drivers yet. This is the level the Snapdragon 8 Gen 3 phones have reached.

### W4 - the X2 Elite drivers (research, hard stop rules)

One driver per kit, in dependency order, each with the question "does it load, and does it touch the right
registers": power and clocks, TrustZone and shared memory, pins, SPMI and PMICs, I2C / SPI, then battery, the DSPs,
GPU, Wi-Fi, sound. For each one the ACPI entry is written to look like the laptop's where our hardware matches,
and the driver is watched in the debugger. A driver that writes to an address that is something else on our chip
is dropped at once. Board drivers of our own (touch first, from our Linux driver) only make sense once pins and
SPI work.

Stop rule: if the power / clock driver cannot be made to run on our chip, everything after it in the list is
closed, and the port stays at W3 until a Windows driver set for SM8850 appears.

### W5 - an install (not planned)

Only if W4 produced a Windows worth keeping, and only as your decision. It would follow `DUALBOOT-PLAN.md`: a
partition of its own carved from `userdata`, the UEFI in `recovery_b`, the same rehearsal-then-write discipline
and the same never-write list. Windows next to Fedora and Android on one `userdata` is a three-way split to plan
then, not now.

## 7. Driver outlook per hardware block

| Block | Linux today | Windows route | Outlook |
|---|---|---|---|
| CPU start, interrupts, timers | proven | generic, from ACPI | good |
| Display (firmware picture, no acceleration, fixed brightness and 60 Hz) | proven with full driver | basic display driver | good |
| UFS | proven | standard driver if the firmware leaves clocks and PHY on | fair |
| USB device (debug link) | proven | kernel debugger's own USB support | fair |
| USB host | by design, untested with accessories | standard xHCI if the UEFI leaves the port in host mode (the OnePlus 15 UEFI cannot yet) | poor for now |
| Clocks, power domains, RPMh | proven | X2 Elite's PEP driver: built for another clock layout | poor |
| Pins, I2C, SPI, SPMI, PMICs | proven | X2 Elite's; the PMIC family is the same, the pin controller is not | poor to fair |
| Battery and charging display | proven (SoCCP, OnePlus variant) | X2 Elite's battery driver speaks to an embedded controller, not to our charger firmware | poor; charging itself continues in firmware |
| GPU (Adreno 840) | proven (Mesa) | X2 Elite's GPU driver is for the X2-85 / X2-90 and checks the chip | very poor |
| Wi-Fi / Bluetooth (WCN7860) | proven | needs the PCIe driver first, then a FastConnect driver that knows this chip (to be checked) | very poor |
| Sound (6 x TFA9865 on TDM, WCD9395) | proven | Qualcomm's audio stack plus amplifier drivers that do not exist for Windows | none |
| Touch and pen (NT36536) | proven, private driver | our own Windows driver, after pins and SPI | poor |
| Sensors, cameras, video, NPU | proven on Linux | chip stacks that do not exist for SM8850 on Windows | none |
| Keyboard cover, pen charger | queued, need your test | our own drivers, last | none for now |

## 8. Test method

- A kit generator beside `genwf.py` builds `winkit-N.img` (UEFI + RAM disk) and records its sha256; the chain
  script is the Linux one with the debugger capture in place of the ssh probe.
- Pass / fail comes from one summary line in the debugger log and, where the debugger is not up yet, from the
  webcam (frames stay in the scratchpad and are deleted after the verdict, as the webcam rule says).
- Every run: battery gate, temperature before and after in Android, slot flags and `misc` before and after.
- Log every run in `WORKLOG.md`; a "Windows" group in the feature matrix only once W1 passes.

## 9. Chances and why

| Goal | My estimate | Reason |
|---|---|---|
| UEFI on the Pad 4's screen from RAM | about 85 % | done on the OnePlus 15 with the same chip and vendor; our boot-chain knowledge covers the differences |
| Windows PE at a prompt | about 50 % | the known blocker (no ACPI) is work we can do; but nobody has shown Windows starting on Oryon phone chips, so an unknown blocker is likely |
| Windows PE with the internal storage listed | about 35 % | standard driver, depends on what the firmware leaves running |
| Touch working | about 15 % | needs the pin and SPI drivers of another chip to work, then our own driver |
| A usable Windows (graphics, Wi-Fi, sound, battery) | under 5 % | needs Qualcomm's closed drivers for a chip they have not released for Windows |

Time: W0 about a week of PC work; W1 one to two weeks; W2 two to four weeks; W3 and W4 open-ended.

## 10. If the goal is Windows programs, not Windows itself

| Route | What it is | Outlook |
|---|---|---|
| Wine with an x86 translator (FEX or Box64) on our Fedora | Windows programs run on Linux; our Vulkan driver (turnip 1.4, proven) carries DirectX through DXVK | good: no new kernel work, a package and test job on the existing kits |
| Windows as a guest under the Gunyah hypervisor | The tablet's firmware has a virtual-machine layer (the `pvmfw` partition exists). Windows 11 ARM in a virtual machine needs no Qualcomm Windows drivers | research: Linux has no merged Gunyah driver yet (hwinv row A24) and the virtual-machine tools for it are young |
| A Windows PC streamed to the tablet | Remote desktop over Wi-Fi | works today |

## 11. Decisions that are yours

1. Go ahead with W0 (PC only) now, or after the Fedora install work (R1, C0) is finished. The tablet time and the
   main session are shared, so W1 onwards competes with the install rehearsal.
2. Whether I may ask the Mu-Silicium maintainers about the OnePlus 15's Windows state (W0.7). Nothing is sent
   anywhere without your OK.
3. Whether the Windows work gets its own private repository (the UEFI package, the ACPI source, the kit tools;
   never the binaries from your backup).
4. Whether section 10's first route (Wine on Fedora) should become a workflow of its own. It is the fastest way
   to a Windows program running on this tablet.

## 12. Workflows to start (all PC only)

| Workflow | Delivers |
|---|---|
| `winuefi` | W0.1-W0.4: the driver comparison, the maps, the write-path audit, a build recipe for `icelandPkg` |
| `winacpi` | W0.5 and the W2 tables: a generator that writes the ACPI source from our device tree, with the X2 Elite mapping table |
| `winkit` | W0.3, W0.6: the Windows PE image recipe, the kit generator, the debugger capture, the runner changes |

The main session reviews each delivery against section 4 before any image goes near the tablet.

## Sources (checked 2 Oct 2026)

- Mu-Silicium status page and releases (Kaanapali and OnePlus 15 support, Windows boot state per device):
  https://github.com/Project-Silicium/Mu-Silicium/blob/main/Status.md ,
  https://github.com/Project-Silicium/Mu-Silicium/releases
- Mu-Silicium's OnePlus 15 package (driver list, ACPI line switched off):
  https://github.com/Project-Silicium/Mu-Silicium/tree/main/Platforms/OnePlus/infinitiPkg
- Mu-Silicium's ACPI tables (none for Kaanapali, Pakala or Lanai): https://github.com/Project-Silicium/Silicium-ACPI
- Porting and Windows PE guides: https://github.com/Project-Silicium/Guides
- Qualcomm reference Windows drivers collected from Windows Update (the X2 Elite row):
  https://github.com/WOA-Project/Qualcomm-Reference-Drivers
- Windows 11 26H1 (build 28000) as the Snapdragon X2 platform release:
  https://4sysops.com/archives/windows-11-26h1-release-date-no-new-features-bromine-platform-changes-only-for-snapdragon-x2-and-nvidia-n1x/
- Adreno generation 8 shared by the X2 Elite and the 8 Elite Gen 5:
  https://www.phoronix.com/news/Freedreno-Lands-Adreno-Gen-8
- Project notes on the other SM8850 trees: `docs/repo-docs/000-pc-knowledge.md`
