# SPDX-License-Identifier: GPL-2.0-or-later
#
# hexagonrpc for the OnePlus Pad 4: hexagonrpcd serves the ADSP's sensors PD its configuration files over FastRPC
# (the sensor hub does not start its sensors without them). Not in Fedora 44.
# Upstream snapshot + two local patches (docs/sensors/patches/hexagonrpc).

%global commit 598b591ae9da6a6cfe2ca5ea78998019ca6395ea
%global shortcommit 598b591

Name:           hexagonrpc
Version:        0.5.0^19.git%{shortcommit}
Release:        1.iceland2%{?dist}
Summary:        FastRPC daemon and library for Qualcomm Hexagon DSPs
License:        GPL-3.0-or-later
URL:            https://github.com/linux-msm/hexagonrpc
Source0:        %{url}/archive/%{commit}/%{name}-%{commit}.tar.gz
Source1:        hexagonrpc.sysusers
Source2:        60-hexagonrpc.rules
# the Pad 4's sensor hub asks for /odm/etc/sensor (stock keeps its sensor configs there)
Patch1:         0001-hexagonrpcd-serve-odm-etc-sensor-from-root-odm-senso.patch
# the Pad 4's sensors PD calls apps_std method 36 once per boot: answer unsupported calls with the error and keep
# serving (upstream hexagonrpcd leaves its loop and exits; systemd restarted it 3 s later on every boot)
Patch2:         0002-hexagonrpcd-answer-unsupported-calls-and-keep-serving.patch

BuildRequires:  gcc
BuildRequires:  meson >= 1.1
BuildRequires:  ninja-build
BuildRequires:  systemd-rpm-macros
%{?systemd_requires}

%description
hexagonrpcd is the application-processor side of FastRPC for Qualcomm Hexagon DSPs: it answers the remote
procedure calls with which a DSP reads its files (sensor configuration, registry, DSP libraries) from a directory
tree on the Linux side. Qualcomm's sensor hub (SSC) in the ADSP needs it before any sensor appears.
Also contains libhexagonrpc and chrecd.

%prep
%autosetup -p1 -n %{name}-%{commit}

%build
%meson
%meson_build

%install
%meson_install
# upstream installs the units below libdir
install -d %{buildroot}%{_unitdir}
mv %{buildroot}%{_libdir}/systemd/system/*.service %{buildroot}%{_unitdir}/
rmdir %{buildroot}%{_libdir}/systemd/system %{buildroot}%{_libdir}/systemd
# no headers are installed, so the unversioned link has no user
rm -f %{buildroot}%{_libdir}/libhexagonrpc.so
# the units run as user "fastrpc"; the device nodes get its group
install -Dm0644 %{SOURCE1} %{buildroot}%{_sysusersdir}/hexagonrpc.conf
install -Dm0644 %{SOURCE2} %{buildroot}%{_udevrulesdir}/60-hexagonrpc.rules

%check
%meson_test

%post
%systemd_post hexagonrpcd-adsp-rootpd.service hexagonrpcd-adsp-sensorspd.service hexagonrpcd-sdsp.service

%preun
%systemd_preun hexagonrpcd-adsp-rootpd.service hexagonrpcd-adsp-sensorspd.service hexagonrpcd-sdsp.service

%postun
%systemd_postun_with_restart hexagonrpcd-adsp-rootpd.service hexagonrpcd-adsp-sensorspd.service hexagonrpcd-sdsp.service

%files
%license COPYING
%doc README.md
%{_bindir}/hexagonrpcd
%{_libdir}/libhexagonrpc.so.0.5
%dir %{_libexecdir}/hexagonrpc
%{_libexecdir}/hexagonrpc/chrecd
%{_mandir}/man1/hexagonrpcd.1*
%{_unitdir}/hexagonrpcd-adsp-rootpd.service
%{_unitdir}/hexagonrpcd-adsp-sensorspd.service
%{_unitdir}/hexagonrpcd-sdsp.service
%{_sysusersdir}/hexagonrpc.conf
%{_udevrulesdir}/60-hexagonrpc.rules

%changelog
* Fri Oct 16 2026 mzak <mzak.amin@gmail.com> - 0.5.0^19.git598b591-1.iceland2
- Patch 0002: an unsupported FastRPC call (unknown handle or method, missing arguments, no memory) is answered
  with its error and hexagonrpcd keeps serving. On the Pad 4 the ADSP's sensors PD calls apps_std method 36
  (sc 0x1f050100) right after INIT_ATTACH_SNS; upstream hexagonrpcd logged 'Unsupported method: 36', left its
  loop and exited, and hexagonrpcd-adsp-sensorspd.service was restarted by systemd once on every boot
* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 0.5.0^19.git598b591-1.iceland1
- First package: upstream 598b591 (v0.5.0 + 19 commits) with the Pad 4 patch that serves /odm/etc/sensor from
  <root>/odm/sensor; units moved to the systemd unit directory; user "fastrpc" and a udev rule for the nodes
