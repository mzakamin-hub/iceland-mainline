# qualcomm-linux/kernel vs the Pad 4 port (deep research, 12 Oct 2026)

> **Status 14 Oct 2026.** Recommendation 3 is done: the Pad 4 kernel is on v7.3-rc7 (queue q89e on 13 Oct, then q89f
> and q89g). The three patches that the rc7 notes named as merged upstream were dropped at the rebase. Recommendations
> 1 and 2 still stand. The sources do not record a new read of the Kaanapali branches after 12 Oct (unverified).


Run wf_3ad3121e-5ba: 103 agents, claims checked by 3-vote verification. The coordinator then checked the findings
against our tree (WSL <pc-work>/build/src, branch iceland).

## What the repo is
- The kernel for **Qualcomm Linux (QLI)**, Qualcomm's embedded / IoT distribution.
  - `main` = a plain mirror of Linus' tree (head 24a19b9 = **v7.3-rc7**).
  - The Qualcomm work sits on side branches:
    - `qcom-next`: aggregates qualcomm-linux/kernel-topics, re-synced at each -rc;
    - `qcom-next-staging(-topics)`;
    - `qcom-7.2`, `qcom-6.19`;
    - the LTS line `qcom-6.18.y` / `qcom-6.18.30` (Yocto recipe linux-qcom_6.18.bb);
    - a debug branch and `staging/nord`.
- **Targets:** QLI only supports IoT / compute boards: QCS6490 RB3 Gen 2, IQ-9075 (Lemans), IQ-8275 (Monaco), QCS615 (Talos). **Kaanapali / SM8850 is not a QLI target.**
- **Commit rules:** the kernel-topics checker accepts only FROMLIST: / FROMGIT: / UPSTREAM: / BACKPORT: subjects. QCLINUX: commits are vendor-only workarounds with no upstream counterpart (e.g. the M.2 EVK Bluetooth regulator hacks reverted in kernel-topics PR #1627).

## Where kaanapali work actually lives
- **Upstream on LKML** (upstream-first, by Qualcomm engineers):
  - GPU Adreno 840 DT v2 (Akhil P Oommen, Jul 2026);
  - DPU 13 / MDSS / DSI v6 (Jan 2026);
  - ADSP / CDSP remoteproc;
  - **the SoCCP late-attach** in qcom_q6v5_pas (v7, 23 Jun 2026, under review) + a SoCCP DT node series (v1, Mar 2026);
  - the audio DT (LPASS macros, LPI TLMM, SoundWire swr0-3, GPR q6apm / q6prm) + a SoundWire v2.2.0 binding;
  - ICE power-domain / iface clock.
- **CodeLinaro kernel-qcom branch `kaanapali`** (git.codelinaro.org/clo/linux-kernel/kernel-qcom/-/tree/kaanapali): Qualcomm's bring-up branch, tested on Kaanapali-MTP. The likeliest place for kaanapali work not yet posted upstream.

## Checked against our tree
- The DPU v13 DMA SSPP REC offset fix (Yongxing Mou, 20 Jul 2026; Fixes 83fe2cd56b1d) is **already in our tree**: `_DMA_SBLK_V13` / `dpu_dma_sblk_v13` in dpu_hw_catalog.c and dpu_13_0_kaanapali.h. PORT-LOG row 22 marks it as already upstream.
- **v7.3-rc7 is tagged** (torvalds tag v7.3-rc7 -> 24a19b953e2a). The owner had kept rc6 because rc7 was not tagged, so the matrix item "the rebase onto v7.3-rc7 / v7.3 when tagged" is now actionable.

## Recommendations
1. **Do not use qualcomm-linux/kernel as a source for this port.**
   - `main` = mainline;
   - `qcom-next` = IoT topics on mainline;
   - QCLINUX: = vendor-only workarounds;
   - 6.18 LTS = backports to an older base.

   At most, an occasional diff of qcom-next against msm-next / the qcom 7.4 trees for FROMLIST commits that touch kaanapali files.
2. **Watch instead:**
   - the SoCCP late-attach series (relevant to our SOCCP);
   - the Adreno 840 DT / GMU series;
   - the audio DT / SoundWire 2.2 series;
   - the CodeLinaro `kaanapali` branch (scan it read-only, the same way as tb323fu / SuperTurtleDev).
3. **The rc7 rebase:** a new item for the owner. One variable, its own rehearsal set, not in the held image.
