# Dual boot helper (untested, not part of the install)

The documented install is Fedora only (`docs/INSTALL-GUIDE.md`): it replaces Android's data, and Android no longer
starts. A dual boot (Android next to Fedora) would need a `fedora` partition carved from `userdata`, which means a change
of the partition table of unit sda; the install never writes a partition table. U-Boot's install build already prefers a
partition named `fedora` over `userdata`, so such a layout is possible later, but it is not designed in detail and has
not been tried.

- `reflash-recovery.ps1`: writes U-Boot into the current slot's `recovery_<slot>` partition, the boot path a dual-boot
  layout would use (recovery starts do not use a slot try, and the stock boot partition stays). It writes only
  `recovery_a` or `recovery_b`, never switches slots, checks the sha256 and the Android header, and needs a typed
  confirmation. It would be needed again after every Android OTA (an OTA switches slots). Rollback: write the saved stock
  recovery image the same way.

**The install does not use this tool, and it is untested as a dual-boot path.** A U-Boot image in `recovery_<slot>` also needs an AVB footer made for that partition
(`docs/guide/07-INSTALL-REVIEW.md` R-1).
