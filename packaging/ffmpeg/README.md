# ffmpeg-free with V4L2 hardware decoding for the OnePlus Pad 4

`ffmpeg-free-8.1.3-1.fc44.iceland4`: Fedora 44's `ffmpeg` (ffmpeg-free) spec with the V4L2 memory-to-memory decoder
path made usable on the Pad 4's Iris video codec (H.264 / HEVC / VP9 / AV1 decode through `*_v4l2m2m`).

| Patch | Origin | What |
|---|---|---|
| `ffmpeg-codec-choice.patch`, `ffmpeg-allow-fdk-aac-free.patch`, `ffmpeg-allow-decklink.patch`, `ffmpeg-chromium.patch` | Fedora | unchanged from Fedora's package |
| `ffmpeg-vulkan-direct-export.patch` | FFmpeg commit [25e187f8](https://git.ffmpeg.org/gitweb/ffmpeg.git/commit/25e187f8494966377a4b9d077260ce7b501a911c) | Vulkan DRM map / decode barrier fix (as in Fedora) |
| `ffmpeg-v4l2-drmprime.patch` | Lukas Rusak (LibreELEC's v4l2 DRM-PRIME series) | v4l2m2m outputs DRM-PRIME frames |
| `ffmpeg-v4l2m2m-timebase.patch` | this project | keep pts when the caller sets no timebase |
| `ffmpeg-v4l2m2m-flush-after-drain.patch` | this project | restart the capture queue on a flush after drain |
| `ffmpeg-v4l2m2m-source-change-last.patch` | this project | finish a same-format source change at its LAST buffer; EOS only while draining |

Licence: LGPL-2.1-or-later (ffmpeg-free's configuration). Sources: `ffmpeg-8.1.3.tar.xz` and its signature from the
URLs in the spec; `enable_decoders` and `enable_encoders` are here; `ffmpeg.keyring` (the FFmpeg release signing
key) comes from Fedora's dist-git (https://src.fedoraproject.org/rpms/ffmpeg). Build on Fedora 44 with
`rpmbuild -bb ffmpeg.spec`.
