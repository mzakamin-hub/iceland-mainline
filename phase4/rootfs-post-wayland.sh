#!/bin/bash
# iceland pc-024 Y9 post-install test (runs in the Fedora rootfs after iceland-dnf.service's install, as root):
# a Wayland compositor on the Adreno 840 - seatd (libseat backend) + cage (wlroots) running glmark2-es2-wayland
# full screen; the renderer, output and score lines go to the kernel log (short lines, /dev/kmsg caps ~1 KB).
# Nothing is written to the tablet. Logs stay in /tmp of the RAM rootfs (cage.log, seatd.log, glmark2.log).
k() { echo "iceland-wl: $*" > /dev/kmsg; }
export XDG_RUNTIME_DIR=/run/user/0; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
for b in seatd cage glmark2-es2-wayland; do command -v "$b" >/dev/null || { k "missing $b - skipped"; exit 0; }; done
seatd -u root -g root > /tmp/seatd.log 2>&1 &
sleep 1
export LIBSEAT_BACKEND=seatd WLR_RENDERER=gles2 WLR_LIBINPUT_NO_DEVICES=1
k "cage + glmark2-es2-wayland start at $(cut -d' ' -f1 /proc/uptime) s"
# stdin from a silent process substitution (not a pipeline, which would wait for the whole sleep): cage/glmark2
# must not see a closed stdin
timeout 240 cage -d -- glmark2-es2-wayland --fullscreen -b build:duration=8 -b texture:duration=8 \
	-b shading:duration=8 -b bump:duration=8 < <(sleep 900) > /tmp/cage.log 2>&1
k "cage exit $? at $(cut -d' ' -f1 /proc/uptime) s"
grep -iE 'renderer|GL_RENDERER|GL_VENDOR|Using .* renderer|DRM|backend|output|modeset|libinput|error|fail|FPS|Score|Frame' /tmp/cage.log |
	grep -viE 'GL_EXTENSIONS|extensions:' | cut -c1-220 | head -n 40 | while read -r l; do k "$l"; done
k "drm: $(grep -E 'fb=|crtc=crtc' /sys/kernel/debug/dri/1/state | head -n 2 | tr '\n' ' ')"
k "gpu freq stats: $(grep -E '^\*? *[0-9]+000000:' /sys/class/devfreq/3d00000.gpu/trans_stat | awk '{print $1, $NF}' | grep -v ' 0$' | tr '\n' ' ')"
