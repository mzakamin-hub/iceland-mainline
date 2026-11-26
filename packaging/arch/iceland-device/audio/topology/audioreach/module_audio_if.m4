# SPDX-License-Identifier: BSD-3-Clause
# Audio Interface (QAIF) hardware endpoint: MODULE_ID_AUDIO_IF_SINK / SOURCE (TDM, PCM or I2S mode) as the kernel's
# audioreach_audio_if_set_media_format() configures it (PARAM_ID_AUDIO_IF_INTF_CFG + HW_EP_MF + frame duration).
# The slot mask / slots / slot width here are the defaults; the machine driver overrides them from the DT's
# dai-tdm-slot-* properties (q6tdm_set_tdm_slot). All tokens go in one u32 array: the kernel reads one array per
# module and casts to the token's width.
include(`util/util.m4') dnl
dnl AR_MODULE_AUDIO_IF_RX(index, sgidx, container-idx, iid, maxip-ports, max-op-ports, src-port, dst-port,
dnl	qaif-type, intf-idx, fmt, dev-name, dst-iid,
dnl	intf-mode, sync-src, sync-mode, invert-sync-pulse, sync-data-delay, slot-mask, nslots-per-frame, slot-width,
dnl	bit-clk-type, ctrl-data-out-enable, active-lane-mask, frame-sync-rate)
define(`AR_MODULE_AUDIO_IF_RX',
`'
`SectionVendorTuples."NAME_PREFIX.aif_rx$1_tuples" {'
`        tokens "audioreach_tokens"'
`'
`        tuples."word.u32_data" {'
`                AR_TKN_U32_MODULE_INSTANCE_ID STR($4)'
`                AR_TKN_U32_MODULE_ID STR(MODULE_ID_AUDIO_IF_SINK)'
`                AR_TKN_U32_MODULE_MAX_IP_PORTS STR($5)'
`                AR_TKN_U32_MODULE_MAX_OP_PORTS STR($6)'
`                AR_TKN_U32_MODULE_SRC_OP_PORT_ID STR($7)'
`                AR_TKN_U32_MODULE_DST_IN_PORT_ID STR($8)'
`                AR_TKN_U32_MODULE_SRC_INSTANCE_ID STR($4)'
`                AR_TKN_U32_MODULE_DST_INSTANCE_ID STR($13)'
`                AR_TKN_U32_MODULE_HW_IF_TYPE STR($9)'
`                AR_TKN_U32_MODULE_HW_IF_IDX STR($10)'
`                AR_TKN_U32_MODULE_FMT_DATA STR($11)'
`                AR_TKN_U16_MODULE_QAIF_TYPE STR($9)'
`                AR_TKN_U16_MODULE_INTF_MODE STR($14)'
`                AR_TKN_U16_MODULE_SYNC_SRC STR($15)'
`                AR_TKN_U16_MODULE_SYNC_MODE STR($16)'
`                AR_TKN_U16_MODULE_CTRL_INVERT_SYNC_PULSE STR($17)'
`                AR_TKN_U16_MODULE_CTRL_SYNC_DATA_DELAY STR($18)'
`                AR_TKN_U32_MODULE_SLOT_MASK STR($19)'
`                AR_TKN_U16_MODULE_NSLOTS_PER_FRAME STR($20)'
`                AR_TKN_U16_MODULE_SLOT_WIDTH STR($21)'
`                AR_TKN_U16_MODULE_BIT_CLK_TYPE STR($22)'
`                AR_TKN_U16_MODULE_CTRL_DATA_OUT_ENABLE STR($23)'
`                AR_TKN_U32_MODULE_ACTIVE_LANE_MASK STR($24)'
`                AR_TKN_U32_MODULE_FRAME_SYNC_RATE STR($25)'
`                AR_TKN_U8_MODULE_INV_INT_BIT_CLK "0"'
`                AR_TKN_U8_MODULE_INV_EXT_BIT_CLK "0"'
`        }'
`}'
`'
`SectionData."NAME_PREFIX.aif_rx$1_data" {'
`        tuples "NAME_PREFIX.aif_rx$1_tuples"'
`}'
`'
`SectionWidget."NAME_PREFIX.aif_rx$1" {'
`        index STR($1)'
`        type "aif_in"'
`        no_pm "true"'
`        stream_name "$12 TDM0 Playback"'
`        subseq "10"'
`        data ['
`                "NAME_PREFIX.sub_graph$2_data"'
`                "NAME_PREFIX.container$3_data"'
`                "NAME_PREFIX.aif_rx$1_data"'
`        ]'
`}') dnl
