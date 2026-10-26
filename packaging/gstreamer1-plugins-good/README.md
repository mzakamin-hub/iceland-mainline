# gstreamer1-plugins-good with the V4L2 colorimetry fix

`gstreamer1-plugins-good-1.28.8-1.fc44.iceland1`: Fedora 44's spec plus one patch,
`gst-plugins-good-1.28-mr12699-v4l2-coded-colorimetry.patch` = GStreamer
[!12699](https://gitlab.freedesktop.org/gstreamer/gstreamer/-/merge_requests/12699) (the 1.28 backport of !12602):
the V4L2 decoders accept any colorimetry on coded output caps, so SD BT.601 and partially signalled H.264 / HEVC
streams negotiate on the Pad 4's Iris decoder instead of failing.

Licence: LGPL-2.1-or-later. Source: `gst-plugins-good-1.28.8.tar.xz` from the URL in the spec. Build on Fedora 44 with
`rpmbuild -bb gstreamer1-plugins-good.spec`.
