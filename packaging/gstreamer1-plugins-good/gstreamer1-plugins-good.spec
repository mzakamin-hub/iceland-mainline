%global         majorminor      1.0

# Only build extras on fedora
%if 0%{?fedora}
%bcond_without extras
%bcond_without nasm
%else
%bcond_with extras
%bcond_with nasm
%endif

# Only build amrnb/amrwbdec on fedora
%if 0%{?fedora}
%bcond_without amr
%else
%bcond_with amr
%endif

# RHEL 10 will provide Qt 6 and drop Qt 5
%if 0%{?rhel} >= 10
%bcond_with qt5
%else
%bcond_without qt5
%endif

%if 0%{?rhel} && 0%{?rhel} < 10
%bcond_with qt6
%else
%bcond_without qt6
%endif

#global gitrel     140
#global gitcommit  9865730cfa5b3a8b2560d082e7e56b350042d3d2
#global shortcommit %(c=%{gitcommit}; echo ${c:0:5})

Name:           gstreamer1-plugins-good
Version:        1.28.8
Release:        1%{?dist}.iceland1
Summary:        GStreamer plugins with good code and licensing

License:        CC0-1.0 AND GPL-2.0-only AND LGPL-2.0-only AND LGPL-2.0-or-later AND LGPL-2.1-only AND LGPL-2.1-or-later AND xlock AND MIT AND BSD-3-Clause AND CC-BY-3.0 
URL:            http://gstreamer.freedesktop.org/

%if 0%{?gitrel}
# git clone git://anogit.freedesktop.org/gstreamer/gst-plugins-good
# cd gst-plugins-good; git reset --hard %{gitcommit}; ./autogen.sh; make; make distcheck
Source0:        gst-plugins-good-%{version}.tar.xz
%else
Source0:        http://gstreamer.freedesktop.org/src/gst-plugins-good/gst-plugins-good-%{version}.tar.xz
%endif

# Register as an AppStream component to be visible in the software center
# NOTE: It would be *awesome* if this file was maintained by the upstream
# project, translated and installed into the right place during `make install`.
# See http://www.freedesktop.org/software/appstream/docs/ for more details.
Source1:        gstreamer-good.appdata.xml

# iceland (OnePlus Pad 4): GStreamer MR !12699 (head a95f1aa304ef), the 1.28 backport of !12602 (merged on main
# 12 Oct 2026): "v4l2object: fix IS_MUTABLE assertion in set_format" + "v4l2object: accept any colorimetry on
# coded OUTPUT caps" (Ben Ashby). The upstream patch as is; -p3 strips the monorepo's subprojects/gst-plugins-good/.
# https://gitlab.freedesktop.org/gstreamer/gstreamer/-/merge_requests/12699
Patch9001:      gst-plugins-good-1.28-mr12699-v4l2-coded-colorimetry.patch

BuildRequires:  meson >= 0.48.0
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  gstreamer1-devel >= %{version}
BuildRequires:  gstreamer1-plugins-base-devel >= %{version}

BuildRequires:  cairo-devel >= 1.10.0
BuildRequires:  cairo-gobject-devel >= 1.10.0
BuildRequires:  flac-devel >= 1.1.4
BuildRequires:  gdk-pixbuf2-devel
BuildRequires:  libjpeg-devel
BuildRequires:  libpng-devel >= 1.2.0
BuildRequires:  libshout-devel
BuildRequires:  libsoup3-devel
BuildRequires:  libX11-devel
BuildRequires:  libXext-devel
BuildRequires:  libXdamage-devel
BuildRequires:  libXfixes-devel
BuildRequires:  pkgconfig(openssl)
BuildRequires:  orc-devel
BuildRequires:  pulseaudio-libs-devel
BuildRequires:  speex-devel
BuildRequires:  taglib-devel
BuildRequires:  wavpack-devel
BuildRequires:  libv4l-devel
BuildRequires:  libvpx-devel >= 1.1.0
BuildRequires:  gtk3-devel >= 3.4
BuildRequires:  mesa-libGL-devel
BuildRequires:  mesa-libGLES-devel
BuildRequires:  mesa-libGLU-devel
BuildRequires:  mesa-libEGL-devel
BuildRequires:  lame-devel
BuildRequires:  mpg123-devel
BuildRequires:  twolame-devel
BuildRequires:  qt6-qtshadertools
%if %{with nasm}
BuildRequires:  nasm
%endif
BuildRequires:  libgudev-devel
%if %{with amr}
BuildRequires:  opencore-amr-devel
%endif

# extras
%if %{with extras}
BuildRequires:  pipewire-jack-audio-connection-kit-devel
%ifnarch s390 s390x
BuildRequires:  libavc1394-devel
BuildRequires:  libdv-devel
BuildRequires:  libiec61883-devel
BuildRequires:  libraw1394-devel
%endif
%endif

# The soup elements dynamically load either version of libsoup at runtime,
# defaulting to libsoup3 if libsoup2 is not already loaded in the process
Recommends:     libsoup3%{?_isa}

# Obsoletes/Provides moved from plugins-bad-free
Obsoletes:      gstreamer1-plugin-mpg123 < 1.13.1
Provides:       gstreamer1-plugin-mpg123 = %{version}-%{release}

%description
GStreamer is a streaming media framework, based on graphs of filters which
operate on media data. Applications using this library can do anything
from real-time sound processing to playing videos, and just about anything
else media-related.  Its plugin-based architecture means that new data
types or processing capabilities can be added simply by installing new
plugins.

GStreamer Good Plugins is a collection of well-supported plugins of
good quality and under the LGPL license.


%package gtk
Summary:         GStreamer "good" plugins gtk plugin
Requires:        %{name}%{?_isa} = %{version}-%{release}
# handle upgrade path
Obsoletes:       gstreamer1-plugins-bad-free-gtk < 1.13.1-2
Provides:        gstreamer1-plugins-bad-free-gtk = %{version}-%{release}
Provides:        gstreamer1-plugins-bad-free-gtk%{?_isa} = %{version}-%{release}

%description gtk
GStreamer is a streaming media framework, based on graphs of elements which
operate on media data.

GStreamer Good Plugins is a collection of well-supported plugins of
good quality and under the LGPL license.

This package (%{name}-gtk) contains the gtksink output plugin.

%if %{with qt5}
%package qt
Summary:         GStreamer "good" plugins qt qml plugin
Requires:        %{name}%{?_isa} = %{version}-%{release}

BuildRequires: pkgconfig(Qt5Gui)
BuildRequires: pkgconfig(Qt5Qml)
BuildRequires: pkgconfig(Qt5Quick)
BuildRequires: pkgconfig(Qt5X11Extras)
BuildRequires: pkgconfig(Qt5WaylandClient)
BuildRequires: qt5-qtbase-private-devel
BuildRequires: qt5-linguist

Supplements: (gstreamer1-plugins-good and qt5-qtdeclarative)

%description qt
GStreamer is a streaming media framework, based on graphs of elements which
operate on media data.

GStreamer Good Plugins is a collection of well-supported plugins of
good quality and under the LGPL license.

This package (%{name}-qt) contains the qtsink output plugin.
%endif

%if %{with qt6}
%package qt6
Summary:         GStreamer "good" plugins qt6 qml plugin
Requires:        %{name}%{?_isa} = %{version}-%{release}

BuildRequires: pkgconfig(Qt6Gui)
BuildRequires: pkgconfig(Qt6Qml)
BuildRequires: pkgconfig(Qt6Quick)
BuildRequires: pkgconfig(Qt6WaylandClient)
BuildRequires: pkgconfig(Qt6Linguist)
BuildRequires: qt6-qtbase-private-devel
BuildRequires: qt6-linguist

Supplements: (gstreamer1-plugins-good and qt6-qtdeclarative)

%description qt6
GStreamer is a streaming media framework, based on graphs of elements which
operate on media data.

GStreamer Good Plugins is a collection of well-supported plugins of
good quality and under the LGPL license.

This package (%{name}-qt6) contains the qml6sink output plugin.
%endif

%if %{with extras}
%package extras
Summary:        Extra GStreamer plugins with good code and licensing
Requires:       %{name}%{?_isa} = %{version}-%{release}


%description extras
GStreamer is a streaming media framework, based on graphs of filters
which operate on media data.

GStreamer Good Plugins is a collection of well-supported plugins of
good quality and under the LGPL license.

%{name}-extras contains extra "good" plugins
which are not used very much and require additional libraries
to be installed.
%endif


%prep
%setup -q -n gst-plugins-good-%{version}
%patch -P 9001 -p3

%build
%meson \
  -D package-name='Fedora GStreamer-plugins-good package' \
  -D package-origin='http://download.fedoraproject.org' \
  -D hls-crypto=openssl \
  -D doc=disabled \
  -D asm=%{?with_nasm:enabled}%{!?with_nasm:disabled} \
  -D doc=disabled \
  -D orc=enabled \
  -D monoscope=disabled \
  -D aalib=disabled \
  -D libcaca=disabled \
  -D rpicamsrc=disabled \
  -D amrnb=%{?with_amr:enabled}%{!?with_amr:disabled} \
  -D amrwbdec=%{?with_amr:enabled}%{!?with_amr:disabled} \
  -D jack=%{?with_extras:enabled}%{!?with_extras:disabled} \
%ifarch s390 s390x
  -D dv=disabled -D dv1394=disabled \
%else
  -D dv=%{?with_extras:enabled}%{!?with_extras:disabled} \
  -D dv1394=%{?with_extras:enabled}%{!?with_extras:disabled} \
%endif
%if 0%{?flatpak_runtime}
  -D v4l2-gudev=disabled \
%endif
  -D qt-egl=disabled \
  -D qt5=%{?with_qt5:enabled}%{!?with_qt5:disabled} \
  -D qt6=%{?with_qt6:enabled}%{!?with_qt6:disabled}

%meson_build

%install
%meson_install

install -p -D %{SOURCE1} %{buildroot}%{_metainfodir}/gstreamer-good.appdata.xml

find $RPM_BUILD_ROOT -name '*.la' -exec rm -fv {} ';'

%find_lang gst-plugins-good-%{majorminor}

%files -f gst-plugins-good-%{majorminor}.lang
%license COPYING
%doc README.md README.static-linking RELEASE
%{_metainfodir}/gstreamer-good.appdata.xml
%if 0
%doc %{_datadir}/gtk-doc/html/gst-plugins-good-plugins-%{majorminor}
%endif

# presets
%dir %{_datadir}/gstreamer-%{majorminor}/presets/
%{_datadir}/gstreamer-%{majorminor}/presets/GstVP8Enc.prs
%{_datadir}/gstreamer-%{majorminor}/presets/GstIirEqualizer10Bands.prs
%{_datadir}/gstreamer-%{majorminor}/presets/GstIirEqualizer3Bands.prs
%{_datadir}/gstreamer-%{majorminor}/presets/GstQTMux.prs

# non-core plugins without external dependencies
%{_libdir}/gstreamer-%{majorminor}/libgstadaptivedemux2.so
%{_libdir}/gstreamer-%{majorminor}/libgstalaw.so
%{_libdir}/gstreamer-%{majorminor}/libgstalphacolor.so
%{_libdir}/gstreamer-%{majorminor}/libgstalpha.so
%{_libdir}/gstreamer-%{majorminor}/libgstapetag.so
%{_libdir}/gstreamer-%{majorminor}/libgstaudiofx.so
%{_libdir}/gstreamer-%{majorminor}/libgstaudioparsers.so
%{_libdir}/gstreamer-%{majorminor}/libgstauparse.so
%{_libdir}/gstreamer-%{majorminor}/libgstautodetect.so
%{_libdir}/gstreamer-%{majorminor}/libgstavi.so
%{_libdir}/gstreamer-%{majorminor}/libgstcutter.so
%{_libdir}/gstreamer-%{majorminor}/libgstdebug.so
%{_libdir}/gstreamer-%{majorminor}/libgstdeinterlace.so
%{_libdir}/gstreamer-%{majorminor}/libgstdtmf.so
%{_libdir}/gstreamer-%{majorminor}/libgsteffectv.so
%{_libdir}/gstreamer-%{majorminor}/libgstequalizer.so
%{_libdir}/gstreamer-%{majorminor}/libgstflv.so
%{_libdir}/gstreamer-%{majorminor}/libgstflxdec.so
%{_libdir}/gstreamer-%{majorminor}/libgstgoom2k1.so
%{_libdir}/gstreamer-%{majorminor}/libgstgoom.so
%{_libdir}/gstreamer-%{majorminor}/libgsticydemux.so
%{_libdir}/gstreamer-%{majorminor}/libgstid3demux.so
%{_libdir}/gstreamer-%{majorminor}/libgstimagefreeze.so
%{_libdir}/gstreamer-%{majorminor}/libgstinterleave.so
%{_libdir}/gstreamer-%{majorminor}/libgstisomp4.so
%{_libdir}/gstreamer-%{majorminor}/libgstlevel.so
%{_libdir}/gstreamer-%{majorminor}/libgstmatroska.so
%{_libdir}/gstreamer-%{majorminor}/libgstmulaw.so
%{_libdir}/gstreamer-%{majorminor}/libgstmultifile.so
%{_libdir}/gstreamer-%{majorminor}/libgstmultipart.so
%{_libdir}/gstreamer-%{majorminor}/libgstnavigationtest.so
%{_libdir}/gstreamer-%{majorminor}/libgstoss4.so
%{_libdir}/gstreamer-%{majorminor}/libgstreplaygain.so
%{_libdir}/gstreamer-%{majorminor}/libgstrtp.so
%{_libdir}/gstreamer-%{majorminor}/libgstrtsp.so
%{_libdir}/gstreamer-%{majorminor}/libgstshapewipe.so
%{_libdir}/gstreamer-%{majorminor}/libgstsmpte.so
%{_libdir}/gstreamer-%{majorminor}/libgstspectrum.so
%{_libdir}/gstreamer-%{majorminor}/libgstudp.so
%{_libdir}/gstreamer-%{majorminor}/libgstvideobox.so
%{_libdir}/gstreamer-%{majorminor}/libgstvideocrop.so
%{_libdir}/gstreamer-%{majorminor}/libgstvideofilter.so
%{_libdir}/gstreamer-%{majorminor}/libgstvideomixer.so
%{_libdir}/gstreamer-%{majorminor}/libgstwavenc.so
%{_libdir}/gstreamer-%{majorminor}/libgstwavparse.so
%{_libdir}/gstreamer-%{majorminor}/libgstximagesrc.so
%{_libdir}/gstreamer-%{majorminor}/libgstxingmux.so
%{_libdir}/gstreamer-%{majorminor}/libgsty4m.so

# gstreamer-plugins with external dependencies but in the main package
%{_libdir}/gstreamer-%{majorminor}/libgstcairo.so
%{_libdir}/gstreamer-%{majorminor}/libgstflac.so
%{_libdir}/gstreamer-%{majorminor}/libgstgdkpixbuf.so
%{_libdir}/gstreamer-%{majorminor}/libgstjpeg.so
%{_libdir}/gstreamer-%{majorminor}/libgstossaudio.so
%{_libdir}/gstreamer-%{majorminor}/libgstpng.so
%{_libdir}/gstreamer-%{majorminor}/libgstpulseaudio.so
%{_libdir}/gstreamer-%{majorminor}/libgstrtpmanager.so
%{_libdir}/gstreamer-%{majorminor}/libgstshout2.so
%{_libdir}/gstreamer-%{majorminor}/libgstsoup.so
%{_libdir}/gstreamer-%{majorminor}/libgstspeex.so
%{_libdir}/gstreamer-%{majorminor}/libgsttaglib.so
%{_libdir}/gstreamer-%{majorminor}/libgstvideo4linux2.so
%{_libdir}/gstreamer-%{majorminor}/libgstvpx.so
%{_libdir}/gstreamer-%{majorminor}/libgstwavpack.so
%{_libdir}/gstreamer-%{majorminor}/libgstlame.so
%{_libdir}/gstreamer-%{majorminor}/libgstmpg123.so
%{_libdir}/gstreamer-%{majorminor}/libgsttwolame.so

%if %{with amr}
%{_libdir}/gstreamer-%{majorminor}/libgstamrnb.so
%{_libdir}/gstreamer-%{majorminor}/libgstamrwbdec.so
%{_datadir}/gstreamer-%{majorminor}/presets/GstAmrnbEnc.prs
%endif

%files gtk
# Plugins with external dependencies
%{_libdir}/gstreamer-%{majorminor}/libgstgtk.so

%if %{with qt5}
%files qt
%{_libdir}/gstreamer-%{majorminor}/libgstqmlgl.so
%endif

%if %{with qt6}
%files qt6
%{_libdir}/gstreamer-%{majorminor}/libgstqml6.so
%endif

%if %{with extras}
%files extras
# Plugins with external dependencies
%{_libdir}/gstreamer-%{majorminor}/libgstjack.so
%ifnarch s390 s390x
%{_libdir}/gstreamer-%{majorminor}/libgstdv.so
%{_libdir}/gstreamer-%{majorminor}/libgst1394.so
%endif
%endif


%changelog
* Mon Oct 19 2026 mzak <mzak.amin@gmail.com> - 1.28.8-1.iceland1
- v4l2: accept any colorimetry on coded OUTPUT caps (GStreamer MR !12699, the
  1.28 backport of !12602): SD BT.601 (2:4:5:4) and partially signalled H.264 /
  HEVC streams negotiate on V4L2 stateful decoders (Iris on the OnePlus Pad 4)
  instead of failing; also fixes the IS_MUTABLE assertion in set_format
- the earlier changelog entries are Fedora's: https://src.fedoraproject.org/rpms/gstreamer1-plugins-good
