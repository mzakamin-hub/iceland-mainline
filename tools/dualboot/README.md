# Dual boot tools (not used)

The owner's decision (13 Oct 2026) is Fedora only, so these tools are not used; the plan is
[../../docs/DUALBOOT-PLAN.md](../../docs/DUALBOOT-PLAN.md). The tool below is kept for that plan.

- `reflash-recovery.ps1`: writes U-Boot into the current slot's `recovery_<slot>` partition. It would be used only for
  dual boot, and after every Android OTA (an OTA switches slots). It writes only `recovery_a` or `recovery_b`, never
  switches slots, checks the sha256 and the Android header, and needs a typed confirmation. Rollback: write the saved
  stock recovery image the same way.

The installed system does not use this tool.
