#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Dual boot (docs/DUAL-BOOT.md, "Backups first"): READ-ONLY backup on the installed Fedora of the OnePlus Pad 4. Run as root:
#   sudo bash dualboot-backup.sh [OUT_DIR]      (default /var/tmp/dualboot-backup-<date-time>)
# Only reads block devices (dd if=... of=<file>); every output file goes into OUT_DIR on Fedora's own disk. It never
# opens a device for writing, never mounts, never runs blockdev --setrw. Private output (partition GUIDs, the unit's
# tables): copy it to the PC's backups folder, never into a repository.
set -u
OUT=${1:-/var/tmp/dualboot-backup-$(date +%Y%m%d-%H%M)}
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
mkdir -p "$OUT" && chmod 700 "$OUT" || exit 1
cd "$OUT" || exit 1
exec > >(tee -a "$OUT/LOG.txt") 2>&1
echo "dualboot-backup (read only) $(date -u +%FT%TZ), kernel $(uname -r)"
pl() { readlink -f "/dev/disk/by-partlabel/$1"; }
rd() { # rd OUT_FILE DEVICE [dd args]: read only
	local f=$1 d=$2; shift 2
	[ -b "$d" ] || { echo "MISSING device $d for $f"; return 1; }
	dd if="$d" of="$f" bs=4096 status=none iflag=direct "$@" && echo "read $f ($(stat -c %s "$f") B)"
}
# ---- 1. partition tables of every UFS LUN: first and last 1 MiB + LUN 0 exactly ----
mkdir -p gpt
for d in /sys/block/sd?; do
	n=${d##*/}; b=$(cat "$d/size"); blocks=$((b * 512 / 4096))
	echo "$n: $blocks blocks of 4096 B"
	rd "gpt/$n-head1M.bin" "/dev/$n" count=256
	rd "gpt/$n-tail1M.bin" "/dev/$n" skip=$((blocks - 256)) count=256
done > /dev/null
for d in /sys/block/sd?; do n=${d##*/}; echo "$n $(( $(cat $d/size) * 512 / 4096 )) blocks"; done | tee gpt/luns.txt
SDA=$(( $(cat /sys/block/sda/size) * 512 / 4096 ))
rd gpt/sda-head6.bin /dev/sda count=6
rd gpt/sda-tail5.bin /dev/sda skip=$((SDA - 5)) count=5
cp gpt/sda-head6.bin gpt/sda-head6.copy2.bin; cp gpt/sda-tail5.bin gpt/sda-tail5.copy2.bin
sfdisk -d /dev/sda > gpt/sda-sfdisk.txt 2>&1
for n in sda sdb sdc sdd sde sdf; do [ -b /dev/$n ] && lsblk -b -o NAME,SIZE,PARTLABEL,PARTUUID /dev/$n > gpt/$n-lsblk.txt 2>&1; done
# ---- 2. Fedora's inner disk (the loop over userdata) ----
mkdir -p fedora
LOOP=$(losetup -j "$(pl userdata)" -O NAME -n 2>/dev/null | head -1)
[ -z "$LOOP" ] && LOOP=$(losetup -l -n -O NAME,BACK-FILE | awk '/userdata|sda/ {print $1; exit}')
losetup -l > fedora/losetup.txt 2>&1; echo "Fedora disk loop: ${LOOP:-not found}"
if [ -n "$LOOP" ]; then
	LB=$(( $(blockdev --getsize64 "$LOOP") / 4096 ))
	rd fedora/inner-head6.bin "$LOOP" count=6
	rd fedora/inner-tail5.bin "$LOOP" skip=$((LB - 5)) count=5
	sfdisk -d "$LOOP" > fedora/inner-sfdisk.txt 2>&1; echo "inner disk $LB blocks" >> fedora/inner-sfdisk.txt
fi
btrfs filesystem usage -b / > fedora/btrfs-usage.txt 2>&1
btrfs subvolume list / > fedora/btrfs-subvolumes.txt 2>&1
df -B1 / /boot /boot/efi > fedora/df.txt 2>&1
cat /etc/repart.d/*.conf > fedora/repart.txt 2>&1; systemctl is-enabled systemd-repart.service >> fedora/repart.txt 2>&1
# ---- 3. small Android partitions (both slots where they exist) + super's metadata ----
mkdir -p parts
for p in misc boot_b recovery_b vendor_boot_b init_boot_b dtbo_b vbmeta_b vbmeta_system_b vbmeta_vendor_b \
	 boot_a recovery_a vendor_boot_a init_boot_a dtbo_a vbmeta_a vbmeta_system_a vbmeta_vendor_a metadata; do
	d=$(pl $p); [ -b "$d" ] && rd "parts/$p.img" "$d"
done
S=$(pl super); SB=$(( $(blockdev --getsize64 "$S") / 4096 ))
rd parts/super-head1M.bin "$S" count=256
rd parts/super-tail1M.bin "$S" skip=$((SB - 256)) count=256
# ---- 4. firmware on both slots: sha256 of the first N bytes (N = Bliss's image size) vs Bliss's image ----
echo "== firmware vs BlissROM v20.1 20261016 (same = the tablet already has Bliss's firmware)" > firmware-compare.txt
while read -r name size sha; do
	for s in a b; do
		d=$(pl ${name}_$s); [ -b "$d" ] || { echo "$name _$s: no partition" >> firmware-compare.txt; continue; }
		h=$(head -c "$size" "$d" | sha256sum | cut -d' ' -f1)
		[ "$h" = "$sha" ] && r=SAME || r=DIFF
		echo "$name _$s: $r" >> firmware-compare.txt
	done
done <<'LIST'
abl 278528 bdb1de2b4ed420a3da42040c016ea9115e54191311d5fd6701f716d0104c1f1b
aop 393216 a932e6dc87c993b795e6ddaab9754ec2d6e35033fb2760847f0ac20a204bd74c
aop_config 28672 4119b78008df95cba7f81c655189a54f218b245010a35f35952f13a6acfe8c8a
bluetooth 8388608 0290e0956ff1b0e6580c49eea939cca85dcb7a46199adadef19dbbcd3de97075
cpucp 446464 1f0c965f4ba1531f18af506e8afc7ad7b9e5967f4fe9706c543cacc62d046a79
cpucp_dtb 16384 b2ac047a6c5cabc8f90132f9d7746cf22b6f2ace0f38a1cf4516d9a801cf757b
dcp 8388608 3b001e985793afa71b37bb988039bcb1e328922eab0c0b80b0f518e9668a199a
devcfg 61440 0b501d595c0d5925113439f5fe93daef1a48443fd4f4ede39f24c6873f7c29e2
dsp 77594624 283e60c9bf75a5e095f5b7943e0264e3480ec08f7457e4552cca9aa75a625ccd
engineering_cdt 1048576 0832aec0b83116f343636f25b2ebf7e96173cc6abaffc109e7ae96f4d79e9ce2
featenabler 106496 08ef34b4f0ec6a934c0b3f5270a09d63f4f5f4951224e181880174dedefffb89
hyp 1658880 8e9ea45ba7b0c7edfa44f212ab71671b4c62f28ca2d6c38e5f660e6b78dd69a7
hyp_ac_config 77824 22443fd36a705269e4b9230f427d7563999de3dc7fa8a5ef7a5055a8e9554ee6
imagefv 114688 10a662ed285db106acfc1bac455d707ec7500285a4317f6e9c28900c41bd5f20
keymaster 3354624 0acc1861160078f582e0a308320aa6a11d1a5e8fc0dfc0ae7d774ab670f37085
modem 367001600 5b92bd694c63ea6f51153a4466067afc91b6575d934587963bdcd9a4d7b0de24
multiimgoem 12288 cef2b557a5135f848e3d39fb635991c3e7a14868fd26aea979fbb2db276df708
multiimgqti 12288 b3d1ce73b479dc87f91f46e6bc48e3183d86d09d24ba036af4497fed4cfc60fb
oplus_sec 1040384 5e3920c437c008ae2728ae92c4ee750296ecba15db6e7d3e1907498990a140f4
pdp 356352 10951e90e921a378096df3409d63ab08bf4112aeb0cf4b2b11e7e618ae2118a7
pdp_cdb 16384 0508b71aaea7f573a8c3e06eb96bc8331bbf335df5dedb25316b4faba1ef2a81
pvmfw 1048576 2c9ec9b8bb09b09ca19177c3ba7f35328e5945e1bdd32b8f1f6372853ae1b4b7
qupfw 69632 f3c1080214664eca8da57f5345433661a8d0ffd98aa5190ad8e89dac31fd3cf6
secretkeeper 1056768 76218efecd8aea4a43d251a49da69b4fa14661a4193823d208d1cdd54a02a585
shrm 184320 d2bc8d0616a259a05ab409b2a0fc3ffe315a7c5c33b4ae1c6667ea64c072cc97
soccp 8388608 6b29db3e8bc835add4ee22b6490fe879e81eb2d3cc9cf5b021f022ea2e0aa8e9
soccp_dcd 16384 87eadbbefdd5c9e67b113216a45fa47f7580bee0d69829da13aba7422f0d6876
soccp_debug 73728 22710d9d36080b24637dc022934f9295252e0646ee4dd04914a8ea72144e19a6
splash 15331328 276bc6e6e3f6b6e51c277ddc25c451a618c78270b2832d538e4208a909b2cbbc
spuservice 94208 f6bbf24e6ba7a3abde6462d885400d2b65d0bde66e74706f71cd2f3076bb3fe9
tme_config 45056 d3e6259270370bbe9f2151a0f4bf232130e3ec37e2598ed86f197759e0f5a062
tme_fw 204800 af5e62c12862fcd233c2f6f66de3166fa3b1d6d21995656972bc8f5bdbc6b5bf
tme_seq_patch 8192 35d85544a793890932c877a5da14c63a6a539223c9929e00055318fe03063b9b
tz 4227072 f6125b453f09038790c448a2b5c7cd29a63f79823798ae475fd708afee4be4ef
tz_ac_config 65536 7393f543d10132b64735dc1eccc4cbbf4bc39d93c75c4296463c5be2a16ad7f1
tz_qti_config 139264 589a6bda7b7c1a82cfa202b69f9eafea3e1ab356d917f1942a3a949c1fc59e70
uefi 2797568 d6457fc950b759eb19e03796c30d243e5b1ca7c1f1ccb8042a686c2adbadac88
uefisecapp 208896 b168c7b4ee67b7af98407e94e2f8d5bc4de734859a9dedb14c01c7e2238fc3db
xbl 1183744 29c4458164abc7714c27ce4f16e4940322a6d08d2affccdc07c58368dc300d21
xbl_ac_config 45056 f6cfba9acd0ed6eb019e511f8d5b5061b460497a850f0ba317e15f90e744adbf
xbl_config 397312 192a442f7212345b2fc91ae880a5fb1b5e01eae870fd5a0b1a5e136008c8d0b1
xbl_ramdump 1036288 386d187f2cc208403d6dde234f2726a8e6500ab78deff0b36c5b18faeae4a04b
LIST
grep -c SAME firmware-compare.txt | sed 's/^/SAME count: /'; grep -c DIFF firmware-compare.txt | sed 's/^/DIFF count: /'
# ---- 5. slot flags as the OS sees them (read only) ----
command -v qbootctl >/dev/null && qbootctl > slots.txt 2>&1
# ---- 6. sums ----
# LOG.txt is still being appended to (tee), so it is not in the sums
find . -type f ! -name SHA256SUMS ! -name SHA256SUMS.copy2 ! -name LOG.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
cp SHA256SUMS SHA256SUMS.copy2
du -sh "$OUT"; echo "DUALBOOT-BACKUP DONE: $OUT"
