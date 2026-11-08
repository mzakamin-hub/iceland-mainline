%ifnarch s390x
%global with_hardware 1
%global with_kmsro 1
%global with_radeonsi 1
%global with_spirv_tools 1
%global with_vmware 1
%global with_vulkan_hw 1
%if !0%{?rhel}
%global with_r300 1
%global with_r600 1
%global with_opencl 1
%global with_va 1
%endif
%if !0%{?rhel} || 0%{?rhel} >= 9
%global with_nvk %{with_vulkan_hw}
%endif
%global base_vulkan %{?with_vulkan_hw:,amd}%{!?with_vulkan_hw:%{nil}}
%endif

%ifarch aarch64 x86_64
%if !0%{?rhel}
%global with_teflon 1
%endif
%endif

%ifarch %{ix86} x86_64
%global with_crocus 1
%global with_iris   1
%global intel_platform_vulkan %{?with_vulkan_hw:,intel,intel_hasvk}%{!?with_vulkan_hw:%{nil}}
%if !0%{?rhel}
%global with_i915   1
%endif
%endif
%ifarch x86_64
%if 0%{?with_vulkan_hw}
%global with_intel_vk_rt 1
%endif
%endif

%ifarch aarch64 x86_64 %{ix86}
%if !0%{?rhel}
%global with_asahi     1
%global with_d3d12     1
%global with_etnaviv   1
%global with_lima      1
%global with_tegra     1
%global with_vc4       1
%global with_v3d       1
%endif
%global with_freedreno 1
%global with_panfrost  1
%if 0%{?with_asahi}
%global asahi_platform_vulkan %{?with_vulkan_hw:,asahi}%{!?with_vulkan_hw:%{nil}}
%endif
%global extra_platform_vulkan %{?with_vulkan_hw:,broadcom,freedreno,panfrost,imagination}%{!?with_vulkan_hw:%{nil}}
%endif

%if !0%{?rhel}
%global with_libunwind 1
%global with_lmsensors 1
%global with_virtio    1
# iceland: Mesa 26.3 removed the anti-lag Vulkan layer (meson option and src/vulkan/anti-lag-layer gone)
# %%global with_vulkan_layers_anti_lag 1
%endif

%ifarch %{valgrind_arches}
%bcond_without valgrind
%else
%bcond_with valgrind
%endif

%global vulkan_drivers swrast%{?base_vulkan}%{?intel_platform_vulkan}%{?asahi_platform_vulkan}%{?extra_platform_vulkan}%{?with_nvk:,nouveau}%{?with_virtio:,virtio}%{?with_d3d12:,microsoft-experimental}

%if 0%{?with_nvk} && 0%{?rhel}
%global vendor_nvk_crates 1
%endif

# We've gotten a report that enabling LTO for mesa breaks some games. See
# https://bugzilla.redhat.com/show_bug.cgi?id=1862771 for details.
# Disable LTO for now
%global _lto_cflags %nil

Name:           mesa
Summary:        Mesa graphics libraries
# iceland (OnePlus Pad 4, Adreno 840 / gen8): Fedora 45's mesa.spec (dist-git f45 13d08919, 26.2.6) with the
# version, the source and the patches changed; one build option added (-Dfreedreno-kmds=msm,virtio, see %%build).
# Base: Mesa staging/26.3 at 25248e6d (2026-11-04) = 26.3.0-rc3 + 137 commits (26.3.0 not tagged yet).
# 26.3.0~rc3^git... sorts above 26.3.0~rc3 and the earlier 26.3.0~rc1~git20261019.e282ea8c iceland builds and
# below the 26.3.0 release. ".iceland1" marks the local build.
Version:        26.3.0~rc3^git20261104.25248e6
Release:        1%{?dist}.iceland1
License:        MIT AND BSD-3-Clause AND SGI-B-2.0
URL:            https://mesa3d.org

# The "Version" field for release candidates has the format: A.B.C~rcX
# However, the tarball has the format: A.B.C-rcX.
# The "ver" variable contains the version in the second format.
# iceland: written out for the snapshot ('^' is a pattern anchor in %%gsub); keep in step with Version
%global ver 26.3.0-rc3-git20261104.25248e6

# iceland: "git archive --prefix=mesa-%%{ver}/" of staging/26.3 at 25248e6de63639c3d3258abb7b3b1c9b0fd66e65
# (https://gitlab.freedesktop.org/mesa/mesa.git), xz -9
Source0:        mesa-%{ver}.tar.xz
# src/gallium/auxiliary/postprocess/pp_mlaa* have an ... interestingly worded license.
# Source1 contains email correspondence clarifying the license terms.
# Fedora opts to ignore the optional part of clause 2 and treat that code as 2 clause BSD.
Source1:        Mesa-MLAA-License-Clarification-Email.txt
# iceland: 26.3 needs venus-protocol 1.1.3 (subprojects/venus-protocol.wrap is a wrap-git) for the virtio Vulkan
# driver; a git archive does not bundle it and %%meson does not download wraps. Unpacked in %%prep.
%global venus_protocol_ver 1.1.3
Source2:        https://gitlab.freedesktop.org/virgl/venus-protocol/-/archive/v%{venus_protocol_ver}/venus-protocol-v%{venus_protocol_ver}.tar.gz

# In CentOS/RHEL, Rust crates required to build NVK are vendored.
# The minimum target versions are obtained from the .wrap files
# https://gitlab.freedesktop.org/mesa/mesa/-/tree/main/subprojects
# but we generally want the latest compatible versions
%global rust_paste_ver 1.0.15
%global rust_proc_macro2_ver 1.0.107
%global rust_quote_ver 1.0.47
%global rust_syn_ver 2.0.119
%global rust_unicode_ident_ver 1.0.26
%global rustc_hash_ver 2.1.3
Source10:       https://crates.io/api/v1/crates/paste/%{rust_paste_ver}/download#/paste-%{rust_paste_ver}.tar.gz
Source11:       https://crates.io/api/v1/crates/proc-macro2/%{rust_proc_macro2_ver}/download#/proc-macro2-%{rust_proc_macro2_ver}.tar.gz
Source12:       https://crates.io/api/v1/crates/quote/%{rust_quote_ver}/download#/quote-%{rust_quote_ver}.tar.gz
Source13:       https://crates.io/api/v1/crates/syn/%{rust_syn_ver}/download#/syn-%{rust_syn_ver}.tar.gz
Source14:       https://crates.io/api/v1/crates/unicode-ident/%{rust_unicode_ident_ver}/download#/unicode-ident-%{rust_unicode_ident_ver}.tar.gz
Source15:       https://crates.io/api/v1/crates/rustc-hash/%{rustc_hash_ver}/download#/rustc-hash-%{rustc_hash_ver}.tar.gz

# iceland: Adreno 840 (a8xx / gen8) and shared ir3 / turnip / freedreno work not in staging/26.3 (2026-11-07):
# one file per merge request, "git format-patch" of the commits as applied in this order on 25248e6d (merged
# MRs: the commits as merged on main; open MRs: the MR head). Authors and messages kept. All apply with
# patch -p1 --fuzz=0 in this order. Drop a patch once its MR is in the 26.3.x tag being built.
# -- merged on main, not in 26.3 --
# !45525 (open, the 26.3 backport of !44352, merged on main 22 Oct): tu/a8xx split large indirect (count) draws -
#   large indirect draws fault on A8xx (was 9001)
Patch9101:      9101-mr45525-26-3-backport-tu-a8xx-split-large-indirect-draws.patch
# !45369: tu drop the BO reference taken by get_vis_stream_patchpoint_cs() - BO leak per command buffer (was 9003)
Patch9102:      9102-mr45369-tu-drop-reference-taken-with-get-vis-stream-patc.patch
# !45366: tu float16 3D path for multisampled copies (was 9004)
Patch9103:      9103-mr45366-tu-add-back-float16-3d-path-for-multisampled-cop.patch
# !45416: tu / freedreno hull shader programming (tessellation; was 9010)
Patch9104:      9104-mr45416-tu-freedreno-modify-hull-shader-programming.patch
# !45342: tu 4x8 integer dot products reported as accelerated (dp4acc; llama.cpp int-dot kernels; was 9009)
Patch9105:      9105-mr45342-tu-mark-signed-4x8-integer-dot-products-as-accel.patch
# !45554: freedreno record the batch's write when a query ends (was 9011)
Patch9106:      9106-mr45554-freedreno-record-the-batch-s-write-when-a-query.patch
# !45506: tu GL behaviour for the primitives-generated query (zink; was 9012)
Patch9107:      9107-mr45506-tu-have-gl-behavior-for-primitive-generated-quer.patch
# !45464: ir3 source-modifier copy propagation + the IR3_REG_BNOT flags fix (replaces the closed !45434 ashr.b
#   miscompile fix); its tu/ci trace-checksum commit left out
Patch9108:      9108-mr45464-ir3-better-copy-prop-for-source-modifiers.patch
# !45517: ir3/ra DOUBLE_ONLY register limit unit
Patch9109:      9109-mr45517-ir3-ra-fix-double-only-register-limit-unit.patch
# !45559: vulkan runtime / tu (+ radv, lavapipe) per-binding pNext data in pBindings order
Patch9110:      9110-mr45559-vulkan-sort-per-binding-pnext-data-in-vk-create.patch
# !45601: tu software multiview with indirect draws; freedreno OpenCL subgroup size (CI-expectation commit left out)
Patch9111:      9111-mr45601-tu-ir3-fix-a702-regressions.patch
# !43899: tu drop the CCU depth invalidation on occlusion query end (the merged version; was 9007, an earlier MR
#   head); its src/freedreno/ci/freedreno-a750-fails.txt hunk left out
Patch9112:      9112-mr43899-turnip-drop-ccu-depth-invalidation-on-occlusion.patch
# !45882: freedreno take only the in-fence as the explicit-sync hint (flicker / corruption)
Patch9113:      9113-mr45882-freedreno-take-only-in-fence-as-a-hint-for-expli.patch
# !45918: tu/lrz A8XX LRZ pitch alignment 32 + partial LRZ fast-clear fix (gen8 rendering corruption)
Patch9114:      9114-mr45918-tu-lrz-fix-partial-lrz-fast-clear-on-a8xx.patch
# !45981: ir3 OpQuantizeToF16 flushes FP16 subnormals
Patch9115:      9115-mr45981-freedreno-ir3-lower-fp32-to-fp16-for-subnormals.patch
# !46027: ir3 fold fsat into (sat) only on cat2/3 float instructions (miscompile)
Patch9116:      9116-mr46027-ir3-only-fold-fsat-to-sat-on-cat2-3-float-instru.patch
# -- open merge requests (MR heads of 2026-11-07) --
# !45243: tu inline uniform block fixes (was 9005)
Patch9117:      9117-mr45243-tu-inline-uniform-block-fixes.patch
# !44365: nir/ir3 32-bit udiv wrong quotient when rcp rounds up (seen on a830 / gen8; was 9006)
Patch9118:      9118-mr44365-nir-ir3-fix-32-bit-udiv-when-rcp-rounds-up.patch
# !45937: tu WFI before reading just-written registers (A8XX: all register-read packets; multisample CTS)
Patch9119:      9119-mr45937-tu-wfi-before-reading-registers-that-were-just-w.patch
# !45985: tu carry flush bits for suspend/resume chains split over command buffers
Patch9120:      9120-mr45985-tu-carry-flush-bits-for-suspended-s-r-chains-bet.patch
# !45926: tu wait for VM_BIND unmap completion before freeing (msm VM_BIND memory churn)
Patch9121:      9121-mr45926-tu-wait-for-vm-bind-unmap-completion-before-free.patch
# !45904: tu sample counts across GMEM preemption (occlusion queries / autotune with preemption on)
Patch9122:      9122-mr45904-tu-preserve-sample-counts-across-gmem-preemption.patch
# !45928: ir3 merge_sets_interfere per-set dominance stacks (pipeline compile time)
Patch9123:      9123-mr45928-ir3-keep-separate-dominance-stacks-in-merge-sets.patch
# !46023: ir3 is_{ss,sy}_producer fixes and their use in legalize (local atomics sync)
Patch9124:      9124-mr46023-ir3-fix-is-ss-sy-producer-and-use-in-legalize.patch
# !45958: freedreno/ir3 api_wavesize DOUBLE_ONLY for GL non-compute shaders on gen6+ (GPU hang in subgroup tests)
Patch9125:      9125-mr45958-freedreno-ir3-set-api-wavesize-double-only-for-g.patch
# !45727: dri / freedreno round up the NV12 chroma plane (odd sizes, UBWC layout = display / video)
Patch9126:      9126-mr45727-freedreno-round-up-the-nv12-chroma-plane-size.patch
# -- general freedreno / turnip / ir3 performance + correctness (open MRs, owner request 7 Nov) --
# !44712: ir3/lower_copies keep partially blocked copies whole (author: -6.47% instrs on the affected shaders)
Patch9127:      9127-mr44712-ir3-lower-copies-don-t-split-partially-blocked-c.patch
# !37924: ir3 opt_absneg pass (author: -0.35% code size on 5% of shaders)
Patch9128:      9128-mr37924-ir3-add-opt-absneg-pass.patch
# !43714: tu no flush for sysmem resolves when there are no resolve attachments (dynamic rendering over-flush)
Patch9129:      9129-mr43714-tu-don-t-flush-for-sysmem-resolves-if-there-are.patch
# !43272: tu synchronize no-rast-order and rast-order draws (VK_EXT_rasterization_order_attachment_access)
Patch9130:      9130-mr43272-tu-synchronize-access-between-no-rast-order-and.patch

BuildRequires:  meson >= 1.3.0
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  gettext
%if 0%{?with_hardware}
BuildRequires:  kernel-headers
BuildRequires:  systemd-devel
%endif
# We only check for the minimum version of pkgconfig(libdrm) needed so that the
# SRPMs for each arch still have the same build dependencies. See:
# https://bugzilla.redhat.com/show_bug.cgi?id=1859515
BuildRequires:  pkgconfig(libdrm) >= 2.4.133
%if 0%{?with_libunwind}
BuildRequires:  pkgconfig(libunwind)
%endif
BuildRequires:  pkgconfig(expat)
BuildRequires:  pkgconfig(zlib) >= 1.2.3
BuildRequires:  pkgconfig(libzstd)
BuildRequires:  pkgconfig(wayland-scanner)
BuildRequires:  pkgconfig(wayland-protocols) >= 1.41
BuildRequires:  pkgconfig(wayland-client) >= 1.11
BuildRequires:  pkgconfig(wayland-server) >= 1.11
BuildRequires:  pkgconfig(wayland-egl-backend) >= 3
BuildRequires:  pkgconfig(libdisplay-info)
BuildRequires:  pkgconfig(x11)
BuildRequires:  pkgconfig(xext)
BuildRequires:  pkgconfig(xdamage) >= 1.1
BuildRequires:  pkgconfig(xfixes)
BuildRequires:  pkgconfig(xcb-glx) >= 1.8.1
BuildRequires:  pkgconfig(xxf86vm)
BuildRequires:  pkgconfig(xcb)
BuildRequires:  pkgconfig(x11-xcb)
BuildRequires:  pkgconfig(xcb-dri2) >= 1.8
BuildRequires:  pkgconfig(xcb-dri3)
BuildRequires:  pkgconfig(xcb-present)
BuildRequires:  pkgconfig(xcb-sync)
BuildRequires:  pkgconfig(xshmfence) >= 1.1
BuildRequires:  pkgconfig(dri2proto) >= 2.8
BuildRequires:  pkgconfig(glproto) >= 1.4.14
BuildRequires:  pkgconfig(xcb-xfixes)
BuildRequires:  pkgconfig(xcb-randr)
BuildRequires:  pkgconfig(xrandr) >= 1.3
BuildRequires:  bison
BuildRequires:  flex
%if 0%{?with_lmsensors}
BuildRequires:  lm_sensors-devel
%endif
%if 0%{?with_va}
BuildRequires:  pkgconfig(libva) >= 0.38.0
%endif
BuildRequires:  pkgconfig(libelf)
BuildRequires:  pkgconfig(libglvnd) >= 1.3.2
BuildRequires:  llvm-devel >= 7.0.0
%if 0%{?with_teflon}
BuildRequires:  flatbuffers-devel
BuildRequires:  flatbuffers-compiler
BuildRequires:  xtensor-devel
%endif
%if 0%{?with_opencl} || 0%{?with_nvk} || 0%{?with_asahi} || 0%{?with_panfrost}
BuildRequires:  clang-devel
BuildRequires:  pkgconfig(libclc)
BuildRequires:  pkgconfig(SPIRV-Tools)
BuildRequires:  pkgconfig(LLVMSPIRVLib)
%endif
%if 0%{?with_opencl} || 0%{?with_nvk}
BuildRequires:  bindgen
%if 0%{?rhel}
BuildRequires:  rust-toolset
%else
BuildRequires:  cargo-rpm-macros
%endif
%endif
%if 0%{?with_opencl}
BuildRequires:  libstdc++-static
%endif
%if 0%{?with_nvk}
BuildRequires:  cbindgen
%endif
%if %{with valgrind}
BuildRequires:  pkgconfig(valgrind)
%endif
BuildRequires:  python3-devel
BuildRequires:  python3-mako
BuildRequires:  python3-pycparser
BuildRequires:  python3-pyyaml
BuildRequires:  vulkan-headers
BuildRequires:  glslang
%if 0%{?with_vulkan_hw}
BuildRequires:  pkgconfig(vulkan)
%endif
%if 0%{?with_d3d12}
BuildRequires:  pkgconfig(DirectX-Headers) >= 1.619.1
%endif

%description
%{summary}.

%package filesystem
Summary:        Mesa driver filesystem
Provides:       mesa-dri-filesystem = %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      mesa-omx-drivers < %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      mesa-libd3d < %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      mesa-libd3d-devel < %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      mesa-vdpau-drivers < %{?epoch:%{epoch}:}%{version}-%{release}

%description filesystem
%{summary}.

%package libGL
Summary:        Mesa libGL runtime libraries
Requires:       libglvnd-glx%{?_isa} >= 1:1.3.2
Requires:       %{name}-dri-drivers%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      %{name}-libOSMesa < 25.1.0~rc2-1

%description libGL
%{summary}.

%package libGL-devel
Summary:        Mesa libGL development package
Requires:       (%{name}-libGL%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release} if %{name}-libGL%{?_isa})
Requires:       libglvnd-devel%{?_isa} >= 1:1.3.2
Provides:       libGL-devel = %{?epoch:%{epoch}:}%{version}-%{release}
Provides:       libGL-devel%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Recommends:     gl-manpages
Obsoletes:      %{name}-libOSMesa-devel < 25.1.0~rc2-1

%description libGL-devel
%{summary}.

%package libEGL
Summary:        Mesa libEGL runtime libraries
Requires:       libglvnd-egl%{?_isa} >= 1:1.3.2
Requires:       %{name}-libgbm%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       %{name}-dri-drivers%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description libEGL
%{summary}.

%package libEGL-devel
Summary:        Mesa libEGL development package
Requires:       (%{name}-libEGL%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release} if %{name}-libEGL%{?_isa})
Requires:       libglvnd-devel%{?_isa} >= 1:1.3.2
Requires:       %{name}-khr-devel%{?_isa}
Provides:       libEGL-devel = %{?epoch:%{epoch}:}%{version}-%{release}
Provides:       libEGL-devel%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description libEGL-devel
%{summary}.

%package dri-drivers
Summary:        Mesa-based DRI drivers
Requires:       %{name}-filesystem%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       %{name}-libgbm%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      %{name}-libglapi < 25.0.0~rc2-1
Obsoletes:      %{name}-va-drivers < 26.0.0-5
Provides:       %{name}-va-drivers = %{?epoch:%{epoch}:}%{version}-%{release}
Provides:       %{name}-va-drivers%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      %{name}-vaapi-drivers < 22.2.0-5

%description dri-drivers
%{summary}.

%package libgbm
Summary:        Mesa gbm runtime library
Provides:       libgbm = %{?epoch:%{epoch}:}%{version}-%{release}
Provides:       libgbm%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Recommends:     %{name}-dri-drivers%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
# If mesa-dri-drivers are installed, they must match in version. This is here to prevent using
# older mesa-dri-drivers together with a newer mesa-libgbm and its dependants.
# See https://bugzilla.redhat.com/show_bug.cgi?id=2193135 .
Requires:       (%{name}-dri-drivers%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release} if %{name}-dri-drivers%{?_isa})

%description libgbm
%{summary}.

%package libgbm-devel
Summary:        Mesa libgbm development package
Requires:       %{name}-libgbm%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Provides:       libgbm-devel = %{?epoch:%{epoch}:}%{version}-%{release}
Provides:       libgbm-devel%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description libgbm-devel
%{summary}.

%if 0%{?with_opencl}
%package libOpenCL
Summary:        Mesa OpenCL runtime library
Requires:       (ocl-icd%{?_isa} or OpenCL-ICD-Loader%{?_isa})
# iceland: f44 variant of the same spec: Fedora 44's spec requires plain libclc
%if 0%{?fedora} >= 45
Requires:       libclc22%{?_isa}
%else
Requires:       libclc%{?_isa}
%endif
Requires:       %{name}-libgbm%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       opencl-filesystem

%description libOpenCL
%{summary}.

%package libOpenCL-devel
Summary:        Mesa OpenCL development package
Requires:       %{name}-libOpenCL%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description libOpenCL-devel
%{summary}.
%endif

%if 0%{?with_teflon}
%package libTeflon
Summary:        Mesa TensorFlow Lite delegate

%description libTeflon
%{summary}.
%endif

%if 0%{?with_d3d12}
%package dxil-devel
Summary:        Mesa SPIR-V to DXIL binary
Requires:       %{name}-filesystem%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description dxil-devel
Development tools for translating SPIR-V shader code to DXIL for Direct3D 12
%endif

%package vulkan-drivers
Summary:        Mesa Vulkan drivers
Requires:       vulkan%{_isa}
Requires:       %{name}-filesystem%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      mesa-vulkan-devel < %{?epoch:%{epoch}:}%{version}-%{release}
Obsoletes:      VK_hdr_layer < 1

%description vulkan-drivers
The drivers with support for the Vulkan API.

%prep
%autosetup -n %{name}-%{ver} -p1
cp %{SOURCE1} docs/
# iceland: venus-protocol for the virtio Vulkan driver (see Source2)
mkdir -p subprojects/venus-protocol-%{venus_protocol_ver}
tar -xzf %{SOURCE2} -C subprojects/venus-protocol-%{venus_protocol_ver} --strip-components=1

# Extract Rust crates meson cache directory
%if 0%{?vendor_nvk_crates}
mkdir subprojects/packagecache/
tar -xvf %{SOURCE10} -C subprojects/packagecache/
tar -xvf %{SOURCE11} -C subprojects/packagecache/
tar -xvf %{SOURCE12} -C subprojects/packagecache/
tar -xvf %{SOURCE13} -C subprojects/packagecache/
tar -xvf %{SOURCE14} -C subprojects/packagecache/
tar -xvf %{SOURCE15} -C subprojects/packagecache/
for d in subprojects/packagecache/*-*; do
    echo '{"files":{}}' > $d/.cargo-checksum.json
done
%endif

%if 0%{?with_nvk}
cat > Cargo.toml <<_EOF
[package]
name = "mesa"
version = "%{ver}"
edition = "2021"

[lib]
path = "src/nouveau/nil/lib.rs"

# only direct dependencies need to be listed here
[dependencies]
paste = "$(grep ^directory subprojects/paste*.wrap | sed 's|.*-||')"
syn = { version = "$(grep ^directory subprojects/syn*.wrap | sed 's|.*-||')", features = ["clone-impls"] }
rustc-hash = "$(grep ^directory subprojects/rustc-hash*.wrap | sed 's|.*-||')"
_EOF
%if 0%{?vendor_nvk_crates}
%cargo_prep -v subprojects/packagecache
%else
%cargo_prep

%generate_buildrequires
%cargo_generate_buildrequires
%endif
%endif


%build
# ensure standard Rust compiler flags are set
export RUSTFLAGS="%build_rustflags"

%if 0%{?with_nvk}
# So... Meson can't actually find them without tweaks
%if !0%{?vendor_nvk_crates}
export MESON_PACKAGE_CACHE_DIR="%{cargo_registry}/"
%endif

# This function rewrites a mesa .wrap file:
# - Removes the lines that start with "source"
# - Replaces the "directory =" with the MESON_PACKAGE_CACHE_DIR
#
# Example: An upstream .wrap file like this (proc-macro2-1-rs.wrap):
#
# [wrap-file]
# directory = proc-macro2-1.0.86
# source_url = https://crates.io/api/v1/crates/proc-macro2/1.0.86/download
# source_filename = proc-macro2-1.0.86.tar.gz
# source_hash = 5e719e8df665df0d1c8fbfd238015744736151d4445ec0836b8e628aae103b77
# patch_directory = proc-macro2-1-rs
#
# Will be transformed to:
#
# [wrap-file]
# directory = meson-package-cache-dir
# patch_directory = proc-macro2-1-rs
rewrite_wrap_file() {
  sed -e "/source.*/d" -e "s/^directory = ${1}-.*/directory = $(basename ${MESON_PACKAGE_CACHE_DIR:-subprojects/packagecache}/${1}-*)/" -i subprojects/${1}*.wrap
}

rewrite_wrap_file proc-macro2
rewrite_wrap_file quote
rewrite_wrap_file syn
rewrite_wrap_file unicode-ident
rewrite_wrap_file paste
rewrite_wrap_file rustc-hash
%endif

%meson \
  -Dplatforms=x11,wayland \
%if 0%{?with_hardware}
  -Dgallium-drivers=llvmpipe,virgl,nouveau%{?with_r300:,r300}%{?with_crocus:,crocus}%{?with_i915:,i915}%{?with_iris:,iris}%{?with_vmware:,svga}%{?with_radeonsi:,radeonsi}%{?with_r600:,r600}%{?with_asahi:,asahi}%{?with_freedreno:,freedreno}%{?with_etnaviv:,etnaviv}%{?with_tegra:,tegra}%{?with_vc4:,vc4}%{?with_v3d:,v3d}%{?with_lima:,lima}%{?with_panfrost:,panfrost}%{?with_vulkan_hw:,zink}%{?with_d3d12:,d3d12}%{?with_teflon:,ethosu,rocket} \
%else
  -Dgallium-drivers=llvmpipe,virgl \
%endif
  -Dgallium-va=%{?with_va:enabled}%{!?with_va:disabled} \
  -Dgallium-mediafoundation=disabled \
  -Dteflon=%{?with_teflon:true}%{!?with_teflon:false} \
%if 0%{?with_opencl}
  -Dgallium-rusticl=true \
%endif
  -Dvulkan-drivers=%{?vulkan_drivers} \
%if 0%{?with_freedreno}
  -Dfreedreno-kmds=msm,virtio \
%endif
  -Dvulkan-layers=device-select%{?with_vulkan_layers_anti_lag:,anti-lag} \
  -Dgles1=enabled \
  -Dgles2=enabled \
  -Dopengl=true \
  -Dgbm=enabled \
  -Dglx=dri \
  -Degl=enabled \
  -Dglvnd=enabled \
  -Dintel-rt=%{?with_intel_vk_rt:enabled}%{!?with_intel_vk_rt:disabled} \
  -Dmicrosoft-clc=disabled \
  -Dllvm=enabled \
  -Dshared-llvm=enabled \
  -Dvalgrind=%{?with_valgrind:enabled}%{!?with_valgrind:disabled} \
  -Dbuild-tests=false \
%if !0%{?with_libunwind}
  -Dlibunwind=disabled \
%endif
%if !0%{?with_lmsensors}
  -Dlmsensors=disabled \
%endif
  -Dandroid-libbacktrace=disabled \
%ifarch %{ix86}
  -Dglx-read-only-text=true \
%endif
  -Dspirv-tools=%{?with_spirv_tools:enabled}%{!?with_spirv_tools:disabled} \
  %{nil}
%meson_build

%if 0%{?with_nvk}
%cargo_license_summary
%{cargo_license} > LICENSE.dependencies
%if 0%{?vendor_nvk_crates}
%cargo_vendor_manifest
%endif
%endif

%install
%meson_install

# likewise glvnd
rm -vf %{buildroot}%{_libdir}/libGLX_mesa.so
rm -vf %{buildroot}%{_libdir}/libEGL_mesa.so
# XXX can we just not build this
rm -vf %{buildroot}%{_libdir}/libGLES*

%if ! 0%{?with_asahi}
# This symlink is unconditionally created when any kmsro driver is enabled
# We don't want this one so delete it
rm -vf %{buildroot}%{_libdir}/dri/apple_dri.so
%endif

# glvnd needs a default provider for indirect rendering where it cannot
# determine the vendor
ln -s libGLX_mesa.so.0 %{buildroot}%{_libdir}/libGLX_system.so.0

%files filesystem
%doc docs/Mesa-MLAA-License-Clarification-Email.txt
%dir %{_libdir}/dri
%dir %{_datadir}/drirc.d

%files libGL
%{_libdir}/libGLX_mesa.so.0*
%{_libdir}/libGLX_system.so.0*
%files libGL-devel
%dir %{_includedir}/GL
%dir %{_includedir}/GL/internal
%{_includedir}/GL/internal/dri_interface.h
%{_libdir}/pkgconfig/dri.pc

%files libEGL
%{_datadir}/glvnd/egl_vendor.d/50_mesa.json
%{_libdir}/libEGL_mesa.so.0*
%files libEGL-devel
%dir %{_includedir}/EGL
%{_includedir}/EGL/eglext_angle.h
%{_includedir}/EGL/eglmesaext.h

%files libgbm
%{_libdir}/libgbm.so.1
%{_libdir}/libgbm.so.1.*
%files libgbm-devel
%{_libdir}/libgbm.so
%{_includedir}/gbm.h
%{_includedir}/gbm_backend_abi.h
%{_libdir}/pkgconfig/gbm.pc

%if 0%{?with_teflon}
%files libTeflon
%{_libdir}/libteflon.so
%endif

%if 0%{?with_opencl}
%files libOpenCL
%{_libdir}/libRusticlOpenCL.so.*
%{_sysconfdir}/OpenCL/vendors/rusticl.icd

%files libOpenCL-devel
%{_libdir}/libRusticlOpenCL.so
%endif

%files dri-drivers
%{_datadir}/drirc.d/00-mesa-defaults.conf
%{_libdir}/libgallium-*.so
%{_libdir}/gbm/dri_gbm.so
%{_libdir}/dri/kms_swrast_dri.so
%{_libdir}/dri/libdril_dri.so
%{_libdir}/dri/swrast_dri.so
%{_libdir}/dri/virtio_gpu_dri.so
%{_datadir}/drirc.d/00-virtio_gpu-defaults.conf

%if 0%{?with_hardware}
%if 0%{?with_r300}
%{_libdir}/dri/r300_dri.so
%{_datadir}/drirc.d/00-r300-defaults.conf
%endif
%if 0%{?with_radeonsi}
%if 0%{?with_r600}
%{_libdir}/dri/r600_dri.so
%{_datadir}/drirc.d/00-r600-defaults.conf
%endif
%{_libdir}/dri/radeonsi_dri.so
%{_datadir}/drirc.d/00-radeonsi-defaults.conf
%endif
%ifarch %{ix86} x86_64
%{_libdir}/dri/crocus_dri.so
%{_datadir}/drirc.d/00-crocus-defaults.conf
%{_libdir}/dri/iris_dri.so
%{_datadir}/drirc.d/00-iris-defaults.conf
%if 0%{?with_i915}
%{_libdir}/dri/i915_dri.so
%endif
%endif
%ifnarch s390x
%if 0%{?with_asahi}
%{_libdir}/dri/apple_dri.so
%{_libdir}/dri/asahi_dri.so
%{_datadir}/drirc.d/00-asahi-defaults.conf
%endif
%if 0%{?with_d3d12}
%{_libdir}/dri/d3d12_dri.so
%{_datadir}/drirc.d/00-d3d12-defaults.conf
%endif
%{_libdir}/dri/ingenic-drm_dri.so
%{_libdir}/dri/imx-drm_dri.so
%{_libdir}/dri/imx-lcdif_dri.so
%{_libdir}/dri/kirin_dri.so
%{_libdir}/dri/komeda_dri.so
%{_libdir}/dri/mali-dp_dri.so
%{_libdir}/dri/mcde_dri.so
%{_libdir}/dri/mxsfb-drm_dri.so
%{_libdir}/dri/rcar-du_dri.so
%{_libdir}/dri/stm_dri.so
%endif
%if 0%{?with_vc4}
%{_libdir}/dri/vc4_dri.so
%endif
%if 0%{?with_v3d}
%{_libdir}/dri/v3d_dri.so
%{_datadir}/drirc.d/00-v3d-defaults.conf
%endif
%if 0%{?with_freedreno}
%{_libdir}/dri/kgsl_dri.so
%{_libdir}/dri/msm_dri.so
%{_datadir}/drirc.d/00-msm-defaults.conf
%endif
%if 0%{?with_etnaviv}
%{_libdir}/dri/etnaviv_dri.so
%endif
%if 0%{?with_tegra}
%{_libdir}/dri/tegra_dri.so
%endif
%if 0%{?with_lima}
%{_libdir}/dri/lima_dri.so
%endif
%if 0%{?with_panfrost}
%{_libdir}/dri/panfrost_dri.so
%{_libdir}/dri/panthor_dri.so
%{_datadir}/drirc.d/00-panfrost-defaults.conf
%endif
%{_libdir}/dri/nouveau_dri.so
%if 0%{?with_vmware}
%{_libdir}/dri/vmwgfx_dri.so
%{_datadir}/drirc.d/00-vmwgfx-defaults.conf
%endif
%endif
%if 0%{?with_kmsro}
%{_libdir}/dri/armada-drm_dri.so
%{_libdir}/dri/exynos_dri.so
%{_libdir}/dri/gm12u320_dri.so
%{_libdir}/dri/hdlcd_dri.so
%{_libdir}/dri/hx8357d_dri.so
%{_libdir}/dri/ili9163_dri.so
%{_libdir}/dri/ili9225_dri.so
%{_libdir}/dri/ili9341_dri.so
%{_libdir}/dri/ili9486_dri.so
%{_libdir}/dri/imx-dcss_dri.so
%{_libdir}/dri/mediatek_dri.so
%{_libdir}/dri/meson_dri.so
%{_libdir}/dri/mi0283qt_dri.so
%{_libdir}/dri/panel-mipi-dbi_dri.so
%{_libdir}/dri/pl111_dri.so
%{_libdir}/dri/repaper_dri.so
%{_libdir}/dri/rockchip_dri.so
%{_libdir}/dri/rzg2l-du_dri.so
%{_libdir}/dri/ssd130x_dri.so
%{_libdir}/dri/st7586_dri.so
%{_libdir}/dri/st7735r_dri.so
%{_libdir}/dri/sti_dri.so
%{_libdir}/dri/sun4i-drm_dri.so
%{_libdir}/dri/udl_dri.so
%{_libdir}/dri/vkms_dri.so
%{_libdir}/dri/zynqmp-dpsub_dri.so
%endif
%if 0%{?with_vulkan_hw}
%{_libdir}/dri/zink_dri.so
%{_datadir}/drirc.d/00-zink-defaults.conf
%endif
%if 0%{?with_va}
%{_libdir}/dri/nouveau_drv_video.so
%if 0%{?with_r600}
%{_libdir}/dri/r600_drv_video.so
%endif
%if 0%{?with_radeonsi}
%{_libdir}/dri/radeonsi_drv_video.so
%endif
%if 0%{?with_d3d12}
%{_libdir}/dri/d3d12_drv_video.so
%endif
%{_libdir}/dri/virtio_gpu_drv_video.so
%endif

%if 0%{?with_d3d12}
%files dxil-devel
%{_bindir}/spirv2dxil
%{_libdir}/libspirv_to_dxil.a
%{_libdir}/libspirv_to_dxil.so
%endif

%files vulkan-drivers
%if 0%{?with_nvk}
%license LICENSE.dependencies
%if 0%{?vendor_nvk_crates}
%license cargo-vendor.txt
%endif
%endif
%{_libdir}/libvulkan_lvp.so
%{_datadir}/vulkan/icd.d/lvp_icd.*.json
%{_datadir}/drirc.d/00-lavapipe-defaults.conf
%{_libdir}/libVkLayer_MESA_device_select.so
%{_datadir}/vulkan/implicit_layer.d/VkLayer_MESA_device_select.json
%if 0%{?with_vulkan_layers_anti_lag}
%{_libdir}/libVkLayer_MESA_anti_lag.so
%{_datadir}/vulkan/implicit_layer.d/VkLayer_MESA_anti_lag.json
%endif
%if 0%{?with_virtio}
%{_libdir}/libvulkan_virtio.so
%{_datadir}/vulkan/icd.d/virtio_icd.*.json
%{_datadir}/drirc.d/00-venus-defaults.conf
%endif
%if 0%{?with_vulkan_hw}
%{_libdir}/libvulkan_radeon.so
%{_datadir}/drirc.d/00-radv-defaults.conf
# iceland: new in 26.3 (not in Fedora's 26.2 %%files)
%{_datadir}/drirc.d/01-radv-performance.conf
%{_datadir}/vulkan/icd.d/radeon_icd.*.json
%if 0%{?with_nvk}
%{_libdir}/libvulkan_nouveau.so
%{_datadir}/vulkan/icd.d/nouveau_icd.*.json
%{_datadir}/drirc.d/00-nvk-defaults.conf
%endif
%if 0%{?with_d3d12}
%{_libdir}/libvulkan_dzn.so
%{_datadir}/vulkan/icd.d/dzn_icd.*.json
%{_datadir}/drirc.d/00-dzn-defaults.conf
%endif
%ifarch %{ix86} x86_64
%{_libdir}/libvulkan_intel.so
%{_datadir}/vulkan/icd.d/intel_icd.*.json
%{_datadir}/drirc.d/00-anv-defaults.conf
%{_libdir}/libvulkan_intel_hasvk.so
%{_datadir}/vulkan/icd.d/intel_hasvk_icd.*.json
%{_datadir}/drirc.d/00-hasvk-defaults.conf
%endif
%ifarch aarch64 x86_64 %{ix86}
%if 0%{?with_asahi}
%{_libdir}/libvulkan_asahi.so
%{_datadir}/vulkan/icd.d/asahi_icd.*.json
%{_datadir}/drirc.d/00-hk-defaults.conf
%endif
%{_libdir}/libvulkan_broadcom.so
%{_datadir}/vulkan/icd.d/broadcom_icd.*.json
%{_datadir}/drirc.d/00-v3dv-defaults.conf
%{_libdir}/libvulkan_freedreno.so
%{_datadir}/vulkan/icd.d/freedreno_icd.*.json
%{_datadir}/drirc.d/00-turnip-defaults.conf
%{_libdir}/libvulkan_panfrost.so
%{_datadir}/vulkan/icd.d/panfrost_icd.*.json
%{_datadir}/drirc.d/00-panvk-defaults.conf
%{_libdir}/libvulkan_powervr_mesa.so
%{_datadir}/vulkan/icd.d/powervr_mesa_icd.*.json
%{_datadir}/drirc.d/00-pvr-defaults.conf
%endif
%endif

%changelog
* Sat Nov 07 2026 mzak <mzak.amin@gmail.com> - 26.3.0~rc3^git20261104.25248e6-1.iceland1
- Fedora 45's mesa.spec (f45 13d08919, 26.2.6) for Mesa staging/26.3 25248e6d
  (26.3.0-rc3 + 137 commits; 26.3.0 not tagged yet): version and source; anti-lag
  layer off (removed in 26.3); venus-protocol 1.1.3 as Source2;
  01-radv-performance.conf packaged (new in 26.3); libclc / libclc22 by release
- -Dfreedreno-kmds=msm,virtio: the freedreno / turnip virtio (native context)
  backend for VM guests
- 30 patches 9101-9130 (Adreno 840 / gen8, ir3, turnip): merged on main and not
  in 26.3: !45525 (26.3 backport of !44352), !45369, !45366, !45416, !45342,
  !45554, !45506, !45464, !45517, !45559, !45601, !43899, !45882, !45918, !45981,
  !46027; open: !45243, !44365, !45937, !45985, !45926, !45904, !45928, !46023,
  !45958, !45727; general ir3 / turnip perf + correctness (open): !44712, !37924,
  !43714, !43272 (9127-9130)
- dropped: !45204 and !45717 (in 26.3)
- the earlier changelog entries are Fedora's (%%autochangelog of
  https://src.fedoraproject.org/rpms/mesa) and the iceland builds of
  26.3.0~rc1~git20261019.e282ea8c (f44)
