// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2024.1 (64-bit)
// Tool Version Limit: 2024.05
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
// control
// 0x00 : Control signals
//        bit 0  - ap_start (Read/Write/COH)
//        bit 1  - ap_done (Read/COR)
//        bit 2  - ap_idle (Read)
//        bit 3  - ap_ready (Read/COR)
//        bit 7  - auto_restart (Read/Write)
//        bit 9  - interrupt (Read)
//        others - reserved
// 0x04 : Global Interrupt Enable Register
//        bit 0  - Global Interrupt Enable (Read/Write)
//        others - reserved
// 0x08 : IP Interrupt Enable Register (Read/Write)
//        bit 0 - enable ap_done interrupt (Read/Write)
//        bit 1 - enable ap_ready interrupt (Read/Write)
//        others - reserved
// 0x0c : IP Interrupt Status Register (Read/TOW)
//        bit 0 - ap_done (Read/TOW)
//        bit 1 - ap_ready (Read/TOW)
//        others - reserved
// 0x10 : Data signal of audio
//        bit 31~0 - audio[31:0] (Read/Write)
// 0x14 : Data signal of audio
//        bit 31~0 - audio[63:32] (Read/Write)
// 0x18 : reserved
// 0x1c : Data signal of len
//        bit 31~0 - len[31:0] (Read/Write)
// 0x20 : reserved
// 0x24 : Data signal of cls_out
//        bit 31~0 - cls_out[31:0] (Read)
// 0x28 : Control signal of cls_out
//        bit 0  - cls_out_ap_vld (Read/COR)
//        others - reserved
// 0x40 ~
// 0x4f : Memory 'scores' (3 * 32b)
//        Word n : bit [31:0] - scores[n]
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

#define XKWS_ACCEL_CONTROL_ADDR_AP_CTRL      0x00
#define XKWS_ACCEL_CONTROL_ADDR_GIE          0x04
#define XKWS_ACCEL_CONTROL_ADDR_IER          0x08
#define XKWS_ACCEL_CONTROL_ADDR_ISR          0x0c
#define XKWS_ACCEL_CONTROL_ADDR_AUDIO_DATA   0x10
#define XKWS_ACCEL_CONTROL_BITS_AUDIO_DATA   64
#define XKWS_ACCEL_CONTROL_ADDR_LEN_DATA     0x1c
#define XKWS_ACCEL_CONTROL_BITS_LEN_DATA     32
#define XKWS_ACCEL_CONTROL_ADDR_CLS_OUT_DATA 0x24
#define XKWS_ACCEL_CONTROL_BITS_CLS_OUT_DATA 32
#define XKWS_ACCEL_CONTROL_ADDR_CLS_OUT_CTRL 0x28
#define XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE  0x40
#define XKWS_ACCEL_CONTROL_ADDR_SCORES_HIGH  0x4f
#define XKWS_ACCEL_CONTROL_WIDTH_SCORES      32
#define XKWS_ACCEL_CONTROL_DEPTH_SCORES      3

