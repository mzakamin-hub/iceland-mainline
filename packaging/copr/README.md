# Updates through COPR

Owner's decision (16 Oct 2026): the tablet gets the project's packages through a COPR repository and a normal
`dnf upgrade` (or GNOME Software). Bundles over the LAN share and `iceland-repo-sync` stay available as the offline
path. This directory holds the COPR side. The device side is iceland-device 0.28-17 (a candidate, see "Device side").

Nothing here creates an account, a token or a COPR project. The owner does those steps (section "Owner steps").

## Design

| | Choice | Why |
|---|---|---|
| Projects | `<owner>/iceland-testing` and `<owner>/iceland` (stable), chroot `fedora-44-aarch64` only | COPR has no channels inside a project. Two projects is COPR's own way: each has its own repository, key and permissions. |
| Promotion | `copr-cli fork <owner>/iceland-testing <owner>/iceland --confirm` (`copr-setup.sh OWNER --promote`) | A fork copies the newest successful build of each package. Nothing is rebuilt, so stable gets the exact binaries the rehearsal tested (signed again with stable's key). Promote only when testing holds nothing untested: testing is promoted as one tested set. |
| Builds | COPR's **custom** source method, one script per package (`copr-custom-script.sh`): clone `main`, run `make-srpm.sh PKG --sources result` | COPR's `make srpm` method needs a `.copr/Makefile` at the repository root. The custom method needs no file outside `packaging/copr/`. The script runs in a `fedora-44-x86_64` chroot with network. COPR then builds the source rpm on its aarch64 builders with no network. |
| Trigger | Manual: `copr-setup.sh OWNER --build PKG [--run]`, or the GitHub Actions template `github/copr-build.yml` (workflow_dispatch, token in the secret `COPR_CONFIG`) | A build should follow a decision, not every push to `main`: a kernel build takes hours. COPR's webhook (`--webhook-rebuild on`) is possible later. |
| Signing | COPR signs every rpm with a per-project GPG key it creates and holds. The public key is at `https://download.copr.fedorainfracloud.org/results/<owner>/<project>/pubkey.gpg`. | The device repository file sets `gpgcheck=1` with that key. dnf asks to import it at the first update (`dnf upgrade -y` imports it). Next step after the projects exist: fetch both keys once, compare the fingerprints with the ones on the projects' pages, and ship them in iceland-device as `file://` keys, so the device trusts nothing it downloads at first use. We never hold the private key. COPR can rotate it, and then the shipped copy needs an update. |
| Retention | COPR keeps the newest build of each package indefinitely; older builds are deleted after 14 days | The tablet keeps its own three kernels (installonly). For a downgrade of iceland-device or the sensor programs, use the pre-transaction btrfs snapshot or a bundle. |

### Packages

| Package | How `make-srpm.sh` gets its sources | Notes |
|---|---|---|
| `kernel-iceland` | `kernel-iceland/kernel-iceland.spec` **(new, built from source)**: the kernel.org tarball `linux-7.3-rc7.tar.gz`, GitHub's archive of iceland-linux at the queue commit, `config-iceland` (the full config of kernel q89l), `90-iceland-dtb.install` | See "The kernel on COPR". |
| `iceland-device` | `packaging/iceland-device` + audioreach-topology `993a17d` + `audio/`, as `build-rpm.sh` does; `COPR_OWNER` is written into the spec (`%global copr_owner`) | noarch |
| `hexagonrpc`, `libssc`, `iio-sensor-proxy` | `packaging/sensors/*.spec` with their upstream tarballs (pinned commits) and the patches in `docs/sensors/patches/` | Build order: `libssc` before `iio-sensor-proxy` (it build-requires `libssc-devel`; COPR adds the project's own repository to the buildroot). |
| `iceland-firmware` | `make-srpm.sh` supports it (git archive of the iceland-firmware repository), **but it is not added to COPR** | COPR accepts only content whose licence is on Fedora's allowed list and that the uploader has the right to distribute. The Pad 4 blobs carry `LicenseRef-Callaway-Redistributable-no-modification-permitted` and no redistribution grant from OnePlus / Qualcomm. They stay on the GitHub release with `iceland-firmware-fetch` (sha256-pinned), as today. Owner decision before any change. |

### The kernel on COPR

The PC's `kernel-iceland` rpm is **not** a source build. `mk-krpm-q89l.sh` and `krpm-tool/mk-kernel-rpm.sh` wrap a finished
PC build (`binq89l` + `modstageq89l`, made with the Android clang r596125) in an rpm whose `%build` is empty. COPR
must compile, so `kernel-iceland/kernel-iceland.spec` is a new from-source spec:

- `%prep` **proves** the source. The tarball's git tree must equal `kernel.pin`'s `UPSTREAM_TREE`, and the tree after
  each patch series must equal `TREE_AFTER_0001_infiniti` / `TREE_AFTER_0002_iceland`. This is the same proof the PC
  scripts run. The patch count must also equal `npatches`.
- `%build` uses `config-iceland` and `make olddefconfig` with Fedora's clang / lld (`LLVM=1`). It **stops** when
  olddefconfig changes any option that is not a toolchain property. It then builds `Image`, the modules and the iceland
  DTB, with `KBUILD_BUILD_USER=mzak` and `KBUILD_BUILD_HOST=iceland-builder` as on the PC.
- `kernel.release` is `7.3.0-rc7-iceland-00438-qaca0efd7d6b1`, and the rpm version is
  `7.3.0~rc7.iceland.00438.qaca0efd7d6b1`. It sorts after the PC build of the same queue (`...00438.gc7bc30386efe`,
  because rpm compares `q` > `g`) and before the next queue. Its module directory is separate, so both kernels can be
  installed side by side.
- Files, scriptlets, `Provides: installonlypkg(kernel)` and dependencies are the PC spec's. `%install` repeats the PC
  check's core rows: at least 900 modules, `sc1320cs` present, and the version string `(mzak@iceland-builder)`.
- Limits: the COPR build timeout defaults to 5 h. `copr-setup.sh` sets 30 h (108000 s) for the kernel; Fedora Copr
  allows up to 50 h. Normal builders have 140 GB of disk, enough for a `DEBUG_INFO=y` build. COPR does not publish
  CPU counts, so the time is an estimate of 2-4 h. If it is too slow, the owner can ask COPR for high-performance
  aarch64 builders (a GitHub issue on fedora-copr/copr with the pattern `<owner>/iceland-testing/.*aarch64/kernel-iceland`).
- **The first COPR kernel is a new binary** (a different compiler build of the same source and config). It must pass
  a RAM rehearsal from the testing channel before it is promoted. Until then the PC build stays the shipped kernel.
- To move to a new queue, update `queue_commit`, `queue_short`, `npatches` and `base_tag` / `base_ver` (when the base
  changes), replace `config-iceland` with the new kernel's `build/bin<tag>/config`, and add a changelog entry.

## Device side (iceland-device 0.28-17, candidate in WSL `~/mainline/build/wf/copr/`)

- `/etc/yum.repos.d/iceland-copr.repo` has two repositories, `iceland-copr-stable` and `iceland-copr-testing`.
  - Both are **off** as shipped.
  - `gpgcheck=1` with COPR's project key.
  - `baseurl` names `fedora-44-$basearch`, matching the release pin.
  - `includepkgs` is limited to our names: `kernel-iceland*`, `iceland-device*`, `iceland-firmware*`, `iio-sensor-proxy*`, `libssc*` and `hexagonrpc*`.
  - The main `excludepkgs` of `80-iceland-kernel.conf` still refuse Fedora's kernels from every repository.
  - Fedora's repositories still exclude our names (`50-iceland-fedora-hold.repo`).
  - `priority=10`, the same as `iceland-local`, so between the two the higher version wins. A lower number would hide
    the other repository's packages whatever their version.
- `iceland-channel stable|testing|off|status`, run as root, writes `/etc/dnf/repos.override.d/80-iceland-channel.repo` and
  refreshes dnf's cache. `testing` enables both projects. Leaving testing downgrades nothing: packages stay until stable
  has a newer version, and the installed kernels stay selectable in GRUB. Do not use `dnf copr enable`: it adds a second
  copy of the repository without `includepkgs`.
- Kernel retention:
  - `kernel-iceland` is removed from `/etc/dnf/protected.d/iceland-device.conf`. dnf refuses to remove a protected
    package, so the installonly trim of the oldest kernel could not happen.
  - `installonly_limit=3` and `protect_running_kernel=True` are now written in `80-iceland-kernel.conf`.
  - With `dnf upgrade`, a new `kernel-iceland` installs next to the others. `kernel-install` then runs
    `96-iceland-trial.install`, which boots the new kernel once as a trial. The confirmed kernel stays the default
    until the desktop is reached. The 4th kernel makes dnf remove the oldest one that is not running.
  - If that is the confirmed kernel, the running kernel becomes the confirmed one (it booted). Otherwise the newest
    remaining kernel whose trial did not fail is used. Before this change it was the newest remaining one, even a
    failed trial.
- Snapshots: `iceland-snapshot.actions` takes a btrfs snapshot before every dnf transaction. The 16 Oct issue scan
  found it broken (syntax error). Fix it before the first COPR update; it is the rollback for everything except the kernel.
- Migration from the local repository / bundles:
  1. Install iceland-device 0.28-17, built with the owner's account name (from a bundle the last time, or from the
     testing project).
  2. Run `sudo iceland-channel stable`, then `sudo dnf upgrade`.
  3. `iceland-local` and `iceland-repo-sync` stay, for offline updates and rehearsal candidates. Their packages
     compete on version only.
- Tests (PC, package test style): `tests/test_copr_channel.py`, with 85 checks.
  - The repository file and the name filters (fnmatch against the real exclude lists).
  - `iceland-channel` in a fake root against a fake dnf5.
  - The retention lines.
  - Six trial-plugin removal cases.
  - The spec lines.
  - `test_install_parts.py` takes the new confirmed-kernel rule, and `test_charging.py` accepts release 16 or later.
  - The whole set has 50 test files, all PASS. A PC rpm build of 0.28-17 (stub tools) has 150 paths: 148 plus the
    repository file and `iceland-channel`.
  - Not run (needs the tablet, a rehearsal): dnf5's resolution with `includepkgs` + priority, the installonly trim with
    the running kernel protected, and GNOME Software showing the COPR updates.

## Owner steps (only the owner can do these)

1. **Fedora account.** Create one at <https://accounts.fedoraproject.org> (username, e-mail, password, then the e-mail
   confirmation). The username becomes `<owner>` in every URL.
2. **COPR login.** Open <https://copr.fedorainfracloud.org>, select "Log in" and sign in with the Fedora account.
3. **API token.** Open <https://copr.fedorainfracloud.org/api/>. COPR shows a `~/.config/copr` block (login, username,
   token, copr_url) with an expiry date. Use one of the two options below; neither is ever pasted into a chat or a file
   of the repositories.
   - **On the PC:** install copr-cli (on Fedora `sudo dnf install copr-cli`; elsewhere `pip install copr-cli`). Save the
     block as `~/.config/copr` and run `chmod 600 ~/.config/copr`.
   - **In GitHub:** go to iceland-mainline, Settings > Secrets and variables > Actions > New repository secret. Name it
     `COPR_CONFIG`, paste the block as the value, and copy `github/copr-build.yml` to `.github/workflows/`.
4. **Projects and packages.** Run `bash packaging/copr/copr-setup.sh <owner>` to print the commands, read them, then run
   it again with `--run`. The command creates both projects with these settings:
   - chroot `fedora-44-aarch64`;
   - network off during builds;
   - not listed on the COPR home page;
   - the description and instructions below.

   It also adds the five packages to iceland-testing with the custom method. If you create the projects in the web UI
   instead, use the same chroot. Also turn off "Follow Fedora branching", so that no F45 chroot is added: the tablet
   stays on 44 until 45 is rehearsed.
5. **First builds, one at a time.** Start each build after the previous one has succeeded:
   `copr-setup.sh <owner> --build hexagonrpc --run`, then `libssc`, `iio-sensor-proxy`, `iceland-device`, and
   `kernel-iceland` last (hours).
6. **Device package with the account name.** Tell the coordinator `<owner>` (a username is not a secret). iceland-device
   0.28-17 is then built with `COPR_OWNER=<owner>`, and the projects' key fingerprints are pinned in the next release.
7. **Promotion,** after a RAM rehearsal of the testing builds: `copr-setup.sh <owner> --promote --run`.

### Name and description (trademarks)

- The COPR projects are named `iceland` / `iceland-testing`, not "Fedora ...". Plain "Fedora" is reserved for the
  Fedora Project's own products.
- An image of Fedora plus our packages may be called a **Fedora Remix**, for example "Fedora Remix for OnePlus Pad 4",
  without asking. Rules: "Fedora" and "Remix" are never separated, the Fedora logo is not used, and nothing implies
  endorsement by Fedora or Red Hat.
- A remix with non-Fedora software replaces `fedora-logos`, `fedora-release` and `fedora-release-notes` with
  equivalents (e.g. `generic-logos`, `generic-release`, `generic-release-notes`). Our image still carries Fedora's.
  This is a to-do for the image builder (X2) before the name is used.
  Sources: <https://fedoraproject.org/wiki/Remix>, <https://docs.fedoraproject.org/en-US/legal/trademarks/>.
- The project description (set by `copr-setup.sh`) says what the packages are, for which device, that the project is
  **unofficial and not affiliated with or endorsed by the Fedora Project, Red Hat or OnePlus**, and where the sources
  are. The instructions say not to use `dnf copr enable` (the device package ships the repository file) and how to
  switch channels.
- COPR's own rules: content only under licences on Fedora's allowed list, and only what the uploader may distribute.
  That is why the firmware is not on COPR. Every package here is GPL / LGPL / MIT source.

## Local checks (PC, no upload)

`~/mainline/build/wf/copr/verify-srpms.sh` copies iceland-mainline together with this directory and the 0.28-17
candidate. It then runs `make-srpm.sh --srpm` for every package with the PC's rpm 4.18 tools and `--sources` for one.
It also runs the kernel's `%prep` (`rpmbuild -bp`) with the real kernel.org and GitHub tarballs, which is the full
source proof. A real binary build needs Fedora 44 aarch64 (mock or COPR). Mock config for a local try on an aarch64
Fedora host: `mock -r fedora-44-aarch64 --rebuild kernel-iceland-*.src.rpm`. On x86_64, mock would need
`qemu-user-static` and would take a day: use COPR.

## Files

| File | |
|---|---|
| `make-srpm.sh` | spec + sources (`--sources DIR`) or the SRPM (`--srpm DIR`) of one package |
| `copr-custom-script.sh` | the COPR custom-method script (template; `copr-setup.sh` fills in the package and owner) |
| `copr-setup.sh` | prints (or with `--run` runs) the owner's copr-cli commands: create, build, promote |
| `kernel-iceland/` | the from-source kernel spec, `config-iceland` (q89l's config), `90-iceland-dtb.install` |
| `github/copr-build.yml` | GitHub Actions template (inactive until the owner copies it to `.github/workflows/`) |
