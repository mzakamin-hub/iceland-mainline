# Mesa for the OnePlus Pad 4 (Adreno 840)

`mesa-26.3.0~rc1~git20261019.e282ea8c-1.fc44.iceland1`, the Mesa build the project's tablet runs. It is Fedora 44's
`mesa.spec` (dist-git f44 `4d53ade0`, 26.2.5-1) with only the version and source changed, plus seven patches for the
A840 (gen8) GPU taken from merge requests that were still open upstream on 20 Oct 2026.

## Source

`mesa-26.3.0-rc1-git20261019.e282ea8c.tar.xz` is a `git archive` of Mesa's `staging/26.3` branch at `e282ea8c`
(26.3.0-rc1 was not tagged yet), with the venus protocol bundled as in the release tarballs:

```bash
git clone https://gitlab.freedesktop.org/mesa/mesa.git && cd mesa && git checkout e282ea8c
git archive --prefix=mesa-26.3.0-rc1-git20261019.e282ea8c/ -o mesa-26.3.0-rc1-git20261019.e282ea8c.tar.xz HEAD
```

The Rust crates (`Source10`-`Source15`) download from crates.io as listed in the spec.

## Patches (all from open upstream merge requests, MIT like Mesa)

| Patch | Merge request | What |
|---|---|---|
| `9001-mr44352-tu-a8xx-split-large-indirect-draws.patch` | [!44352](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/44352) | turnip: split large indirect draws on A8xx (fault on big draws) |
| `9002-mr45204-tu-texel-buffer-emulation-bounds.patch` | [!45204](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45204) | turnip: texel buffer emulation bounds check |
| `9003-mr45369-tu-vis-stream-bo-reference.patch` | [!45369](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45369) | turnip: drop the reference taken for the visibility stream patchpoint |
| `9004-mr45366-tu-float16-3d-path-msaa-copies.patch` | [!45366](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45366) | turnip: the float16 3D path for multisampled copies |
| `9005-mr45243-tu-inline-uniform-block-fixes.patch` | [!45243](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45243) | turnip: inline uniform block fixes |
| `9006-mr44365-nir-ir3-udiv-rcp-rounding.patch` | [!44365](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/44365) | nir / ir3: fp32 correction path for 32-bit udiv (backport) |
| `9007-mr43899-tu-sysmem-depth-clear-ccu.patch` | [!43899](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/43899) | turnip: CCU depth / colour cache coherency in sysmem depth clears |

Each patch keeps its upstream author. Drop a patch once its merge request is in the Mesa version you build.

## Build

On Fedora 44 aarch64 with the build dependencies of the spec (`dnf builddep mesa.spec`):

```bash
cp *.patch Mesa-MLAA-License-Clarification-Email.txt mesa-26.3.0-rc1-git20261019.e282ea8c.tar.xz ~/rpmbuild/SOURCES/
spectool -g -R mesa.spec
rpmbuild -bb mesa.spec
```

The binary RPMs are not published here.
