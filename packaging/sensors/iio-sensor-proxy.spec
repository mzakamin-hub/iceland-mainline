# SPDX-License-Identifier: GPL-2.0-or-later
#
# iio-sensor-proxy for the OnePlus Pad 4: 3.9 built with SSC support (the sensors behind the ADSP) and two local
# patches (docs/sensors/patches/iio-sensor-proxy). Fedora 44 ships 3.8 without SSC support; this build replaces it
# (the release number stays above Fedora's, and the local repository has the higher dnf priority).

Name:           iio-sensor-proxy
Version:        3.9
Release:        11.iceland1%{?dist}
Summary:        IIO accelerometer sensor to input device proxy
License:        GPL-3.0-or-later
URL:            https://gitlab.freedesktop.org/hadess/iio-sensor-proxy
Source0:        %{url}/-/archive/%{version}/%{name}-%{version}.tar.gz
# a client that claims a sensor while the daemon is still looking for sensors gets its readings
Patch1:         0001-main-poll-sensors-claimed-during-the-initial-discove.patch
# mutter 50 never claims an accelerometer it sees at once after a boot in touch mode: HasAccelerometer is held
# back until the client has claimed, or for 2 s after it looked (a mutter that waits for it: daemon restart)
Patch2:         0002-main-hold-back-HasAccelerometer-until-a-client-has-c.patch
# the SSC light sensor streams at 10 Hz with +-2 % noise: a level is passed on only at a 5 % / 1 lux step, at most
# every 500 ms (SSC_LIGHT_FILTER=0 in the environment: every sample, as before)
Patch3:         0003-ssc-light-rate-limit-and-hysteresis-for-the-ambient-.patch

BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(gio-2.0) >= 2.76
BuildRequires:  pkgconfig(gudev-1.0) >= 237
BuildRequires:  pkgconfig(polkit-gobject-1)
BuildRequires:  pkgconfig(libssc) >= 0.2.1
BuildRequires:  systemd-rpm-macros
%{?systemd_requires}
Obsoletes:      iio-sensor-proxy-docs < 3.9-10

%description
iio-sensor-proxy is a D-Bus proxy for accelerometers, ambient light sensors, proximity sensors and compasses
(net.hadess.SensorProxy). GNOME uses it for automatic screen rotation and automatic brightness.
This build reads the sensors of Qualcomm's sensor hub (SSC) through libssc.

%prep
%autosetup -p1

%build
%meson -Dssc-support=enabled -Dgtk_doc=false -Dtests=false -Dgtk-tests=false \
       -Dudevrulesdir=%{_udevrulesdir} -Dsystemdsystemunitdir=%{_unitdir}
%meson_build

%install
%meson_install

%check
%meson_test

%post
%systemd_post iio-sensor-proxy.service

%preun
%systemd_preun iio-sensor-proxy.service

%postun
%systemd_postun_with_restart iio-sensor-proxy.service

%files
%license COPYING
%doc README.md NEWS
%{_bindir}/monitor-sensor
%{_libexecdir}/iio-sensor-proxy
%{_unitdir}/iio-sensor-proxy.service
%{_udevrulesdir}/80-iio-sensor-proxy.rules
%{_datadir}/dbus-1/system.d/net.hadess.SensorProxy.conf
%{_datadir}/polkit-1/actions/net.hadess.SensorProxy.policy

%changelog
* Thu Oct 15 2026 mzak <mzak.amin@gmail.com> - 3.9-11.iceland1
- the SSC ambient light level is passed on only when it changed by 5 % or 1 lux (the larger), at most every
  500 ms; a change that comes too soon is passed on when the 500 ms are over (local patch 0003). On the Pad 4 the
  sensor hub streams the light sensor at 10 Hz and indoor noise made every sample a LightLevel change: 100 in 10 s
  with the tablet still, each waking gnome-settings-daemon's automatic brightness. SSC_LIGHT_FILTER=0 in the
  daemon's environment turns it off
* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 3.9-10.iceland1
- 3.9 with SSC support (libssc) for the OnePlus Pad 4
- sensors claimed during the initial discovery are polled (local patch 0001)
- HasAccelerometer is held back from a client until it has claimed the accelerometer, or until 2 s after it
  first looked: works around mutter 50 never claiming an accelerometer it sees at once after a boot, and keeps
  auto-rotate after a restart of the daemon under a running session (local patch 0002)
