Name:           iceland-coexist
Version:        1.0
Release:        8%{?dist}
Summary:        OnePlus Pad 4: Fedora 44 next to Arch Linux ARM in one shared /boot
License:        GPL-2.0-or-later
BuildArch:      noarch
Source0:        60-iceland-coexist.install
Source1:        coexist.conf
Source2:        install.conf
Source3:        02-iceland-coexist.conf
Source4:        52-iceland-coexist-hold.repo
Source5:        45-iceland-vmlinuz-first.install
Source6:        iceland-oneshot
Source7:        dracut-oneshot-module-setup.sh
Source8:        iceland-oneshot-clear.service
Source9:        iceland-oneshot-consume.service
Source10:       03-iceland-oneshot.conf
Requires:       iceland-device >= 0.28-30
Requires:       /usr/bin/kernel-install
Requires:       dracut
# iceland-oneshot: grub2-editenv, findmnt / blkid / losetup, cmp, lsinitrd
Requires:       /usr/bin/grub2-editenv
Requires:       util-linux
Requires:       diffutils

%description
Fedora's kernel-install writes only into its own subdirectory of the shared /boot (bind-mounted at /boot by
/etc/fstab); its BLS entries are fedora-<kver>-f44.conf in the shared loader/entries; the default boot entry is never
changed by a kernel install. Fedora's own boot-entry, device-tree, GRUB and EFI writers are masked; Mesa, the
patched gst-plugins-good, libcamera, GRUB and shim are held. PC-built for the fedback kit (22 Oct 2026).
iceland-oneshot (1.0-4): GRUB cannot write grubenv on this tablet, so a one-shot boot entry is cleared by Linux:
in the initramfs before udev starts (dracut module iceland-oneshot), and by a root unit on every boot as the
fallback.

%prep
%build
%install
install -Dm0755 %{SOURCE0} %{buildroot}/usr/lib/kernel/install.d/60-iceland-coexist.install
install -Dm0755 %{SOURCE5} %{buildroot}/usr/lib/kernel/install.d/45-iceland-vmlinuz-first.install
install -Dm0644 %{SOURCE1} %{buildroot}/etc/iceland/coexist.conf
install -Dm0644 %{SOURCE2} %{buildroot}/etc/kernel/install.conf
install -Dm0644 %{SOURCE3} %{buildroot}/etc/dracut.conf.d/02-iceland-coexist.conf
install -Dm0644 %{SOURCE4} %{buildroot}/usr/share/dnf5/repos.override.d/52-iceland-coexist-hold.repo
mkdir -p %{buildroot}/etc/kernel/install.d
install -Dm0755 %{SOURCE6} %{buildroot}/usr/bin/iceland-oneshot
install -Dm0755 %{SOURCE7} %{buildroot}/usr/lib/dracut/modules.d/91iceland-oneshot/module-setup.sh
install -Dm0644 %{SOURCE8} %{buildroot}/usr/lib/dracut/modules.d/91iceland-oneshot/iceland-oneshot-clear.service
install -Dm0644 %{SOURCE9} %{buildroot}/usr/lib/systemd/system/iceland-oneshot-consume.service
mkdir -p %{buildroot}/usr/lib/systemd/system/sysinit.target.wants
ln -s ../iceland-oneshot-consume.service %{buildroot}/usr/lib/systemd/system/sysinit.target.wants/iceland-oneshot-consume.service
install -Dm0644 %{SOURCE10} %{buildroot}/etc/dracut.conf.d/03-iceland-oneshot.conf
mkdir -p %{buildroot}/var/lib/iceland/oneshot
for p in 10-devicetree 20-grub 90-loaderentry 90-uki-copy 92-tuned 95-set-boot-entry 96-iceland-trial 99-grub-mkconfig 90-iceland-dtb; do
	ln -s /dev/null %{buildroot}/etc/kernel/install.d/$p.install
done

%posttrans
# the module reaches an initramfs with the next kernel, or by hand: iceland-oneshot initramfs --side / --promote
# (the opt1 kit step A builds, boot-tests and then promotes it). Nothing is rebuilt here.
lsinitrd /boot/initramfs-$(uname -r).img 2>/dev/null | grep -q iceland-oneshot-clear.service || echo "iceland-coexist: the running kernel's initramfs has no one-shot module yet (iceland-oneshot initramfs --side)" || :

%files
/usr/bin/iceland-oneshot
/usr/lib/dracut/modules.d/91iceland-oneshot/module-setup.sh
/usr/lib/dracut/modules.d/91iceland-oneshot/iceland-oneshot-clear.service
/usr/lib/systemd/system/iceland-oneshot-consume.service
/usr/lib/systemd/system/sysinit.target.wants/iceland-oneshot-consume.service
/etc/dracut.conf.d/03-iceland-oneshot.conf
%dir /var/lib/iceland/oneshot
/usr/lib/kernel/install.d/45-iceland-vmlinuz-first.install
/usr/lib/kernel/install.d/60-iceland-coexist.install
%config(noreplace) /etc/iceland/coexist.conf
%config(noreplace) /etc/kernel/install.conf
/etc/dracut.conf.d/02-iceland-coexist.conf
/usr/share/dnf5/repos.override.d/52-iceland-coexist-hold.repo
/etc/kernel/install.d/10-devicetree.install
/etc/kernel/install.d/20-grub.install
/etc/kernel/install.d/90-loaderentry.install
/etc/kernel/install.d/90-uki-copy.install
/etc/kernel/install.d/92-tuned.install
/etc/kernel/install.d/95-set-boot-entry.install
/etc/kernel/install.d/96-iceland-trial.install
/etc/kernel/install.d/99-grub-mkconfig.install
/etc/kernel/install.d/90-iceland-dtb.install

%changelog
* Fri Oct 30 2026 mzak <mzak.amin@gmail.com> - 1.0-8
- DTB_VARIANT defaults to standard (coexist.conf and the hook's own default): each Fedora entry boots its kernel's own
  device tree. The glitchfix-rails variant is not needed: with the rails in auto mode and the kernel's USB fix
  (dwc3_qcom.keep_icc_runtime, q90d and later) on, the display glitch did not appear; with the fix off it came back.
  An existing /etc/iceland/coexist.conf is kept (noreplace): set DTB_VARIANT=standard there by hand.

* Sat Oct 24 2026 mzak <mzak.amin@gmail.com> - 1.0-7
- iceland-oneshot consume (every boot): every one-shot entry that next_entry does not name is removed (a copy stays in
  /var/lib/iceland/oneshot/entries/). After a one-shot that hung before the initramfs (q90o-run stage C, pseudo-NMI)
  its entry stayed in /boot/loader/entries and kept being booted
- iceland-oneshot arm refuses options the kernel acts on before the initramfs (irqchip.*, early memory / CPU / console
  / security options): if they break the boot nothing can clear next_entry (GRUB cannot write here) and the one-shot
  repeats at every start; --allow-early arms them anyway, with a warning

* Thu Oct 22 2026 mzak <mzak.amin@gmail.com> - 1.0-6
- iceland-oneshot clear-initrd: looks for the boot file system on /dev/mapper/iceland-* too (iceland-device 0.28-32
  maps the Fedora disk's partitions with device-mapper when iceland.carrier.map=dm is on the command line)
- 60-iceland-coexist.install: a new kernel without its own DTB_VARIANT tree (/usr/lib/iceland/dtb/K/ or the rpm's
  dtb/qcom/) gets the default kernel's variant tree when the two kernels' own trees are byte-identical; else the
  kernel's own tree with a WARNING naming the reason (q90h fell back to its own tree silently)

* Thu Oct 22 2026 mzak <mzak.amin@gmail.com> - 1.0-5
- iceland-oneshot arm --initrd: compare the directories by device and inode (/boot is a bind mount of
  /bootfs/fedora44 on the tablet, so pwd -P of the two differed and the side initramfs was refused)

* Thu Oct 22 2026 mzak <mzak.amin@gmail.com> - 1.0-4
- iceland-oneshot: reliable one-shot boots although GRUB cannot write grubenv here: entries
  iceland-oneshot-NAME.conf (copy of the default + options), cleared in the initramfs before udev starts
  (dracut module 91iceland-oneshot, only with iceland.oneshot= on the command line) and by
  iceland-oneshot-consume.service on every boot (fallback); grubenv edited in place (same 1024 bytes)
- iceland-oneshot initramfs --side / --promote / --undo: rebuild the running kernel's initramfs with the module,
  boot-test it as a one-shot first

* Thu Oct 22 2026 mzak <mzak.amin@gmail.com> - 1.0-3
- 45-iceland-vmlinuz-first.install: /boot/vmlinuz-K before 50-dracut, so dracut never targets the read-only
  ESP (/boot/efi/<machine-id>/K/initrd) for a new kernel (q90f install, 22 Oct 2026)

* Thu Oct 22 2026 mzak <mzak.amin@gmail.com> - 1.0-2
- 60-iceland-coexist.install: quoting fix in a log line (an apostrophe inside ${...:-...})

* Thu Oct 22 2026 mzak <mzak.amin@gmail.com> - 1.0-1
- first build (fedback kit): Fedora next to Arch in one /boot
