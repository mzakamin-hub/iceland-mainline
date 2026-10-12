# SPDX-License-Identifier: BSD-3-Clause
# Copyright, Linaro Ltd, 2023
include(`audioreach/audioreach.m4')
include(`audioreach/stream-subgraph.m4')
include(`audioreach/device-subgraph.m4')
include(`util/route.m4')
include(`util/mixer.m4')
include(`audioreach/tokens.m4')
dnl
dnl OnePlus Pad 4: the stream gain into the speakers (MultiMedia1/2/5 -> PRIMARY_TDM_RX_0 -> 6x TFA9865) is capped.
dnl Q13 linear gain, 8192 = 0 dB. 0.27r6 (owner, 11 Oct 2026): the cap is STOCK's ceiling, 8192 = 0 dB (stock's PAL sets
dnl the stream volume as a linear 0..1.0 factor: odm resourcemanager.xml config_volume; never above unity), raised from
dnl the -12 dB placeholder 2056; the protection is the PipeWire chain in front (62-iceland-speakers.conf). The kernel
dnl keeps writes and the power-up gain within this maximum (audioreach: keep the volume control within the topology's
dnl maximum). Never above stock: tests/test_stock_levels.py.
define(`VOL_CTRL_MAX', `8192')dnl
#
# Stream SubGraph  for MultiMedia Playback
#
#  ______________________________________________
# |               Sub Graph 1                    |
# | [WR_SH] -> [PCM DEC] -> [PCM CONV] -> [LOG]  |- Kcontrol
# |______________________________________________|
#
dnl Playback MultiMedia1
STREAM_SG_PCM_ADD(audioreach/subgraph-stream-vol-playback-capped.m4, FRONTEND_DAI_MULTIMEDIA1,
	`S16_LE', 48000, 48000, 2, 2,
	0x00004001, 0x00004001, 0x00006001, `110000')
dnl Playback MultiMedia2
STREAM_SG_PCM_ADD(audioreach/subgraph-stream-vol-playback-capped.m4, FRONTEND_DAI_MULTIMEDIA2,
	`S16_LE', 48000, 48000, 2, 2,
	0x00004002, 0x00004002, 0x00006010, `110000')
dnl Capture MultiMedia3
STREAM_SG_PCM_ADD(audioreach/subgraph-stream-capture.m4, FRONTEND_DAI_MULTIMEDIA3,
	`S16_LE', 48000, 48000, 1, 2,
	0x00004003, 0x00004003, 0x00006020, `110000')
dnl Capture MultiMedia4
STREAM_SG_PCM_ADD(audioreach/subgraph-stream-capture.m4, FRONTEND_DAI_MULTIMEDIA4,
	`S16_LE', 48000, 48000, 1, 2,
	0x00004004, 0x00004004, 0x00006030, `110000')
dnl Playback MultiMedia5
STREAM_SG_PCM_ADD(audioreach/subgraph-compress-stream-vol-playback-capped.m4, FRONTEND_DAI_MULTIMEDIA5,
	`S16_LE', 48000, 48000, 2, 2,
	0x0000400a, 0x0000400a, 0x00006040, `110000')
dnl Playback MultiMedia6 - for DisplayPort RX 0
STREAM_SG_PCM_ADD(audioreach/subgraph-stream-vol-playback.m4, FRONTEND_DAI_MULTIMEDIA6,
	`S16_LE', 48000, 48000, 2, 2,
	0x0000400b, 0x0000400b, 0x000060A0, `110000')
#
#
# Device SubGraph  for WSA RX0 Backend
#
#         ___________________
#        |   Sub Graph 2     |
# Mixer -| [LOG] -> [WSA EP] |
#        |___________________|
#
dnl DEVICE_SG_ADD(stream, stream-dai-id, stream-index,
dnl 	format, min-rate, max-rate, min-channels, max-channels,
dnl	interface-type, interface-index, data-format,
dnl	sg-iid-start, cont-iid-start, mod-iid-start
dnl WSA Playback
DEVICE_SG_ADD(audioreach/subgraph-device-codec-dma-playback.m4, `WSA_CODEC_DMA_RX_0', WSA_CODEC_DMA_RX_0,
	`S16_LE', 48000, 48000, 2, 2,
	LPAIF_INTF_TYPE_WSA, CODEC_INTF_IDX_RX0, 0, DATA_FORMAT_FIXED_POINT,
	0x00004005, 0x00004005, 0x00006050)
dnl
dnl Primary TDM Playback: the OnePlus Pad 4 speakers (six TFA9865 as TDM slaves) on the stock back end
dnl TDM-LPAIF-RX-PRIMARY, classic TDM sink module; every value below is the stock ACDB's for this endpoint:
dnl 8 slots x 32 bit, 48 kHz, LPASS drives the frame sync (internal), data-out enable, long sync mode, no
dnl inversion, 1-cycle data delay.
define(`TDM_SYNC_SRC', `1') dnl TDM_SYNC_SRC_INTERNAL
define(`TDM_CTRL_DATA_OE', `1') dnl
define(`TDM_SLOT_MASK', `0xff') dnl
define(`TDM_NSLOTS', `8') dnl
define(`TDM_SLOT_WIDTH', `32') dnl
define(`TDM_SYNC_MODE', `1') dnl TDM_LONG_SYNC_MODE
define(`TDM_INVERT_SYNC', `0') dnl
define(`TDM_DATA_DELAY', `1') dnl
DEVICE_SG_ADD(audioreach/subgraph-device-tdm-playback.m4, `Primary', PRIMARY_TDM_RX_0,
	`S32_LE', 48000, 48000, 8, 8,
	LPAIF_INTF_TYPE_LPAIF, I2S_INTF_TYPE_PRIMARY, 0, DATA_FORMAT_FIXED_POINT,
	0x00004006, 0x00004006, 0x00006060, `PRIMARY_TDM_RX_0')
dnl
dnl WCDRX Playback
DEVICE_SG_ADD(audioreach/subgraph-device-codec-dma-playback.m4, `RX_CODEC_DMA_RX_0', RX_CODEC_DMA_RX_0,
	`S16_LE', 48000, 48000, 2, 2,
	LPAIF_INTF_TYPE_RXTX, CODEC_INTF_IDX_RX0, 0, DATA_FORMAT_FIXED_POINT,
	0x00004007, 0x00004007, 0x00006070)
dnl
dnl VA Capture
DEVICE_SG_ADD(audioreach/subgraph-device-codec-dma-capture.m4, `VA_CODEC_DMA_TX_0', VA_CODEC_DMA_TX_0,
	`S16_LE', 48000, 48000, 1, 2,
	LPAIF_INTF_TYPE_VA, CODEC_INTF_IDX_TX0, 0, DATA_FORMAT_FIXED_POINT,
	0x00004008, 0x00004008, 0x00006080)
dnl
dnl WCDTX Capture
DEVICE_SG_ADD(audioreach/subgraph-device-codec-dma-capture.m4, `TX_CODEC_DMA_TX_3', TX_CODEC_DMA_TX_3,
	`S16_LE', 48000, 48000, 1, 2,
	LPAIF_INTF_TYPE_RXTX, CODEC_INTF_IDX_TX3, 0, DATA_FORMAT_FIXED_POINT,
	0x00004009, 0x00004009, 0x00006090)
dnl
dnl Display port0 Playback
DEVICE_SG_ADD(audioreach/subgraph-device-display-port-playback.m4, `DISPLAY_PORT_RX_0', DISPLAY_PORT_RX_0,
	`S16_LE', 48000, 48000, 2, 2,
	0, 0, 0, DATA_FORMAT_FIXED_POINT,
	0x00004010, 0x00004010, 0x000060B0, `DISPLAY_PORT_RX_0')
dnl

STREAM_DEVICE_PLAYBACK_MIXER(WSA_CODEC_DMA_RX_0, ``WSA_CODEC_DMA_RX_0'', ``MultiMedia1'', ``MultiMedia2'', ``MultiMedia5'')
STREAM_DEVICE_PLAYBACK_MIXER(PRIMARY_TDM_RX_0, ``PRIMARY_TDM_RX_0'', ``MultiMedia1'', ``MultiMedia2'', ``MultiMedia5'')
STREAM_DEVICE_PLAYBACK_MIXER(RX_CODEC_DMA_RX_0, ``RX_CODEC_DMA_RX_0'', ``MultiMedia1'', ``MultiMedia2'', ``MultiMedia5'')
dnl DisplayPort mixer
STREAM_DEVICE_PLAYBACK_MIXER(DISPLAY_PORT_RX_0, ``DISPLAY_PORT_RX_0'', ``MultiMedia5'', ``MultiMedia6'')

STREAM_DEVICE_PLAYBACK_ROUTE(WSA_CODEC_DMA_RX_0, ``WSA_CODEC_DMA_RX_0 Audio Mixer'', ``MultiMedia1, stream0.logger1'', ``MultiMedia2, stream1.logger1'', ``MultiMedia5, stream4.logger1'')
STREAM_DEVICE_PLAYBACK_ROUTE(PRIMARY_TDM_RX_0, ``PRIMARY_TDM_RX_0 Audio Mixer'', ``MultiMedia1, stream0.logger1'', ``MultiMedia2, stream1.logger1'', ``MultiMedia5, stream4.logger1'')
STREAM_DEVICE_PLAYBACK_ROUTE(RX_CODEC_DMA_RX_0, ``RX_CODEC_DMA_RX_0 Audio Mixer'', ``MultiMedia1, stream0.logger1'', ``MultiMedia2, stream1.logger1'', ``MultiMedia5, stream4.logger1'')
STREAM_DEVICE_PLAYBACK_ROUTE(DISPLAY_PORT_RX_0, ``DISPLAY_PORT_RX_0 Audio Mixer'', ``MultiMedia5, stream4.logger1'', ``MultiMedia6, stream5.logger1'')

dnl STREAM_DEVICE_CAPTURE_MIXER(stream-index, kcontro1, kcontrol2... kcontrolN)
STREAM_DEVICE_CAPTURE_MIXER(FRONTEND_DAI_MULTIMEDIA3, ``VA_CODEC_DMA_TX_0'',``TX_CODEC_DMA_TX_3'' )
STREAM_DEVICE_CAPTURE_MIXER(FRONTEND_DAI_MULTIMEDIA4, ``VA_CODEC_DMA_TX_0'',``TX_CODEC_DMA_TX_3'' )
dnl STREAM_DEVICE_CAPTURE_ROUTE(stream-index, mixer-name, route1, route2.. routeN)
STREAM_DEVICE_CAPTURE_ROUTE(FRONTEND_DAI_MULTIMEDIA3, ``MultiMedia3 Mixer'', ``VA_CODEC_DMA_TX_0, device110.logger1'', ``TX_CODEC_DMA_TX_3, device120.logger1'')
STREAM_DEVICE_CAPTURE_ROUTE(FRONTEND_DAI_MULTIMEDIA4, ``MultiMedia4 Mixer'', ``VA_CODEC_DMA_TX_0, device110.logger1'', ``TX_CODEC_DMA_TX_3, device120.logger1'')
