# iris-vaapi: VA-API hardware video decode for the OnePlus Pad 4

`iris-vaapi-0.2.0^20261023git9852479-1.iceland1`: the VA-API driver of
[CFM880/iris-vaapi](https://github.com/CFM880/iris-vaapi) (upstream name vpu-vaapi, commit `9852479`, version 0.2.0)
for the Qualcomm Iris V4L2 decoder (`qcom_iris`) of the Pad 4's kernel, packaged for Fedora 44 aarch64.

## What works on the Pad 4

- `vainfo` lists H.264 (Constrained Baseline / Main / High), HEVC Main / Main10 and VP9 profile 0 / 2 decoding.
- `ffmpeg -hwaccel vaapi` decodes VP9 1080p in hardware; H.264 decodes in hardware through VA-API (the pipelined
  decode Chromium uses). Fedora's `ffmpeg-free` has no H.264 / HEVC software parser, so ffmpeg can drive only VP9.
- Fedora's chromium decodes H.264 and VP9 in hardware with `iris-vaapi-chromium` installed. Fedora's aarch64
  chromium is built without VA-API: it uses the Iris V4L2 decoder directly and needs only the feature flag that
  package sets.

## Packages

| Package | Installs |
|---|---|
| `iris-vaapi` | `/usr/lib64/dri/vpu_drv_video.so` (and `iris_drv_video.so` linked to it); `LIBVA_DRIVER_NAME=iris` for user sessions (`/usr/lib/environment.d/55-iris-vaapi.conf`); `/dev/dma_heap/system` as 0660 root:video plus the active seat user (`70-iris-vaapi-dmaheap.rules`); `qcom_iris decode_order_output=1` (`/usr/lib/modprobe.d/iris-vaapi.conf`; the kernel's default stays off and removing the package turns it off again) |
| `iris-vaapi-chromium` | `CHROMIUM_FLAGS=--enable-features=AcceleratedVideoDecoder,VaapiVideoDecoder` for user sessions (`56-iris-vaapi-chromium.conf`; a user's `CHROMIUM_USER_FLAGS` still wins) |
| `iris-vaapi-tests` | upstream's hardware tests in `/usr/libexec/iris-vaapi`: `test_va` (a vainfo stand-in), `test_va_decode`, `test_va_stress`, `test_va_vp9` |

The environment.d files take effect at the next login.

## Patches

| Patch | What |
|---|---|
| `0001-decode-skip-capture-pictures-without-a-client-timest.patch` | a CAPTURE picture without a client timestamp (the HFI gen2 firmware returns such internal pictures in decode-order mode) is requeued and skipped instead of failing the session |
| `0002-vaapi-report-YUV420-for-the-10-bit-profiles-too.patch` | the 10-bit profiles also report `VA_RT_FORMAT_YUV420`, which Chromium checks before it lists HEVC Main10 |

Both are re-implemented here from the notes of TheMojoMan's port for the OnePlus Pad 3 (oneplus-erhai-ubuntu,
oneplus-erhai-video); see `README.iceland`.

## Build (Fedora 44 aarch64)

```bash
git clone https://github.com/CFM880/iris-vaapi.git && cd iris-vaapi
C=9852479288b088699ae0c0b4c848dbda58bf7391
git archive --prefix=iris-vaapi-$C/ $C | gzip -n > ~/rpmbuild/SOURCES/iris-vaapi-9852479.tar.gz
cp /path/to/iceland-mainline/packaging/iris-vaapi/* ~/rpmbuild/SOURCES/
rpmbuild -ba ~/rpmbuild/SOURCES/iris-vaapi.spec
```

## Licence

GPL-2.0-or-later, as upstream (`COPYING` is upstream's licence text).
