# Dual boot tools (PLAN v4 Phase 4-DB)

Only for use **after the user has approved dual boot**. Everything else in this repo is RAM-boot only.

- `reflash-recovery.ps1`: put U-Boot into the current slot's `recovery_<slot>`. Use it when setting up dual boot,
  and after every Android OTA (an OTA switches slots). It writes only `recovery_a`/`recovery_b`, never switches
  slots, checks the sha256 and the Android header, and needs a typed `FLASH recovery_<slot>`. Rollback: flash the
  saved stock recovery image the same way.
