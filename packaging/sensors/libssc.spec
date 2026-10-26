# SPDX-License-Identifier: GPL-2.0-or-later
#
# libssc for the OnePlus Pad 4: the client library for Qualcomm's sensor hub (SSC) over QMI / QRTR.
# iio-sensor-proxy uses it for the accelerometer, light, proximity and compass sensors. Not in Fedora 44.

%global commit 54dd13e36d65c21263cf5b0f4a70c230a77b26bc
%global shortcommit 54dd13e

Name:           libssc
Version:        0.4.4^8.git%{shortcommit}
Release:        2.iceland1%{?dist}
Summary:        Library to access the sensors of the Qualcomm Sensor Core (SSC)
License:        GPL-3.0-or-later
URL:            https://codeberg.org/DylanVanAssche/libssc
Source0:        %{url}/archive/%{commit}.tar.gz#/%{name}-%{shortcommit}.tar.gz
# OnePlus Pad 4: the sensor hub's hall sensor (cover), data type "hall"; ssccli --sensor hall
Patch1:         libssc-iceland-hall.patch

BuildRequires:  gcc
BuildRequires:  meson >= 1.4
BuildRequires:  ninja-build
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(qmi-glib) >= 1.33.4
BuildRequires:  pkgconfig(libprotobuf-c)
BuildRequires:  pkgconfig(gobject-introspection-1.0)
BuildRequires:  protobuf-c-compiler
BuildRequires:  protobuf-compiler

%description
libssc talks to the Qualcomm Sensor Core (the sensor hub in the ADSP / SLPI of Snapdragon SoCs) through QMI
service 400 on the QRTR bus and exposes the accelerometer, gyroscope, magnetometer, compass, light and proximity
sensors as GObjects. ssccli reads a sensor from the command line.

%package devel
Summary:        Development files for libssc
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
Headers, the pkg-config file and the introspection data of libssc.

%prep
%autosetup -n %{name} -p1
# the tests and the mock sensor hub need Python headers and a QRTR mock: not built for the package
sed -i "/subdir('mocking')/d; /subdir('tests')/d" meson.build

%build
%meson
%meson_build

%install
%meson_install
# no Vala binding in the package (built only where vapigen happens to be installed)
rm -rf %{buildroot}%{_datadir}/vala
# the introspection data is built when gobject-introspection finds libqmi's
: > gir-main.lst; : > gir-devel.lst
if [ -e %{buildroot}%{_libdir}/girepository-1.0/SSC-2.typelib ]; then echo "%{_libdir}/girepository-1.0/SSC-2.typelib" >> gir-main.lst; fi
if [ -e %{buildroot}%{_datadir}/gir-1.0/SSC-2.gir ]; then echo "%{_datadir}/gir-1.0/SSC-2.gir" >> gir-devel.lst; fi

%files -f gir-main.lst
%license LICENSE
%doc README.md CHANGELOG.md
%{_bindir}/ssccli
%{_libdir}/libssc.so.2

%files devel -f gir-devel.lst
%{_includedir}/libssc/
%{_libdir}/libssc.so
%{_libdir}/pkgconfig/libssc.pc

%changelog
* Tue Oct 27 2026 mzak <mzak.amin@gmail.com> - 0.4.4^8.git54dd13e-2.iceland1
- hall sensor (data type "hall": the Pad 4's cover hall in the sensor hub) and ssccli --sensor hall

* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 0.4.4^8.git54dd13e-1.iceland1
- First package: upstream 54dd13e (v0.4.4 + 8 commits), without the test and mocking subdirectories
