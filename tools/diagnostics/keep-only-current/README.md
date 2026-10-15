# keep-only-current

Frees space on the installed system: keeps only the running kernel and the current root, and removes every other
`kernel-iceland`, every root snapshot (`snapshots/root-*`, `root.before-rollback-*`) and their "Roll back" GRUB
entries.

```
sudo bash keep-only-current.sh            # read only: lists what would go
sudo bash keep-only-current.sh --delete   # does it, after you type KEEP-ONLY
```

**Permanent.** Removed kernels and deleted snapshots cannot be brought back. Afterwards GRUB offers no older kernel
and no rollback entry until the next dnf transaction takes a new snapshot. Kept: the running kernel, the root, `/home`,
`/var` and the update bundles' undo copies in `/var/lib/iceland/backup-*`.

It refuses to run while a kernel trial boot is pending or when the GRUB default is not the running kernel: confirm
the running kernel first.
