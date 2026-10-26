Name:    libcamera
Version: 0.7.1
Release: 3%{?dist}.iceland_af1
Summary: A library to support complex camera ISPs
# see .reuse/dep5 and COPYING for details
License: LGPL-2.1-or-later
URL:     http://libcamera.org/

Source0: https://gitlab.freedesktop.org/camera/libcamera/-/archive/v%{version}/%{name}-v%{version}.tar.bz2
Source1: qcam.desktop
Source2: qcam.metainfo.xml
Source3: 70-libcamera.rules

Patch01: 0001-disable-rpi-pisp.patch
# OnePlus Pad 4 (afnxp): contrast-detect autofocus in the simple pipeline + soft ISP
# 0001-0003 from Osilvfe/libcamera caihong-camera (2f4cf4a413, 9afba3cd3d, 1b79c8179a), 0004 ours
Patch90: 0001-pipeline-simple-add-native-manual-focus-control.patch
Patch91: 0002-software_isp-report-a-luminance-gradient-focus-metri.patch
Patch92: 0003-pipeline-simple-add-contrast-detect-autofocus.patch
Patch93: 0004-pipeline-simple-autofocus-defaults-and-settling-for-.patch

# libcamera does not currently build on these architectures
ExcludeArch: s390x ppc64le

BuildRequires: gcc-c++
BuildRequires: gtest-devel
BuildRequires: desktop-file-utils
BuildRequires: meson
BuildRequires: openssl
BuildRequires: ninja-build
BuildRequires: pkgconfig(glib-2.0)
BuildRequires: gnutls-devel
BuildRequires: pkgconfig(gstreamer-video-1.0)
BuildRequires: pkgconfig(gstreamer-allocators-1.0)
BuildRequires: libatomic
BuildRequires: libevent-devel
BuildRequires: libjpeg-turbo-devel
BuildRequires: libtiff-devel
%if ! 0%{?rhel}
BuildRequires: libunwind-devel
BuildRequires: pkgconfig(libdw)
%endif
BuildRequires: libyaml-devel
BuildRequires: libyuv-devel
BuildRequires: lttng-ust-devel
BuildRequires: pkgconfig(Qt6Core)
BuildRequires: pkgconfig(Qt6Gui)
BuildRequires: pkgconfig(Qt6OpenGL)
BuildRequires: pkgconfig(Qt6OpenGLWidgets)
BuildRequires: pkgconfig(Qt6Widgets)
BuildRequires: pybind11-devel
BuildRequires: python3-devel
BuildRequires: python3-jinja2
BuildRequires: python3-ply
BuildRequires: python3-pyyaml
BuildRequires: SDL2-devel
BuildRequires: systemd-devel
# libcamera is not really usable without its IPA plugins
Recommends: %{name}-ipa%{?_isa}
Obsoletes: libcamera-doc < 0.6.0

%description
libcamera is a library that deals with heavy hardware image processing
operations of complex camera devices that are shared between the linux
host all while allowing offload of certain aspects to the control of
complex camera hardware such as ISPs.

Hardware support includes USB UVC cameras, libv4l cameras as well as more
complex ISPs (Image Signal Processor).

%package     devel
Summary:     Development package for %{name}
Requires:    %{name}%{?_isa} = %{version}-%{release}

%description devel
Files for development with %{name}.

%package     ipa
Summary:     ISP Image Processing Algorithm Plugins for %{name}
License:     LGPL-2.1-or-later AND BSD-2-Clause
Requires:    %{name}%{?_isa} = %{version}-%{release}

%description ipa
Image Processing Algorithms plugins for interfacing with device
ISPs for %{name}

%package     tools
Summary:     Tools for %{name}
License:     LGPL-2.1-or-later AND BSD-3-Clause
Requires:    %{name}%{?_isa} = %{version}-%{release}

%description tools
Command line tools for %{name}

%package     qcam
Summary:     Graphical QCam application for %{name}
License:     GPL-2.0-or-later AND MIT
Requires:    %{name}%{?_isa} = %{version}-%{release}

%description qcam
Graphical QCam application for %{name}

%package     gstreamer
Summary:     GSTreamer plugin for %{name}
Requires:    %{name}%{?_isa} = %{version}-%{release}

%description gstreamer
GSTreamer plugins for %{name}

%package     v4l2
Summary:     V4L2 compatibility layer for %{name}
Requires:    %{name}%{?_isa} = %{version}-%{release}

%description v4l2
V4L2 compatibility layer for %{name}

%package     -n python3-%{name}
Summary:     Python bindings for %{name}
Requires:    %{name}%{?_isa} = %{version}-%{release}

%description -n python3-%{name}
Python bindings for %{name}

%prep
%autosetup -p1 -n %{name}-v%{version}

%build
# cam/qcam crash with LTO
%global _lto_cflags %{nil}
export CFLAGS="%{optflags} -Wno-deprecated-declarations"
# Set also max-devirt-targets=1 to prevent compilation errors,
# maybe due to https://gcc.gnu.org/bugzilla/show_bug.cgi?id=120345.
export CXXFLAGS="%{optflags} -Wno-deprecated-declarations --param=max-devirt-targets=1"

# Build and include the virtual and vimc pipelines. This also builds tests but
# those do not get included in any packages.
%meson \
    -Dv4l2=enabled \
    -Dlc-compliance=disabled \
    %{?rhel:-Dlibunwind=disabled} \
    -Dtest=true \
    -Ddocumentation=disabled \
    -Drpi-awb-nn=disabled \
    %{nil}
%meson_build

# Stripping requires the re-signing of IPA libraries, manually
# copy standard definition of __spec_install_post and re-sign.
%define __spec_install_post \
    %{?__debug_package:%{__debug_install_post}} \
    %{__arch_install_post} \
    %{__os_install_post} \
    %{_builddir}/%{name}-v%{version}/src/ipa/ipa-sign-install.sh %{_builddir}/%{name}-v%{version}/%{_vpath_builddir}/src/ipa-priv-key.pem %{buildroot}/%{_libdir}/libcamera/ipa/ipa_*.so \
%{nil}

%install
%meson_install

# Install Desktop Entry file
desktop-file-install --dir=%{buildroot}%{_datadir}/applications \
                     %SOURCE1

# Install AppStream metainfo file
mkdir -p %{buildroot}/%{_metainfodir}/
cp -a %SOURCE2 %{buildroot}/%{_metainfodir}/

# Install udev rules
mkdir -p %{buildroot}/%{_udevrulesdir}/
install -D -m 644 %SOURCE3 %{buildroot}/%{_udevrulesdir}/

%files
%license COPYING.rst LICENSES/LGPL-2.1-or-later.txt
# We leave the version here explicitly to know when it bumps
%{_libdir}/libcamera*.so.0.7
%{_libdir}/libcamera*.so.%{version}
%{_udevrulesdir}/70-libcamera.rules

%files devel
%{_includedir}/%{name}/
%{_libdir}/libcamera*.so
%{_libdir}/pkgconfig/libcamera-base.pc
%{_libdir}/pkgconfig/libcamera.pc

%files ipa
%{_datadir}/libcamera/
%{_libdir}/libcamera/
%{_libexecdir}/libcamera/
%exclude %{_libexecdir}/libcamera/v4l2-compat.so

%files gstreamer
%{_libdir}/gstreamer-1.0/libgstlibcamera.so

%files qcam
%{_bindir}/qcam
%{_datadir}/applications/qcam.desktop
%{_metainfodir}/qcam.metainfo.xml

%files tools
%license LICENSES/GPL-2.0-only.txt
%{_bindir}/cam
%{_bindir}/libcamera-bug-report

%files v4l2
%{_bindir}/libcamerify
%{_libexecdir}/libcamera/v4l2-compat.so

%files -n python3-%{name}
%{python3_sitearch}/*

%changelog
* Thu Oct 22 2026 mzak <mzak.amin@gmail.com> - 0.7.1-3.iceland_af1
- OnePlus Pad 4: autofocus for the simple pipeline (lens control, soft ISP focus
  metric, contrast-detect AF; continuous by default, LIBCAMERA_SIMPLE_AF_MODE /
  LIBCAMERA_SIMPLE_AF_RANGE)
- the earlier changelog entries are Fedora's: https://src.fedoraproject.org/rpms/libcamera
