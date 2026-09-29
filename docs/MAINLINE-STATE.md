# Mainline (cloud debugger) state, 2026-09-29 ~19:10 (saved before a context compaction)

**Role:** a dedicated cloud debugger for the PC (relay 017). Watch both repos with `tools/mainline/watch-pc.sh`
(background; re-arm after each wake), answer every PC push in `relay/answers/<name>.md` (candidate patches
compile-checked on queue 0045+ in `/home/user/k45`, output in `/home/user/k45-out`), keep FEATURES/TODO and the
published matrix (https://claude.ai/artifact/GtN6zLRTeabVcyg3LirNBm, source `docs/features/`) current. Commits: author
mzak, signed (check `git cat-file -p HEAD | grep gpgsig` after any rebase; re-amend if missing), with the Claude
trailers. GitHub had 503 spells: retry with backoff.

**User rules:** rule 13 (Pad 4 stock values only, OxygenOS 11.A.38 / the user's LineageOS trees); no tablet writes; the
Wi-Fi region is **US** (the user's choice, EG dropped); Boot & platform only after the user confirms the install; fast
charging out of scope; charge only while watched until the Power area is done.

**Campaign (relay 019, the user's order):** ✅ Audio (closed) → **Display & input (the pink/blocky glitches, the screen)**
→ Graphics & compute (GPU, NPU) → Power & charging → Thermal → Sleep → Connectivity → Sensors & camera → Software →
(last) Boot & platform.

**Queue (iceland-linux):** 0001-0052. 0046-0050 the speakers (verified identical + the tree hash reproduced),
0051 the volume cap, 0052 the wcd939x TLV.

**Open candidates waiting for a tablet test (all in relay/answers):**
- `area-audio-5/0001-0002`: stock tfa reg 0x62 + TDM pin drive (a side check in the next kit, then 0053/0054).
- `timer-sm8850/0001-0002`: the rpmh-rsc past-wakeup clamp + the always-on arch timer (the Sleep area).
- `pc-026-s10-crashlog/`: ramoops DT + the rsc debug patch; `iceland-linux configs/debug-hang.config`.
- relay 015: the battmgr stock charger inputs + charge_behaviour + constant_charge_current_max, the usb-therm zone;
  relay 009: the skin/XO zones (stock gear caps still needed) → the Power/Thermal areas.
- iceland-device 0.7 (packaging/iceland-device): the battery guard, the UCM + topology, Wi-Fi region, refresh, NPU off.

**Known issues / hypotheses:** the mic hiss (−47 dBFS; packing and identity mapping ruled out; next: the downstream
WCD939x per-rate TX port params); the post-resume stall + unexplained resets (Sleep area); the battery estimate
(the current flips sign, no CHARGE_NOW → Power area); the pink glitches (UBWC 6.0/HBB vs stock `sde-highest-bank-bit
<8 3 7 2>`, relay 011 + answer 011-prep).
