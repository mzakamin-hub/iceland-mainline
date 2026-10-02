# Index: where to find what

The documentation set (this folder: WSL `~/mainline/build/wf/docs/`; drafts until the main session commits them):

| File | Content |
|---|---|
| `PLAN.md` | the plan of this document set (audiences, outlines, sources) |
| `01-OVERVIEW.md` | the project, what works (matrix numbers, battery life), what does not, the safety principles |
| `02-HARDWARE.md` | SoC and board block by block with driver source and proof; PMICs, rails, thermal design; RAM / UFS; the partition layout; firmware sources; `efisp`; built-in vs modules |
| `03-BOOT-AND-PARTITIONS.md` | stock boot chain, A/B, AVB; the RAM boot; the planned install chain; the rehearsal; unbrickable / restorable |
| `04-BUILD-YOUR-OWN.md` | step-by-step: trees, `prepare.sh`, config, build, U-Boot, firmware (read-only), a RAM-boot image, logs |
| `05-PORTING-TO-OTHER-DISTROS.md` | Debian in detail, Arch and postmarketOS-style in brief, what is Fedora-specific |
| `06-PROCESS-HISTORY.md` | timeline, method, key findings, lessons, evidence map |
| `07-INSTALL-REVIEW.md` | independent review of the install: findings, consistency, recovery gaps, questions |
| `GLOSSARY.md` | terms |
| `RESUME-2026-10-02.md` | one page for a fresh session: state, agents, next actions, owner decisions and tests |

The main session committed the drafts of 2 Oct evening to `iceland-mainline/docs/guide/` (commit u, 1c417e9). This
folder stays the source; later updates are committed from here.

## Project folder `C:\Users\lucne\OnePlusPad4-Mainline` (snapshot + the log)

| Path | Content |
|---|---|
| `HANDOVER.md`, `STATE.md`, `CLAUDE.md` | how to resume, the rules, where things live |
| `WORKLOG.md` | the running history (entries 1-44+) |
| `docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md` | the install plan and the step-by-step guide (copies in iceland-mainline `docs/`) |
| `docs/BOOT-LOG-PLAN.md` | boot-log error inventory and plan (2 Oct; P1-a corrected: the battery does not need the ADSP) |
| `docs/INSTALL-RERUN-COMMANDS.md` | the install agent's verified next commands (copy the scripts, P1 + TIN, notgzip test, B run, R1, Part A read) and the open GPU-firmware decision |
| `docs/WORKFLOW-BRIEF*.md` | the workflow briefs |
| `docs/memory/` | the session memory notes (resume points, rules); the serial is masked |
| `docs/results/`, `docs/repo-docs/` | older results files and copies of repo docs |
| `kernel/queue/` | a copy of iceland-linux (may lag) |
| `scripts/` | copies of the chain, kit, build, commit and matrix scripts |
| `workflows/` | public parts of the workflow folders |

## WSL `~/mainline`

| Path | Content |
|---|---|
| `gh/iceland-linux/` | kernel queue: `kernel.pin`, `patches/0001-infiniti` (138), `patches/0002-iceland` (0001-0174), `configs/` (`distro-neutral.config`, `required.config`, `debug-hang.config`), `scripts/prepare.sh`, `scripts/build.sh`, `packaging/fedora/` (kernel-iceland spec + DT plug-in), `packaging/repo/make-repo.sh`, `docs/PORT-LOG.md`, `debug-patches/` |
| `gh/iceland-mainline/` | `README.md`, `PROJECT.md`, `CHANGELOG.md`; `docs/` (`PLAN.md` v4 incl. Phase 4-DB dual boot, `KNOWLEDGE.md`, `FEATURES.md`, `features/` matrix source, `reference/pad4-hardware-boot-partitions.md`, `device-facts/`, `research/`, `sensors/patches/`, `tests/` log sets, INSTALL-PLAN / GUIDE, WORKLOG copy); `packaging/iceland-device/`, `packaging/sensors/`; `audio/` (UCM, topology); `firmware/` (manifest: names only, `convert-nt36536.py`); `tools/linux-ram/` (kit builder, shim `init`, `run-linux.ps1`, `fw-extract.sh`), `tools/dualboot/`, `tools/capture/`, `tools/relay/`; `phase4/` (Fedora rootfs in RAM); `relay/` (relay-era requests and results) |
| `gh/iceland-u-boot/` | `uboot.pin`, `patches/0001-infiniti` (14), `patches/0002-iceland` (3), `scripts/prepare.sh` + `build.sh`, `tools/diag/` (diag environments A-L, `build-diag.sh`) |
| `build/` | the working area: `src/` (kernel git, branch `iceland` = queue head), `out/`, `bin<tag>/` + `modstage<tag>/` test kernels, `build-q2.sh`, `build-q56.sh`, `queue-00NN.sh`, `make-kit26.sh`, `prep-area-combo-N.sh`, `gen-combo-N.py`, `an/` (tablet scripts, probes, `genwf.py`, `chk.sh`, `kmsg-errors.py`), `area-combo-N/` log sets, `wf/` (workflows) |
| `build/wf/<name>/` | each workflow: `REPORT.md`, `NEXT.md`, `tablet.sh`, `cand/` (public candidates), `priv/` and `work/` (private / scratch) |
| `build/wf/install/` | the install tooling: `cand/kernel-iceland/`, `cand/iceland-device/` (0.18 fragment), `cand/fwx/` (firmware extractor), `cand/image/` (fetch, `mk-golden.py`, `mk-sparse.py`), `cand/rehearsal/` (NBD server, relay, head, `rehearse.ps1`, `accept.sh`, `iceland-rescue`), `cand/u-boot/` (patches 0004-0006, `mk-uboot.sh`, `check-header.py`, sandbox check), `selfcheck.sh`, `next-k2p1u1.sh`, `genwf-install-b.py` |
| `build/wf/install/HANDOVER-ROUND6.md` | the install workflow's round-6 record: state per review item, AVB proof, C0 design, the dual-boot plan brief, current file hashes |
| `build/wf/r1debug/REPORT.md` | R1's root cause, the fix verified 15 / 15 in a U-Boot sandbox, the notgzip test head |
| `build/wf/bootfix/`, `build/wf/bypass/` | the hwfix workflow: device-tree gaps (topic B, queued 0167-0174), the PCIe L2 diagnosis (topic A, run 97), bypass charging (topic C) |
| `build/wf/hwinv/INVENTORY.md` | 112 hardware blocks, stock vs mainline |
| `build/wf/audit/REPORT.md`, `AUDIT-TABLE.md` | the stock-values audit (the full table is private) |
| `research/matrix-*.py` | feature-matrix update scripts |

## Windows

| Path | Content |
|---|---|
| `C:\platform-tools\` | adb / fastboot, the staged kits, the runner `relay-run-kit-early.ps1`, `usb-proxy.py`, `rootfs-serve\`, live kmsg streams |
| `C:\OnePlusPad4\` | **private**: the 151-partition backup, the stock 11.A.38 images, the owner's scripts (backup, unlock, LineageOS, return to stock: `30-`, `31-`, `39-`), captures |

## Quick answers

| Question | Look at |
|---|---|
| Does feature X work, and how was it proven? | `iceland-mainline/docs/FEATURES.md` (row notes name the run) |
| Which patch does Y? | `ls iceland-linux/patches/0002-iceland/`; the WORKLOG entry that queued it |
| What did run N show? | `~/mainline/build/area-combo-N/` and the WORKLOG entry naming run N |
| What is stock's value for Z? | `wf/audit/AUDIT-TABLE.md`, `docs/device-facts/`, `docs/reference/pad4-hardware-boot-partitions.md` |
| Which partitions may be written? | `docs/INSTALL-PLAN.md` section 2; `02-HARDWARE.md` section 6 |
| How do I get back to stock? | `docs/INSTALL-GUIDE.md` section 8; `C:\OnePlusPad4\scripts\39-Return-To-Stock.ps1` (written and dry-run, never executed) |
