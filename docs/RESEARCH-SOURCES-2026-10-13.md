# Deep research over the project's sources (13 Oct 2026)

> **Status 14 Oct 2026.** Item 3 of the suggestions (the rc7 rebase) is done in q89e, q89f and q89g (13 Oct). Still open
> from this report, and not recorded as done in the sources (unverified): the CodeLinaro `kaanapali` scan; the Adreno GMU
> level check (all 19 OPPs) and the HFI-24 patch; the re-checks of the SoCCP, C-PHY, QMI and GPU DT series at the v7.3
> final rebase. The DPU DMA REC fix is already in the tree (no action).


Question: what is new in the listed sources that the Pad 4 port lacks (A), and what is the upstream status of the
patches / bugs we carry or track (B). Workflow run wf_889ba4b6-6b7: 107 agents, 24 sources fetched, 95 claims, 25 verified
(3-vote adversarial), 22 confirmed, 3 refuted. Coverage is NARROW: most listed sources produced no verified claim
(status unknown, not "nothing new").

## Verified findings, checked against our q89e tree (v7.3-rc7, up3-qe1-rc7 a9bb76144dab)

| Item | Status (verified) | Our tree | Action |
|---|---|---|---|
| Kaanapali DPU 13.0 catalog (83fe2cd56b1d), SSPP sub-blocks (688c7734002a), writeback | in mainline since v7.0-rc4 (3-0) | inherited from upstream; no copy in our queue | nothing to drop |
| DSI PHY revision fix (Pengyu Luo, drm-msm-fixes-2026-03-06) | in v7.0-rc7 (3-0 / 2-1) | inherited | nothing to drop |
| Later fixes "Kaanapali CWB register configuration" (May 2026), "DMA SSPP REC offsets on DPU v13" (31 Jul 2026) | upstream | DMA REC fix present (_DMA_SBLK_V13, per the QCOM-LINUX-KERNEL review); CWB fix to confirm | check CWB at the next rebase |
| Adreno 840 DT v2 (Akhil P Oommen, 8 patches, 5 Jul 2026; all author sign-offs) | pending | our DT has the GPU / GMU / SMMU nodes (adreno-44050a01, gmu-840.1, kaanapali-smmu-500) with 19 GPU OPPs | TRY its driver patch "a6xx: Increase HFI GX perf level limit to 24": our tree's legacy HFI table is 16 levels; the a8xx path builds a variable table (GMU_MAX_GX_FREQS 32), so check whether all 19 levels reach the GMU (no truncation warning seen in r141) |
| SoCCP late-attach v7 (Jingyi Wang, 23 Jun 2026) | pending, no v8 / Applied found; v6 review points open | carried | keep |
| QMI TMD remoteproc cooling (Gaurav Kohli / Casey Connolly lineage) | pending; we carry v8 (Aug 2026) = the newest found | carried | keep |
| qcom C-PHY v9 (David Heidelberg; Reviewed-by the CAMSS maintainer) | pending, no v10 | carried | keep |
| Kaanapali CAMSS / CCI DT v2 (Hangxiang Ma, 21 Jul 2026) | pending; needs CAMSS driver v15 (20 Jul) | not needed: our cameras run | SKIP for now (churn; v1 was applied then backed out) |
| libcamera stop-cleanup (patchwork 21825, commit 2cbf863f, Nov 2024) | merged, in 0.4+ incl. Fedora 0.7.1 | - | the 2026 race (#320 / #335 / #319) is separate and unfixed upstream; r152: Fedora 0.7.1-2 avoids the trigger (in-process IPA) |

Refuted (1-2 or 0-3): "the whole display path incl. DSI / MDSS was in v7.0-rc4", "Adreno 840 GPU DT v1 not mergeable,
depends on Glymur GPU DT", "Adreno 840 support as a8xx v3 patch 15/20 with sign-off".

## Not answered by this run (open)
SuperTurtleDev kernel / firmware since d0c0f18; map220v; infiniti-mainline linux / u-boot; Xlie; tb323fu; gts6l;
Robotix22; OnePlusOSS trees; CodeLinaro kaanapali (= the queued R2 scan); Mu-Silicium / Silicium-ACPI / WOA drivers;
hexagonrpc; libssc; iio-sensor-proxy; AudioReach; Fedora libcamera 0.7.1-2 stable status; PipeWire 2669; drm/msm work
item 100; GStreamer v4l2 BT.601 (we are fixing it in the kernel driver); PMIC glink suspend v3; remoteproc dtb; gpucc
voteable (dropped from q89e: merged in rc7 as 55981579b27b); domain-off; Rob Clark 30 Sep; patchwork.freedesktop
725401/725403, 754331/754332, 755589-755599, 757345, 757683/757684; audio DT / SoundWire 2.2.
"Pending" rests on LKML mirrors (lkml.iu.edu), not lore / subsystem trees: re-check against linux-next.

## Suggested follow-ups
1. R2 (queued): the CodeLinaro kaanapali scan, plus a git-based (not web-search) diff of SuperTurtleDev / map220v /
   infiniti / Xlie trees against our q89e queue - web search cannot answer "what is new in a repo".
2. Adreno 840: check GMU level delivery (all 19 OPPs) and take the HFI-24 patch if levels are cut.
3. Re-check SoCCP v7 / C-PHY v9 / QMI TMD / GPU DT v2 on lore + linux-next at the next rebase (v7.3 final).
