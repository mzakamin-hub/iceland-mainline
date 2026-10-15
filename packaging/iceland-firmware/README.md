# iceland-firmware

Generic firmware of the OnePlus Pad 4 (OPD2514, "iceland"; Snapdragon 8 Elite Gen 5 / kaanapali) for mainline Linux,
taken from the stock software release 11.A.38 and packaged for Fedora (`iceland-firmware.spec`).

The package lives in the public repository [mzakamin-hub/iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware)
(created 12 Oct 2026). Releases: 11.A.38-2 (commit c40c33e) and 11.A.38-3 (commit 70ea8f1, which adds the thermal model
file). The install image and the installed tablet use 11.A.38-3.
This directory holds the package's text parts; the firmware files themselves are not kept in iceland-mainline.

Layout of the repository:

    iceland-firmware.spec        RPM spec (noarch; files under /usr/lib/firmware/updates and
                                 /usr/share/qcom/kaanapali/OnePlus/iceland)
    MANIFEST.tsv                 path, sha256, bytes, class, stock source partition:path, transformation, notice,
                                 comparison with SuperTurtleDev/iceland-mainline-kernel-firmware
    EXCLUDED.tsv                 unit-specific data that is never packaged
    NOTICE.md                    vendor notices and the documented transformations
    Notice-qca-atheros.txt       Qualcomm Atheros notice (WCN7860)
    root/usr/lib/firmware/updates/...                      the firmware files (about 130 MB; the largest, adsp.mbn,
                                                           about 41 MB, is below GitHub's file limit, so no LFS)
    root/usr/share/qcom/kaanapali/OnePlus/iceland/...      the sensor hub's file tree (without the registry)
    root/etc/iceland/thermal-model.json                    stock's shell-temperature model for iceland-thermal
                                                           (decoded, generic; from 11.A.38-3)

Every file is byte-identical to what the installer's extraction writes from a tablet's own stock partitions;
`sha256sum -c` against MANIFEST.tsv proves it. The one exception is `/etc/iceland/thermal-model.json` (since 11.A.38-3):
stock's thermal model, decoded from the vendor's encrypted configuration. It is generic and the same on every unit. The
encrypted inputs, the key and the decoder are not published (NOTICE.md).

Unit-specific data (the sensor calibration registry from `persist`, the Bluetooth and Wi-Fi addresses) is not in the
package. The installer still extracts it from the tablet itself.
