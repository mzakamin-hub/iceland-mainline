# Iceland team plan - from the r2g logs to a complete, proven, committed build (started Sat 3 Oct 2026 03:00)

> **Status 14 Oct 2026.** This team plan (3 Oct) is history. The round it organised ended with the loop 5 work
> (9-13 Oct), the golden build B149, and the install on 13 Oct. The loop 5 folders and the agent ledger are not in the
> repository. The roles and gates below no longer run.


Owner's order (3 Oct about 03:00): "use a whole team of agents using opus and fable ... an automated process with no
intervention from my side to reach a complete working build with everything. Project should be completed by a timeline
and fixes and error collection should be consolidated to avoid multiple re-iterations and repetitive actions."
Actions: testing (live testing, log collection, error collection, dmesg), debugging, fixing, building, documenting,
committing once proven working - and not limited to those.

"Complete working build" = kernel q84 (+ queue 0175..), kernel-iceland K2 / K3, iceland-device P1, the tablet inputs
(TIN), proven on the tablet in the kits and in the install rehearsal R2-final with every acceptance and debugger check
green (or a written benign verdict), committed to the private repos with docs and the feature matrix. The install
itself (any write to the tablet) stays the owner's, with the owner's decisions listed at the end.

## 1. The team
| role | who (model) | does | writes only in |
|---|---|---|---|
| orchestrator + tablet runner + committer | main session (Opus) | timeline, gates, merges the ledger, every tablet session (kits, B runs, rehearsals), queue push, commits | everywhere it must |
| ledger keeper | ledger (Opus) | one error ledger for every run: ingest, normalise, dedupe, map to F-ids, status board, run diffs | wf/ledger/ (tool proposed for an/) |
| debugger + live tester | debugger (Fable; replaced the stopped fedtest agent, works in wf/fedtest/) | root causes from logs and cores, verifies every finding and fix against the logs, runs the suite inside tablet sessions (only between SESSION UP / DOWN from main) | wf/fedtest/ |
| reviewer | review (Opus) | independent review of every fix candidate, build script and commit diff: correctness, rule 13 sources, charging safety, privacy, style | wf/review/ |
| builder | builder (Opus) | turns G1-passed candidates into one consolidated build: kernel q84, K2 / K3, P1, TIN, kit generators, manifests | wf/builder/ + the build outputs it is told to make |
| fixer: image + rehearsal tooling | install (Fable) | F3 F7 F8 F10 F13 F14 + image side of others; P1 / TIN recipes | wf/install/ |
| fixer: cameras | camfix (Opus; restarted on the owner's choice) | F2 F5 F6 (+ the F1 fix if it lands in camera code) | wf/camfix/ |
| fixer: kernel / DT | klog (Opus; restarted on the owner's choice) | F11 F12 F15-F22 | wf/klog/ |
| charging-safety guardian | chgsafe (existing) | chgsafe v2 facts for the builder, kit 106 generator + pass criteria, safety verdicts on every power-touching record | wf/chgsafe/ |
| power + sleep owner | sleeppower (existing) | power view of F16, the sleep proof of q84 in kit 106 (rehearsals cannot suspend), power verdicts | wf/sleeppower/ |
| rehearsal / boot-chain debugger | r1debug (existing) | verdicts on the install agent's rehearsal fixes, pre-boot head checker, post-session end classifier | wf/r1debug/ |
| documenter | docs (existing) | guides, release notes, matrix script, commit scripts (prepared, not run) | wf/docs/ |

Agents never: flash / erase / format / set_active / -w / unlock; act on the tablet outside a session given by main;
commit or push; touch another agent's folder; wsl --shutdown; pkill -f their own pattern; copy private data out.

## 2. One ledger, one fix record per finding (no repeated work)
- The ledger: wf/ledger/ledger.py (adopted as an/ledger.py) keeps an/ledger/errors.json + an/ledger/LEDGER.md.
  Every run (kit, B run, rehearsal) is ingested once: kmsg stream, journal, dmesg, acceptance results, debugger suite.
  Lines are normalised to signatures; each signature has first / last seen, runs, count, F-id or NEW, benign flag.
- Every finding has exactly one F-id (F1-F23 from an/r2g-logs/FIX-LIST.md; new ones get the next number from the
  ledger keeper). Before anyone works on a log line, they look it up in the ledger.
- Fix record (the only way a fix enters a build): wf/<agent>/fixes/F<nn>.json
  {"id","title","owner","kind": kernel-patch|kernel-config|dt|image|tooling|userspace|benign,
   "root_cause","evidence": [bundle file: line text], "stock_source", "change": {patcher / config / image files},
   "signatures_gone": [regex], "signatures_expected": [regex], "test", "risk", "status": "candidate"}
- Verdicts: wf/fedtest/verdicts/F<nn>.json and wf/review/verdicts/F<nn>.json
  {"id","verdict": confirmed|rejected|needs-data,"notes"}.

## 3. Gates (status in the ledger board)
- G0 found: in the ledger with an F-id and an owner.
- G1 ready: fix record + debugger "confirmed" + reviewer "confirmed" (benign items: both confirm the evidence);
  plus chgsafe "confirmed" for anything touching power / regulators / charger / thermal, sleeppower for anything
  with a power or wake effect, r1debug for rehearsal-tooling records (verdicts in wf/<agent>/verdicts/).
- G2 built: in a build manifest (wf/builder/manifest-<tag>.json).
- G3 proven: the tablet run shows signatures_gone gone, signatures_expected present, the test passing, no new
  signature caused by it (ledger diff against r2g).
- G4 committed: queued / committed and pushed, docs and matrix updated.

## 4. One consolidated loop (not one loop per bug)
- Candidate freeze at 05:00: what is G1 by 05:30 goes into build 1; late items wait for loop 2 (only if needed).
- One build, one consolidated kit, one B run, one rehearsal per loop; the ledger diff decides what is proven.
- Loop 2 only for what loop 1 did not prove; a regression is rolled back, not patched on top.

## 5. Timeline (Sat 3 Oct)
| time | milestone |
|---|---|
| 03:00-03:30 | team up; ledger tool started; r2g logs ingested as the baseline (with r2f / r2 / r1d for history) |
| 05:00 | candidate freeze: every F has a fix record or a benign record |
| 05:30 | G1: debugger + reviewer verdicts on every record |
| 06:30 | builder: q84 kernel (+ binq84/config saved first), compile-clean; build manifest |
| 07:00 | K2 / K3 from q84, P1 + TIN with all image fixes |
| 07:00-08:00 | tablet: consolidated kit 106 (chgsafe v2 + the kernel-fix checks), B run 107 (26 / 0) |
| 08:00-09:00 | tablet: R2-final r2h (MAX 1500, guard fixed) + acceptance + debugger suite; ledger diff vs r2g |
| 09:00-10:00 | G3 review; queue 0175.. (DRY then real), commit x, docs, matrix, snapshot -> "build complete" |
| 10:00-13:00 | reserve: loop 2 only if something was not proven; hard target 13:00 |

## 6. Owner involvement
None planned. The tablet stays connected to the PC; every session starts with a fast presence + battery gate
(fastboot / adb device present, battery over the kit gate). If it fails, the pipeline pauses and notifies the owner
(no chain left waiting on adb). Things only the owner can check stay deferred and are listed in the final report
(overnight drain, chargers, pen, DP, USB accessories, pogo). The install writes and decisions 1 / 2, boot_b vs
recovery_b, dual boot, the way back to LineageOS stay the owner's.
