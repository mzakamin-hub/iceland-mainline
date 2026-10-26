# libcamera with autofocus for the OnePlus Pad 4

`libcamera-0.7.1-3.fc44.iceland_af1`: Fedora 44's `libcamera.spec` (0.7.1-3) plus four patches that give the simple
pipeline handler (the one the Pad 4's SmartSens sensors use, with the software ISP) lens control and autofocus.

| Patch | Author | What |
|---|---|---|
| `0001-disable-rpi-pisp.patch` | Fedora | Fedora's own patch |
| `0001-pipeline-simple-add-native-manual-focus-control.patch` | Osilvfe ([caihong-camera](https://github.com/Osilvfe)) | manual focus through the lens controller |
| `0002-software_isp-report-a-luminance-gradient-focus-metri.patch` | Osilvfe | a focus metric from the software ISP's statistics |
| `0003-pipeline-simple-add-contrast-detect-autofocus.patch` | Osilvfe | contrast-detect autofocus |
| `0004-pipeline-simple-autofocus-defaults-and-settling-for-.patch` | this project | continuous AF by default, settling, `LIBCAMERA_SIMPLE_AF_MODE` / `LIBCAMERA_SIMPLE_AF_RANGE` |

Licence: LGPL-2.1-or-later (libcamera). Source: `libcamera-v0.7.1.tar.bz2` from the URL in the spec. Build on
Fedora 44: `spectool -g -R libcamera.spec && rpmbuild -bb libcamera.spec` with the patches and the other files of this
directory in `SOURCES`.
