#!/usr/bin/env python3
"""glitch-analyze.py OUTDIR - part of glitch-probe (OnePlus Pad 4 lower-quarter flicker).

Reads the stage traces / snapshots written by glitch-probe.sh and prints one row per stage
plus a 'glitch y vs n' comparison. Standard library only; it reads files, nothing else.

Per stage (from the tracefs instance):
  vbl      DPU vblank callbacks (dpu_crtc_vblank_cb) and the frame period
  gaps     vblank intervals > 1.5 periods (vsync irq off: encoder idle or vblank off)
  jit_us   largest vblank-callback jitter (irq latency) within normal intervals
  commits  msm_atomic_commit_tail_start (non-async)
  late%    CTL flushes (msm_atomic_flush_commit) written in the last 15 % of a frame
  miss     flushes that took more than one extra frame to latch (wait_flush too long)
  busy     dpu_hw_ctl_trigger_pending_flush with CTL_FLUSH != 0 (a new flush while the
           previous one is still pending -> half-latched frame possible)
  wfmax    longest wait_flush in ms
  skip     drm vblank event sequence jumps > 1 (frames mutter did not present)
  fdtmo    dpu_enc_frame_done_timeout, under = dpu_enc_underrun_cb
  idle     encoder ENTER_IDLE (rc_state 4) transitions, irqoff = phys vid irq disables
  bwrel    bandwidth release / perf updates, icc0 = MDP icc votes with avg 0
  deep%    time the MDSS-irq CPU spent in its deepest idle state
From the before / after snapshots: mdssirq / touch / adspirq interrupt deltas.
"""
import os
import re
import statistics
import sys

LINE = re.compile(r'^\s*(?P<comm>.+?)-(?P<pid>\d+)\s+(?:\(\s*\S+\)\s+)?\[(?P<cpu>\d+)\]\s+(?:\S+\s+)?'
                  r'(?P<ts>\d+\.\d+):\s+(?P<ev>[\w:]+):\s?(?P<rest>.*)$')
KV = re.compile(r'(\w[\w-]*)[=:]\s*(0x[0-9a-fA-F]+|-?\d+|\S+)')


def parse(path):
    evs = []
    try:
        with open(path, errors='replace') as f:
            for ln in f:
                if ln.startswith('#'):
                    continue
                m = LINE.match(ln)
                if not m:
                    continue
                evs.append((float(m['ts']), int(m['cpu']), m['ev'], m['rest']))
    except OSError:
        pass
    evs.sort(key=lambda e: e[0])
    return evs


def kv(rest):
    return {k: v for k, v in KV.findall(rest)}


def toint(v, default=0):
    try:
        return int(v, 0)
    except (TypeError, ValueError):
        return default


def analyse(evs):
    r = {}
    vbl = [e[0] for e in evs if e[2] == 'dpu_crtc_vblank_cb']
    r['vbl'] = len(vbl)
    d = [b - a for a, b in zip(vbl, vbl[1:])]
    short = [x for x in d if x < 0.050]
    per = statistics.median(short) if short else 0.0
    r['per_ms'] = per * 1000
    r['gaps'] = sum(1 for x in d if per and x > 1.5 * per)
    jit = [abs(x - per) for x in d if per and x <= 1.5 * per]
    r['jit_us'] = max(jit) * 1e6 if jit else 0.0

    def phase(t):
        # position of t in its frame (0 = just after a vblank callback, 1 = next one)
        if not per or not vbl:
            return None
        lo, hi = 0, len(vbl) - 1
        if t < vbl[0]:
            return None
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if vbl[mid] <= t:
                lo = mid
            else:
                hi = mid - 1
        return ((t - vbl[lo]) % per) / per

    commits = [e for e in evs if e[2] == 'msm_atomic_commit_tail_start' and kv(e[3]).get('async', '0') == '0']
    r['commits'] = len(commits)
    flushes = [e[0] for e in evs if e[2] == 'msm_atomic_flush_commit']
    ph = [p for p in (phase(t) for t in flushes) if p is not None]
    r['late_pct'] = 100.0 * sum(1 for p in ph if p > 0.85) / len(ph) if ph else 0.0
    hist = [0] * 10
    for p in ph:
        hist[min(9, int(p * 10))] += 1
    r['hist'] = hist
    # wait_flush pairs
    waits, start = [], None
    for e in evs:
        if e[2] == 'msm_atomic_wait_flush_start':
            start = e[0]
        elif e[2] == 'msm_atomic_wait_flush_finish' and start is not None:
            waits.append((start, e[0] - start))
            start = None
    r['wfmax_ms'] = max((w for _, w in waits), default=0.0) * 1000
    miss = 0
    for t, w in waits:
        p = phase(t)
        if per and p is not None and w > (1.0 - p) * per + 0.35 * per:
            miss += 1
    r['miss'] = miss
    busy = 0
    for e in evs:
        if e[2] == 'dpu_hw_ctl_trigger_pending_flush':
            if toint(kv(e[3]).get('CTL_FLUSH'), 0) != 0:
                busy += 1
    r['busy'] = busy
    seqs = [toint(kv(e[3]).get('seq')) for e in evs if e[2] == 'drm_vblank_event']
    r['flips'] = len(seqs)
    r['skip'] = sum(1 for a, b in zip(seqs, seqs[1:]) if b - a > 1)
    cnt = {}
    for e in evs:
        cnt[e[2]] = cnt.get(e[2], 0) + 1
    r['fdtmo'] = cnt.get('dpu_enc_frame_done_timeout', 0)
    r['under'] = cnt.get('dpu_enc_underrun_cb', 0)
    r['more'] = cnt.get('dpu_crtc_frame_event_more_pending', 0)
    r['done'] = cnt.get('dpu_crtc_frame_event_done', 0)
    r['idle'] = sum(1 for e in evs if e[2] == 'dpu_enc_rc' and 'rc_state:4' in e[3].replace(' ', ''))
    r['irqoff'] = cnt.get('dpu_enc_phys_vid_irq_disable', 0)
    r['bwrel'] = cnt.get('dpu_cmd_release_bw', 0)
    r['perf'] = cnt.get('dpu_perf_crtc_update', 0)
    icc0 = 0
    for e in evs:
        if e[2] == 'icc_set_bw' and re.search(r'mdp|display|mdss', e[3]):
            if toint(kv(e[3]).get('avg_bw'), -1) == 0:
                icc0 += 1
    r['icc0'] = icc0
    r['crtc_dis'] = cnt.get('dpu_crtc_disable', 0)
    r['crtc_en'] = cnt.get('dpu_crtc_enable', 0)
    # idle residency of the irq cpu (power:cpu_idle state=N entry, 4294967295 exit)
    idle_t, deep_t, cur, since = 0.0, 0.0, None, None
    states = set()
    t_first = evs[0][0] if evs else 0.0
    t_last = evs[-1][0] if evs else 0.0
    for e in evs:
        if e[2] != 'cpu_idle':
            continue
        st = toint(kv(e[3]).get('state'), -1)
        if st == 4294967295 or st < 0:
            if cur is not None and since is not None:
                idle_t += e[0] - since
                if cur == max(states):
                    deep_t += e[0] - since
            cur, since = None, None
        else:
            states.add(st)
            cur, since = st, e[0]
    span = t_last - t_first
    r['deep_pct'] = 100.0 * deep_t / span if span > 0 and states else 0.0
    r['idle_pct'] = 100.0 * idle_t / span if span > 0 and states else 0.0
    irq = [e for e in evs if e[2] == 'irq_handler_entry']
    cpus = {}
    for e in irq:
        cpus[e[1]] = cpus.get(e[1], 0) + 1
    r['irqcpu'] = ','.join('%d:%d' % kv_ for kv_ in sorted(cpus.items())) or '-'
    r['overrun'] = 0
    # DPU core clock votes (dpu_core_perf_update_clk: dev, stop_req, clk_rate) and CRTC enables
    r['clk'] = [(e[0], toint(kv(e[3]).get('clk_rate'))) for e in evs
                if e[2] == 'dpu_core_perf_update_clk' and kv(e[3]).get('stop_req', 'false') != 'true'
                and toint(kv(e[3]).get('clk_rate')) > 0]
    r['enables'] = [e[0] for e in evs if e[2] == 'dpu_crtc_enable']
    r['first_ts'] = evs[0][0] if evs else 0.0
    r['under_ts'] = [e[0] for e in evs if e[2] == 'dpu_enc_underrun_cb']
    r['fdtmo_ts'] = [e[0] for e in evs if e[2] == 'dpu_enc_frame_done_timeout']
    return r


def verdict(r):
    """objective per-stage verdict -> (word, reasons)"""
    bad, sus = [], []
    if r['under']:
        bad.append('underrun_cb %d' % r['under'])
    if r['fdtmo']:
        bad.append('frame-done timeout %d' % r['fdtmo'])
    if r.get('newcd'):
        bad.append('new display devcoredump %d' % r['newcd'])
    if r['busy']:
        bad.append('CTL flush while previous pending %d' % r['busy'])
    if r['flips'] and r['skip'] > max(3, 0.05 * r['flips']):
        sus.append('missed presentations %d/%d' % (r['skip'], r['flips']))
    if r['commits'] and r['miss'] > max(3, 0.05 * r['commits']):
        sus.append('late latches %d/%d' % (r['miss'], r['commits']))
    if r['jit_us'] > 1000:
        sus.append('vblank irq jitter %.0f us' % r['jit_us'])
    if r['wfmax_ms'] > 3 * max(r['per_ms'], 1):
        sus.append('wait_flush max %.1f ms' % r['wfmax_ms'])
    if r['vbl'] == 0 and r['commits'] == 0:
        return 'NO-DATA', ['no display events traced']
    if bad:
        return 'GLITCH-EVIDENCE', bad + sus
    if sus:
        return 'SUSPECT', sus
    return 'CLEAN', []


def irq_counts(path):
    """irq lines of a snapshot -> {name-or-number: total}"""
    res = {}
    try:
        with open(path, errors='replace') as f:
            for ln in f:
                if not ln.startswith('irq '):
                    continue
                parts = ln.split()
                tot = toint(parts[-1].split('=')[1]) if parts[-1].startswith('SUM=') else 0
                num = parts[1].rstrip(':')
                name = ' '.join(p for p in parts[2:-1] if not p.isdigit())
                res[num + ' ' + name] = tot
    except OSError:
        pass
    return res


def snap_deltas(base, r):
    b = irq_counts(base + '.before')
    a = irq_counts(base + '.after')
    touch = mdss = adsp = 0
    for k, v in a.items():
        d = v - b.get(k, v)
        lk = k.lower()
        if re.search(r'nt36|novatek|touch|geni|spi', lk):
            touch += d
        if (MDSS_PARENT and lk.split()[0] == MDSS_PARENT) or (not MDSS_PARENT and re.search(r' msm$', lk)):
            mdss += d
        if re.search(r'glink|smp2p|ipcc|adsp|qrtr|fastrpc', lk):
            adsp += d
    r['touch'] = touch
    r['mdssirq'] = mdss
    r['adspirq'] = adsp
    r['newcd'] = len(devcds(base + '.after') - devcds(base + '.before'))
    r['clk_snap'] = core_clk(base + '.before')


def devcds(path):
    res = set()
    try:
        with open(path, errors='replace') as f:
            for ln in f:
                if ln.startswith('devcoredump ') and re.search(r'display|mdss|dsi', ln):
                    res.add(ln.split()[1])
    except OSError:
        pass
    return res


def core_clk(path):
    try:
        with open(path, errors='replace') as f:
            for ln in f:
                if ln.startswith('core_perf/core_clk_rate:'):
                    return toint(ln.split(':', 1)[1].strip())
    except OSError:
        pass
    return 0


MDSS_PARENT = ''


def k1_verdict(out, stages):
    """K1 = the enable commit after a blank votes the DPU core clock from the mode only.
    Compare the first clock vote after the blank's CRTC enable with phase A's steady vote and
    look for display errors at / after that enable."""
    lines = ['K1 test (DPU core clock at the CRTC enable after the blank vs phase A):']
    a_rates = [c for ph, n, k, ans, r in stages if ph == 'A' for _, c in r['clk']]
    a_ref = max(a_rates) if a_rates else 0
    src = 'phase A clock votes (trace)'
    if not a_ref:
        snaps = [r['clk_snap'] for ph, n, k, ans, r in stages if ph == 'A' and r['clk_snap']]
        a_ref = max(snaps) if snaps else 0
        src = 'phase A core_perf/core_clk_rate (debugfs)'
    bt = os.path.join(out, 'blank.trace')
    if not os.path.exists(bt):
        lines.append('  no blank trace (phase B not run or --blank none)')
        lines.append('K1: UNDECIDED (no blank)')
        return '\n'.join(lines)
    b = analyse(parse(bt))
    b_base = os.path.join(out, 'blank')
    newcd = len(devcds(b_base + '.after') - devcds(b_base + '.before'))
    dm = 0
    try:
        with open(b_base + '.dmesg', errors='replace') as f:
            dm = sum(1 for ln in f if re.search(r'underrun|frame done timeout|reset fail|timeout', ln, re.I))
    except OSError:
        pass
    en = b['enables'][-1] if b['enables'] else None
    en_clk = 0
    if en is not None:
        after = [c for t, c in b['clk'] if t >= en]
        en_clk = after[0] if after else 0
    blank_err = b['under'] + b['fdtmo'] + newcd + dm
    b_err = sum(1 for ph, n, k, ans, r in stages if ph == 'B' and r.get('verdict') == 'GLITCH-EVIDENCE')
    a_err = sum(1 for ph, n, k, ans, r in stages if ph == 'A' and r.get('verdict') == 'GLITCH-EVIDENCE')
    lines.append('  phase A reference clock: %s Hz (%s)' % (a_ref or '?', src))
    lines.append('  blank: crtc enable %s, first clock vote after it: %s Hz' % ('seen' if en is not None else 'NOT seen', en_clk or '?'))
    lines.append('  errors in the blank window: underrun_cb %d, frame-done timeout %d, new devcoredump %d, dmesg %d'
                 % (b['under'], b['fdtmo'], newcd, dm))
    lines.append('  stages with GLITCH-EVIDENCE: phase A %d, phase B %d' % (a_err, b_err))
    if en is None or not en_clk or not a_ref:
        res = 'UNDECIDED (no enable or no clock vote traced)'
    elif en_clk < 0.98 * a_ref:
        if blank_err or b_err > a_err:
            res = 'CONFIRMED (enable clock %.0f%% of phase A, with display errors after the enable)' % (100.0 * en_clk / a_ref)
        else:
            res = 'UNDECIDED (enable clock lower, %.0f%% of phase A, but no display error followed)' % (100.0 * en_clk / a_ref)
    else:
        res = 'NOT CONFIRMED (enable clock already at the phase A level%s)' % (
            '; the errors after the enable have another cause' if blank_err or b_err > a_err else '')
    lines.append('K1: ' + res)
    return '\n'.join(lines)


def main():
    global MDSS_PARENT
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    try:
        with open(os.path.join(out, 'summary.txt'), errors='replace') as f:
            m = re.search(r'gic-parent=(\d+)', f.read())
            MDSS_PARENT = m.group(1) if m else ''
    except OSError:
        pass
    stages = []
    for fn in sorted(os.listdir(out)):
        m = re.match(r'^([AB])-(\d\d)-(.+)\.trace$', fn)
        if not m:
            continue
        base = os.path.join(out, fn[:-6])
        ans = '-'
        try:
            with open(base + '.answer') as f:
                ans = f.read().strip() or '-'
        except OSError:
            pass
        evs = parse(os.path.join(out, fn))
        r = analyse(evs)
        snap_deltas(base, r)
        try:
            with open(os.path.join(out, fn)) as f:
                for ln in f:
                    if ln.startswith('# per-cpu overrun:'):
                        r['overrun'] = toint(ln.split(':')[1].strip())
        except OSError:
            pass
        stages.append((m[1], int(m[2]), m[3], ans, r))
    if not stages:
        print('no stage traces found in', out)
        return 1
    cols = [('vbl', '%5d'), ('per_ms', '%6.2f'), ('gaps', '%4d'), ('jit_us', '%6.0f'), ('commits', '%6d'),
            ('late_pct', '%5.1f'), ('miss', '%4d'), ('busy', '%4d'), ('wfmax_ms', '%6.1f'), ('skip', '%4d'),
            ('fdtmo', '%5d'), ('under', '%5d'), ('more', '%4d'), ('idle', '%4d'), ('irqoff', '%6d'),
            ('bwrel', '%5d'), ('icc0', '%4d'), ('deep_pct', '%5.1f'), ('mdssirq', '%6d'), ('touch', '%6d'),
            ('adspirq', '%6d')]
    print('glitch-analyze: %d stages in %s' % (len(stages), out))
    print('%-26s %-3s ' % ('stage', 'gl') + ' '.join('%6s' % c[0][:6] for c in cols))
    for ph, n, kind, ans, r in stages:
        print('%-26s %-3s ' % ('%s-%02d-%s' % (ph, n, kind), ans) +
              ' '.join('%6s' % (fmt % r[c]) for c, fmt in cols))
    print()
    print('flush phase histogram (10 bins of a frame, 0 = right after vblank):')
    for ph, n, kind, ans, r in stages:
        print('  %-26s %s  irq cpu:%s  trace overrun:%d crtc dis/en:%d/%d' %
              ('%s-%02d-%s' % (ph, n, kind), ' '.join('%3d' % h for h in r['hist']), r['irqcpu'],
               r['overrun'], r['crtc_dis'], r['crtc_en']))
    yes = [r for *_, ans, r in stages if ans == 'y']
    no = [r for *_, ans, r in stages if ans == 'n']
    print()
    if yes and no:
        print('glitch y (%d stages) vs n (%d stages): mean per stage' % (len(yes), len(no)))
        for c, _ in cols:
            my = statistics.mean(r[c] for r in yes)
            mn = statistics.mean(r[c] for r in no)
            flag = ''
            if (my > 0 or mn > 0) and (my >= 2 * mn + 1 or mn >= 2 * my + 1):
                flag = '  <-- differs'
            print('  %-9s y=%10.2f  n=%10.2f%s' % (c, my, mn, flag))
    else:
        print('need stages answered both y and n for the comparison')
    print()
    print('automatic verdict per stage (objective metrics only):')
    for ph, n, kind, ans, r in stages:
        word, why = verdict(r)
        r['verdict'] = word
        print('  %-26s %-15s %s' % ('%s-%02d-%s' % (ph, n, kind), word, '; '.join(why)))
    print()
    print(k1_verdict(out, stages))
    print()
    print('reading guide:')
    print('  under>0 in y stages            -> DPU fetch starvation (bandwidth / QoS / DDR); see the .icc files')
    print('  busy>0 or miss/late% high in y  -> commit timing: a flush lands at / after the latch point')
    print('  fdtmo>0 / gaps with frames due  -> frame-done / vsync irq accounting (0314/0315 area)')
    print('  jit_us high, deep% high in y    -> irq latency of the MDSS cpu (idle depth / affinity)')
    print('  all equal y vs n, skip high     -> compositor side (mutter frame scheduling / buffers)')
    print('  y only in finger stages, touch irq high, n in *-pointer -> panel / touch (TDDI) side')
    return 0


if __name__ == '__main__':
    sys.exit(main())
