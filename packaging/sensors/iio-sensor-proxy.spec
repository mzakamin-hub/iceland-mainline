## START: Set by rpmautospec
## (rpmautospec version 0.8.4)
## RPMAUTOSPEC: autorelease, autochangelog
%define autorelease(e:s:pb:n) %{?-p:0.}%{lua:
    release_number = 3;
    base_release_number = tonumber(rpm.expand("%{?-b*}%{!?-b:1}"));
    print(release_number + base_release_number - 1);
}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}
## END: Set by rpmautospec

Name:           iio-sensor-proxy
Version:        3.9
Release:        13%{?dist}.iceland1
Summary:        IIO accelerometer sensor to input device proxy

# tests/unittest_inspector.py is LGPL-2.1-or-later but it is not packaged
License:        GPL-3.0-or-later
URL:            https://gitlab.freedesktop.org/hadess/iio-sensor-proxy
Source0:        %{url}/-/archive/%{version}/%{name}-%{version}.tar.bz2
# a client that claims a sensor while the daemon is still looking for sensors gets its readings
Patch9001:      0001-main-poll-sensors-claimed-during-the-initial-discove.patch
# mutter 50 never claims an accelerometer it sees at once after a boot in touch mode: HasAccelerometer is held
# back until the client has claimed, or for 2 s after it looked (a mutter that waits for it: daemon restart)
Patch9002:      0002-main-hold-back-HasAccelerometer-until-a-client-has-c.patch
# the SSC light sensor streams at 10 Hz with +-2 % noise: a level is passed on only at a 5 % / 1 lux step, at most
# every 500 ms (SSC_LIGHT_FILTER=0 in the environment: every sample, as before)
Patch9003:      0003-ssc-light-rate-limit-and-hysteresis-for-the-ambient-.patch
# auto-rotate from the sensor hub's on-change device_orient sensor instead of the 25 Hz accelerometer stream
# (SSC_ACCEL_ORIENT=0 in the environment, or a hub without it: the accelerometer stream, as before)
Patch9004:      0004-ssc-accel-orientation-from-the-sensor-hub-s-device_o.patch

BuildRequires:  meson
BuildRequires:  gcc
BuildRequires:  git-core
BuildRequires:  gtk-doc
BuildRequires:  pkgconfig(udev)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  pkgconfig(gudev-1.0)
BuildRequires:  pkgconfig(polkit-gobject-1)
# iceland: SSC (Qualcomm sensor hub) support; libssc-devel is our own package (not in Fedora 45)
BuildRequires:  pkgconfig(libssc) >= 0.2.1
BuildRequires:  systemd
BuildRequires:  umockdev
BuildRequires:  python3-dbusmock
%{?systemd_requires}

%description
%{summary}.

%package docs
Summary:        Documentation for %{name}
License:        GFDL-1.1-or-later
BuildArch:      noarch

%description docs
This package contains the documentation for %{name}.

%prep
%autosetup -S git_am

%build
%meson -Dgtk_doc=true -Dgtk-tests=false -Dssc-support=enabled
%meson_build

%install
%meson_install

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%license COPYING
%doc README.md
%{_bindir}/monitor-sensor
%{_libexecdir}/%{name}
%{_unitdir}/%{name}.service
%{_udevrulesdir}/*-%{name}.rules
%{_datadir}/dbus-1/system.d/net.hadess.SensorProxy.conf
%{_datadir}/polkit-1/actions/net.hadess.SensorProxy.policy

%files docs
%dir %{_datadir}/gtk-doc/
%dir %{_datadir}/gtk-doc/html/
%{_datadir}/gtk-doc/html/%{name}/

%changelog
* Sat Nov 07 2026 mzak <mzak.amin@gmail.com> - 3.9-13.iceland1
- rebased onto Fedora 45's iio-sensor-proxy-3.9-3.fc45 spec (Fedora's tarball, gtk-doc and the -docs package
  again): SSC support enabled (libssc), local patches 0001-0004 unchanged as Patch9001-9004 (git am)

* Fri Oct 23 2026 mzak <mzak.amin@gmail.com> - 3.9-12.iceland1
- auto-rotate from the sensor hub's own orientation sensor (local patch 0004)

* Thu Oct 15 2026 mzak <mzak.amin@gmail.com> - 3.9-11.iceland1
- SSC ambient light level rate limit and hysteresis (local patch 0003)

* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 3.9-10.iceland1
- 3.9 with SSC support (libssc) for the OnePlus Pad 4; local patches 0001 and 0002
- the earlier changelog entries are Fedora's: https://src.fedoraproject.org/rpms/iio-sensor-proxy
