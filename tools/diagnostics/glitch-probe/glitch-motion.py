#!/usr/bin/env python3
"""glitch-motion.py SECONDS [OUTFILE] - part of glitch-probe: synthetic screen motion.

A maximized GTK window (GTK 4, else GTK 3; python3-gobject + pycairo as on Fedora Workstation)
that redraws every frame (frame-clock tick callback) for SECONDS seconds and then quits: moving
bars, a moving block over the whole height and a frame counter, so every frame the compositor
composites new content over the whole screen, the lower quarter included. Started and stopped
by glitch-probe by PID; it changes nothing on the system. Prints the frames drawn at the end.
"""
import math
import sys
import time

secs = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
outf = sys.argv[2] if len(sys.argv) > 2 else None

try:
    import gi
    try:
        gi.require_version('Gtk', '4.0')
        from gi.repository import Gtk, GLib
        GTK = 4
    except (ValueError, ImportError):
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, GLib
        GTK = 3
except Exception as e:  # noqa: BLE001 - report any import problem and leave
    print('motion: no GTK through python3-gobject (%s)' % e)
    sys.exit(3)

state = {'frames': 0, 't0': time.monotonic()}


def draw(cr, w, h):
    t = time.monotonic() - state['t0']
    state['frames'] += 1
    hue = (t * 0.25) % 1.0
    cr.set_source_rgb(0.5 + 0.5 * math.sin(6.283 * hue), 0.5 + 0.5 * math.sin(6.283 * hue + 2.1),
                      0.5 + 0.5 * math.sin(6.283 * hue + 4.2))
    cr.paint()
    n = 32
    bw = max(4, w // (2 * n))
    for i in range(n):
        x = (i * w / n + t * 600) % w
        cr.set_source_rgb((i % 3) / 2.0, ((i + 1) % 3) / 2.0, ((i + 2) % 3) / 2.0)
        cr.rectangle(x, 0, bw, h)
        cr.fill()
    # a block that sweeps the whole height, so the lower quarter changes every frame too
    by = (t * 400) % h
    cr.set_source_rgb(1, 1, 1)
    cr.rectangle(0, by, w, h / 12)
    cr.fill()
    for k in range(4):   # checker rows in the lower quarter
        y0 = h * 0.75 + k * h / 16
        for j in range(0, w, 64):
            if ((j // 64) + k + int(t * 30)) % 2:
                cr.set_source_rgb(0, 0, 0)
                cr.rectangle(j, y0, 64, h / 16)
                cr.fill()
    cr.set_source_rgb(0, 0, 0)
    cr.move_to(40, 80)
    cr.set_font_size(48)
    cr.show_text('glitch-probe motion  frame %d' % state['frames'])


def tick(widget, clock, *a):
    widget.queue_draw()
    return True


def finish(*a):
    dt = time.monotonic() - state['t0']
    msg = 'motion: GTK %d, %d frames in %.1f s (%.1f fps)' % (GTK, state['frames'], dt, state['frames'] / max(dt, 0.001))
    print(msg)
    if outf:
        with open(outf, 'a') as f:
            f.write(msg + '\n')
    loop.quit()
    return False


loop = GLib.MainLoop()
if GTK == 4:
    win = Gtk.Window(title='glitch-probe motion')
    area = Gtk.DrawingArea()
    area.set_draw_func(lambda a, cr, w, h, *u: draw(cr, w, h))
    win.set_child(area)
    win.connect('close-request', lambda *a: finish() or False)
else:
    win = Gtk.Window(title='glitch-probe motion')
    area = Gtk.DrawingArea()
    area.connect('draw', lambda a, cr: draw(cr, a.get_allocated_width(), a.get_allocated_height()) or False)
    win.add(area)
    win.connect('delete-event', lambda *a: finish() or False)
area.add_tick_callback(tick)
win.maximize()
if GTK == 4:
    win.present()
else:
    win.show_all()
GLib.timeout_add(int(secs * 1000), finish)
try:   # the probe stops it with SIGTERM: report the frame count first
    import signal
    GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGTERM, finish)
except (AttributeError, ImportError):
    pass
loop.run()
