# SPDX-License-Identifier: GPL-2.0-or-later
%global commit 9852479288b088699ae0c0b4c848dbda58bf7391
%global shortcommit 9852479
%global commitdate 20261023

Name:           iris-vaapi
Version:        0.2.0^%{commitdate}git%{shortcommit}
Release:        1.iceland1%{?dist}
Summary:        VA-API decode driver for the Qualcomm Iris V4L2 video decoder
License:        GPL-2.0-or-later
URL:            https://github.com/CFM880/iris-vaapi
# git archive --prefix=iris-vaapi-%%{commit}/ %%{commit} | gzip -n (upstream has no release tarballs)
Source0:        iris-vaapi-%{shortcommit}.tar.gz
Source1:        55-iris-vaapi.conf
Source2:        70-iris-vaapi-dmaheap.rules
Source3:        iris-vaapi-modprobe.conf
Source4:        56-iris-vaapi-chromium.conf
Source5:        README.iceland
# Re-implemented for HFI gen2 (SM8750 / SM8850) after TheMojoMan's erhai port notes (oneplus-erhai-ubuntu)
Patch1:         0001-decode-skip-capture-pictures-without-a-client-timest.patch
Patch2:         0002-vaapi-report-YUV420-for-the-10-bit-profiles-too.patch

ExclusiveArch:  aarch64
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconfig(libva)
BuildRequires:  pkgconfig(vulkan)
Requires:       libva
Requires(post): systemd-udev
Recommends:     libva-utils

%description
iris-vaapi (upstream name vpu-vaapi) is a VA-API driver that passes the
parameters and slices of VA-API clients (Chromium, FFmpeg, mpv) as complete
access units to the stateful Qualcomm Iris V4L2 decoder (qcom_iris).
Profiles: H.264 Constrained Baseline / Main / High, HEVC Main / Main10,
VP9 profile 0 / 2.

This build installs the driver as vpu_drv_video.so and as iris_drv_video.so,
sets LIBVA_DRIVER_NAME=iris for user sessions, lets the video group and the
active seat user allocate from /dev/dma_heap/system (0660 root:video plus a
logind ACL), and turns on the decode-order output that the driver needs in
the iceland kernel's qcom_iris module (decode_order_output=1).

%package chromium
Summary:        Chromium hardware video decode flags for the Qualcomm Iris decoder
Requires:       %{name} = %{version}-%{release}
Supplements:    (%{name} and chromium)

%description chromium
Sets CHROMIUM_FLAGS for user sessions (Fedora's chromium wrapper passes it;
a user's CHROMIUM_USER_FLAGS still replaces it): AcceleratedVideoDecoder,
the Linux hardware-decode gate, and VaapiVideoDecoder. Fedora 44's aarch64
chromium is built without VA-API (use_vaapi=0, use_v4l2_codec=1): it decodes
through the Iris V4L2 node directly and needs only the first feature; the
second one matters for VA-API builds (Chrome, Electron) that read this
variable through a wrapper.

%package tests
Summary:        Hardware test programs of iris-vaapi
Requires:       %{name} = %{version}-%{release}

%description tests
Upstream's VA-API hardware tests in %{_libexecdir}/iris-vaapi: test_va
(driver profiles and entrypoints, a vainfo stand-in), test_va_decode (first
H.264 picture), test_va_stress (pipelined H.264 decode as Chromium does it,
input.h264 [frame-count]) and test_va_vp9.

%prep
%autosetup -p1 -n iris-vaapi-%{commit}
cp -p %{SOURCE5} .

%build
%make_build CC=gcc CFLAGS="%{optflags}" LDFLAGS="%{build_ldflags}" build/vpu_drv_video.so 	build/test_va build/test_va_decode build/test_va_stress build/test_va_vp9

%check
# upstream's hardware-independent unit tests (H.264 / HEVC parsers, slice rewrite, platform, codec, VP9, surfaces)
make CC=gcc CFLAGS="%{optflags}" LDFLAGS="%{build_ldflags}" check

%install
install -D -m 0755 build/vpu_drv_video.so %{buildroot}%{_libdir}/dri/vpu_drv_video.so
ln -s vpu_drv_video.so %{buildroot}%{_libdir}/dri/iris_drv_video.so
install -D -m 0644 %{SOURCE1} %{buildroot}%{_prefix}/lib/environment.d/55-iris-vaapi.conf
install -D -m 0644 %{SOURCE2} %{buildroot}%{_udevrulesdir}/70-iris-vaapi-dmaheap.rules
install -D -m 0644 %{SOURCE3} %{buildroot}%{_prefix}/lib/modprobe.d/iris-vaapi.conf
install -D -m 0644 %{SOURCE4} %{buildroot}%{_prefix}/lib/environment.d/56-iris-vaapi-chromium.conf
for t in test_va test_va_decode test_va_stress test_va_vp9; do
  install -D -m 0755 build/$t %{buildroot}%{_libexecdir}/iris-vaapi/$t
done

%post
# the running system: dma-heap mode / ACL now, decode order for the next decoder session (the parameter is read
# when an instance is opened); a kernel without the parameter keeps its behaviour
udevadm control --reload-rules >/dev/null 2>&1 || :
udevadm trigger --subsystem-match=dma_heap --action=change >/dev/null 2>&1 || :
p=/sys/module/qcom_iris/parameters/decode_order_output
[ -w $p ] && echo Y > $p 2>/dev/null || :

%postun
if [ $1 -eq 0 ]; then
  udevadm control --reload-rules >/dev/null 2>&1 || :
  udevadm trigger --subsystem-match=dma_heap --action=change >/dev/null 2>&1 || :
  p=/sys/module/qcom_iris/parameters/decode_order_output
  [ -w $p ] && echo N > $p 2>/dev/null || :
fi

%files
%license COPYING
%doc README.md README.iceland docs/chromium-integration.md
%{_libdir}/dri/vpu_drv_video.so
%{_libdir}/dri/iris_drv_video.so
%{_prefix}/lib/environment.d/55-iris-vaapi.conf
%{_udevrulesdir}/70-iris-vaapi-dmaheap.rules
%{_prefix}/lib/modprobe.d/iris-vaapi.conf

%files chromium
%{_prefix}/lib/environment.d/56-iris-vaapi-chromium.conf

%files tests
%dir %{_libexecdir}/iris-vaapi
%{_libexecdir}/iris-vaapi/test_va
%{_libexecdir}/iris-vaapi/test_va_decode
%{_libexecdir}/iris-vaapi/test_va_stress
%{_libexecdir}/iris-vaapi/test_va_vp9

%changelog
* Mon Oct 26 2026 mzak <mzak.amin@gmail.com> - 0.2.0^20261023git9852479-1.iceland1
- First package for the OnePlus Pad 4 (SM8850, iceland): upstream 9852479 (0.2.0)
- Skip CAPTURE pictures without a client timestamp instead of failing the session, and report YUV420 for the
  10-bit profiles too (re-implemented after TheMojoMan's erhai port notes)
- dma-heap 0660 root:video + uaccess, LIBVA_DRIVER_NAME=iris, qcom_iris decode_order_output=1, Chromium flags
  and hardware tests subpackages
