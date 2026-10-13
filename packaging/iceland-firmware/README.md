# iceland-firmware

Generic firmware of the OnePlus Pad 4 (OPD2514, "iceland"; Snapdragon 8 Elite Gen 5 / kaanapali) for mainline Linux,
taken from the stock software release 11.A.38 and packaged for Fedora (`iceland-firmware.spec`).

Proposed repository: `mzakamin-hub/iceland-firmware` (dedicated, firmware only; the kernel and project repositories
keep their blob guards). Layout:

    iceland-firmware.spec        RPM spec (noarch; files under /usr/lib/firmware/updates and
                                 /usr/share/qcom/kaanapali/OnePlus/iceland)
    MANIFEST.tsv                 path, sha256, bytes, class, stock source partition:path, transformation, notice,
                                 comparison with SuperTurtleDev/iceland-mainline-kernel-firmware
    EXCLUDED.tsv                 unit-specific data that is never packaged
    NOTICE.md                    vendor notices and the documented transformations
    Notice-qca-atheros.txt       Qualcomm Atheros notice (WCN7860)
    root/usr/lib/firmware/updates/...                      the firmware files (~130 MB; largest file adsp.mbn ~41 MB, below GitHub limits)
    root/usr/share/qcom/kaanapali/OnePlus/iceland/...      the sensor hub's file tree (without the registry)
    root/etc/iceland/thermal-model.json                    stock's shell-temperature model for iceland-thermal
                                                           (decoded, generic; from 11.A.38-3)

Every file is byte-identical to what `iceland-fw-extract` (iceland-mainline) writes from a tablet's own stock
partitions; `sha256sum -c` against MANIFEST.tsv proves it. The one exception is
`/etc/iceland/thermal-model.json` (since 11.A.38-3): stock's thermal model, decoded from the vendor's
encrypted configuration, generic and the same on every unit; the encrypted inputs, the key and the decoder are not
published (NOTICE.md). Unit-specific data (the sensor calibration registry from
`persist`, Bluetooth / Wi-Fi addresses) is not here: the installer still extracts it from the tablet itself.
