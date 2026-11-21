# Mesa for the OnePlus Pad 4 (Adreno 840)

**Fedora 45 build (21 Nov 2026):** `mesa-26.3.1^git20261120.6cd33b7-1.fc45.iceland1`: Fedora 45's `mesa.spec`
(dist-git f45 `13d08919`, 26.2.6, adapted to 26.3) with Mesa's `staging/26.3` at `6cd33b7f` (26.3.1 + 49 stable fixes)
and 41 patches `9101-*` to `9142-*`: freedreno / turnip / ir3 / vulkan merge requests for the A8xx, and two A8xx GL
hang fixes from the armada distribution. Each patch file keeps its upstream author; numbers 9101-9130 are the same
merge requests as in the previous build (`26.3.0~rc3^git20261104.25248e6`), 9126 is gone (in 26.3.1).

## Source

`mesa-26.3.1-git20261120.6cd33b7.tar.xz` is a `git archive` of Mesa's `staging/26.3` branch at
`6cd33b7f68ee04c5270215591b2d29535af291bd` (tree `51fe67c75056eade1c70f356599b301a6ec2cd92`):

```bash
git init mesa && cd mesa
git fetch --depth 1 https://gitlab.freedesktop.org/mesa/mesa.git 6cd33b7f68ee04c5270215591b2d29535af291bd
git archive --prefix=mesa-26.3.1-git20261120.6cd33b7/ FETCH_HEAD | xz -T0 -9 > mesa-26.3.1-git20261120.6cd33b7.tar.xz
```

The venus protocol 1.1.3 (`Source2`, needed by the virtio Vulkan driver; a `git archive` does not bundle the wrap) and
the Rust crates (`Source10`-`Source15`) download from the URLs in the spec (`spectool -g`); `%prep` unpacks them.

## Build

On Fedora 45 aarch64 (the `mesa-arm64` workflow of this repository does exactly this on a GitHub arm64 runner):

```bash
cp *.patch Mesa-MLAA-License-Clarification-Email.txt mesa-26.3.1-git20261120.6cd33b7.tar.xz ~/rpmbuild/SOURCES/
spectool -g -C ~/rpmbuild/SOURCES mesa.spec
sudo dnf builddep mesa.spec
rpmbuild -ba --define 'dist .fc45' --define 'debug_package %{nil}' mesa.spec
```

The binary RPMs are not published here.

## Patches

Review state as of 21 Nov 2026 (none of the open merge requests is approved upstream yet). "merged" = taken as merged
on Mesa `main` (not in 26.3); "open" = the merge request head named in the file header.

| Patch | Source | State | Review / note | What |
|---|---|---|---|---|
| `9101-mr45525-26-3-backport-tu-a8xx-split-large-indirect-draws.patch` | [!45525](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45525) | open (26.3 backport of merged !44352) | - | 26.3: backport tu/a8xx - split large indirect draws ( !44352) |
| `9102-mr45369-tu-drop-reference-taken-with-get-vis-stream-patc.patch` | [!45369](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45369) | merged | - | tu: Drop reference taken with get_vis_stream_patchpoint_cs() |
| `9103-mr45366-tu-add-back-float16-3d-path-for-multisampled-cop.patch` | [!45366](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45366) | merged | - | tu: Add back float16 3D path for multisampled copies |
| `9104-mr45416-tu-freedreno-modify-hull-shader-programming.patch` | [!45416](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45416) | merged | - | tu,freedreno: modify hull shader programming |
| `9105-mr45342-tu-mark-signed-4x8-integer-dot-products-as-accel.patch` | [!45342](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45342) | merged | - | tu: Mark signed 4x8 integer dot products as accelerated |
| `9106-mr45554-freedreno-record-the-batch-s-write-when-a-query.patch` | [!45554](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45554) | merged | - | freedreno: Record the batch's write when a query ends |
| `9107-mr45506-tu-have-gl-behavior-for-primitive-generated-quer.patch` | [!45506](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45506) | merged | - | tu: Have GL behavior for primitive generated query |
| `9108-mr45464-ir3-better-copy-prop-for-source-modifiers.patch` | [!45464](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45464) | merged | the parts already in 26.3.1 left out | ir3: better copy prop for source modifiers |
| `9109-mr45517-ir3-ra-fix-double-only-register-limit-unit.patch` | [!45517](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45517) | merged | - | ir3/ra: fix DOUBLE_ONLY register limit unit |
| `9110-mr45559-vulkan-sort-per-binding-pnext-data-in-vk-create.patch` | [!45559](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45559) | merged | - | vulkan: sort per-binding pNext data in vk_create_sorted_bindings |
| `9111-mr45601-tu-ir3-fix-a702-regressions.patch` | [!45601](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45601) | merged | the parts already in 26.3.1 left out | tu, ir3: fix a702 regressions |
| `9112-mr43899-turnip-drop-ccu-depth-invalidation-on-occlusion.patch` | [!43899](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/43899) | merged | - | turnip: Drop CCU depth invalidation on occlusion query end |
| `9113-mr45882-freedreno-take-only-in-fence-as-a-hint-for-expli.patch` | [!45882](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45882) | merged | - | freedreno : Take only in fence as a hint for explicit sync |
| `9114-mr45918-tu-lrz-fix-partial-lrz-fast-clear-on-a8xx.patch` | [!45918](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45918) | merged | - | tu/lrz: Fix partial LRZ fast-clear on A8XX |
| `9115-mr45981-freedreno-ir3-lower-fp32-to-fp16-for-subnormals.patch` | [!45981](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45981) | merged | - | freedreno/ir3: Lower FP32 to FP16 for subnormals |
| `9116-mr46027-ir3-only-fold-fsat-to-sat-on-cat2-3-float-instru.patch` | [!46027](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46027) | merged | the parts already in 26.3.1 left out | ir3: only fold fsat to (sat) on cat2/3 float instructions |
| `9117-mr45243-tu-inline-uniform-block-fixes.patch` | [!45243](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45243) | merged | refreshed from the merged commits | tu: Inline uniform block fixes |
| `9118-mr44365-nir-ir3-fix-32-bit-udiv-when-rcp-rounds-up.patch` | [!44365](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/44365) | merged | refreshed from the merged commits | nir,ir3: fix 32-bit udiv when rcp rounds up |
| `9119-mr45937-tu-wfi-before-reading-registers-that-were-just-w.patch` | [!45937](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45937) | merged | refreshed from the merged commits | tu: WFI before reading registers that were just written |
| `9120-mr45985-tu-carry-flush-bits-for-suspended-s-r-chains-bet.patch` | [!45985](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45985) | merged | refreshed from the merged commits | tu: Carry flush bits for suspended s/r chains between command buffers |
| `9121-mr45926-tu-wait-for-vm-bind-unmap-completion-before-free.patch` | [!45926](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45926) | open | - | tu: Wait for VM_BIND unmap completion before freeing resources |
| `9122-mr45904-turnip-preserve-sample-counts-across-gmem-preemp.patch` | [!45904](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45904) | open | - | turnip: Preserve sample counts across GMEM preemption |
| `9123-mr45928-ir3-keep-separate-dominance-stacks-in-merge-sets.patch` | [!45928](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45928) | open | - | ir3: keep separate dominance stacks in merge_sets_interfere |
| `9124-mr46023-ir3-fix-is-ss-sy-producer-and-use-in-legalize.patch` | [!46023](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46023) | open | - | ir3: fix is_{ss,sy}_producer and use in legalize |
| `9125-mr45958-freedreno-ir3-set-api-wavesize-double-only-for-g.patch` | [!45958](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/45958) | merged | refreshed from the merged commits | freedreno/ir3: set api_wavesize=DOUBLE_ONLY for GL non-compute shaders on gen6+ |
| `9127-mr44712-ir3-lower-copies-don-t-split-partially-blocked-c.patch` | [!44712](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/44712) | open | - | ir3/lower_copies: don't split partially blocked copies |
| `9128-mr37924-ir3-add-opt-absneg-pass.patch` | [!37924](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/37924) | open | one-word rename on top (`sat_is_fsat`, after 9116): our change | ir3: add opt_absneg pass |
| `9129-mr43714-tu-don-t-flush-for-sysmem-resolves-if-there-are.patch` | [!43714](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/43714) | open | - | tu: Don't flush for sysmem resolves if there are no resolves |
| `9130-mr43272-tu-synchronize-access-between-no-rast-order-and.patch` | [!43272](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/43272) | open | - | tu: Synchronize access between no-rast-order and rast-order draw calls |
| `9131-mr46456-tu-a8xx-reset-lrz-control-after-flush.patch` | [!46456](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46456) | open | none | tu/a8xx: reset LRZ control after flush |
| `9132-mr46139-tu-a8xx-use-subpass-fence-before-reading-resolve.patch` | [!46139](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46139) | open | discussed, no r-b | tu/a8xx: Use SUBPASS_FENCE before reading resolved into sysmem input attachments in gmem |
| `9133-mr46146-turnip-emit-gpu-patched-vis-stream-packets-into.patch` | [!46146](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46146) | open | r-b (Danylo Piliaiev); one niche case open | turnip: Emit GPU-patched vis stream packets into IB2s |
| `9134-mr46147-turnip-fix-the-fdm-aspect-guard-and-bound-the-fd.patch` | [!46147](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46147) | open | none | turnip: Fix the FDM aspect guard and bound the FDM offset LRZ padding |
| `9135-mr46194-tu-update-input-attachment-idx-when-msrtss-inter.patch` | [!46194](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46194) | open | rb (Emma Anholt) | tu: Update input attachment idx when MSRTSS internal is used |
| `9136-mr46592-tu-mark-dynamic-descriptor-sizes-of-empty-shader.patch` | [!46592](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46592) | open | none | tu: mark dynamic descriptor sizes of empty shaders unknown |
| `9137-mr46182-ir3-array-to-ssa-don-t-resolve-readers-to-delete.patch` | [!46182](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46182) | open | none (maintainer engaged) | ir3/array_to_ssa: don't resolve readers to deleted phis |
| `9138-mr46556-ir3-keep-the-preamble-early-on-gpus-with-early-p.patch` | [!46556](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46556) | open | none (may be subsumed by split preambles) | ir3: keep the preamble early on GPUs with early preamble |
| `9139-mr46398-ir3-sched-allow-a0-x-a1-x-writes-to-be-scheduled.patch` | [!46398](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46398) | open | none (author: ir3 developer) | ir3/sched: allow a0.x/a1.x writes to be scheduled earlier |
| `9140-mr46589-freedreno-a8xx-use-the-a8xx-compute-workgroup-ti.patch` | [!46589](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/46589) | open | none | freedreno/a8xx: use the A8xx compute workgroup tile height |
| `9141-armada0016-freedreno-a8xx-wait-for-zpass-done-sample-count.patch` | [armada #894](https://github.com/armada-os/armada/pull/894) | not upstream | MIT, Armada contributors (see `NOTICE-armada-patches.txt`) | freedreno/a8xx: wait for ZPASS_DONE sample count writes |
| `9142-armada0017-freedreno-a8xx-emit-an-rb-done-ts-event-after-ea.patch` | [armada #894](https://github.com/armada-os/armada/pull/894) | not upstream | MIT, Armada contributors (see `NOTICE-armada-patches.txt`) | freedreno/a8xx: emit an RB_DONE_TS event after each draw |

Not taken on purpose:

- !46240 (gen8 VPC GMEM cache rework) and its fix !46551: both only on Mesa `main`; !46240 alone hangs every
  application on an A840, so neither goes into a 26.3 build.
- !46016 (full sysmem depth CCU cache on X2-90): the A840 device table stays unchanged.

Drop a patch once its merge request is in the Mesa version you build.
