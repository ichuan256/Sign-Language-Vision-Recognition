// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2024.1 (64-bit)
// Tool Version Limit: 2024.05
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
/***************************** Include Files *********************************/
#include "xkp_hls_stem.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XKp_hls_stem_CfgInitialize(XKp_hls_stem *InstancePtr, XKp_hls_stem_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Ctrl_BaseAddress = ConfigPtr->Ctrl_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XKp_hls_stem_Start(XKp_hls_stem *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_AP_CTRL) & 0x80;
    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XKp_hls_stem_IsDone(XKp_hls_stem *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XKp_hls_stem_IsIdle(XKp_hls_stem *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XKp_hls_stem_IsReady(XKp_hls_stem *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XKp_hls_stem_EnableAutoRestart(XKp_hls_stem *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_AP_CTRL, 0x80);
}

void XKp_hls_stem_DisableAutoRestart(XKp_hls_stem *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_AP_CTRL, 0);
}

void XKp_hls_stem_Set_in_r(XKp_hls_stem *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IN_R_DATA, (u32)(Data));
    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IN_R_DATA + 4, (u32)(Data >> 32));
}

u64 XKp_hls_stem_Get_in_r(XKp_hls_stem *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IN_R_DATA);
    Data += (u64)XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IN_R_DATA + 4) << 32;
    return Data;
}

void XKp_hls_stem_Set_w(XKp_hls_stem *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_W_DATA, (u32)(Data));
    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_W_DATA + 4, (u32)(Data >> 32));
}

u64 XKp_hls_stem_Get_w(XKp_hls_stem *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_W_DATA);
    Data += (u64)XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_W_DATA + 4) << 32;
    return Data;
}

void XKp_hls_stem_Set_bias(XKp_hls_stem *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_BIAS_DATA, (u32)(Data));
    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_BIAS_DATA + 4, (u32)(Data >> 32));
}

u64 XKp_hls_stem_Get_bias(XKp_hls_stem *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_BIAS_DATA);
    Data += (u64)XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_BIAS_DATA + 4) << 32;
    return Data;
}

void XKp_hls_stem_Set_M(XKp_hls_stem *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_M_DATA, (u32)(Data));
    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_M_DATA + 4, (u32)(Data >> 32));
}

u64 XKp_hls_stem_Get_M(XKp_hls_stem *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_M_DATA);
    Data += (u64)XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_M_DATA + 4) << 32;
    return Data;
}

void XKp_hls_stem_Set_F(XKp_hls_stem *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_F_DATA, Data);
}

u32 XKp_hls_stem_Get_F(XKp_hls_stem *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_F_DATA);
    return Data;
}

void XKp_hls_stem_Set_out_r(XKp_hls_stem *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_OUT_R_DATA, (u32)(Data));
    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_OUT_R_DATA + 4, (u32)(Data >> 32));
}

u64 XKp_hls_stem_Get_out_r(XKp_hls_stem *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_OUT_R_DATA);
    Data += (u64)XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_OUT_R_DATA + 4) << 32;
    return Data;
}

void XKp_hls_stem_InterruptGlobalEnable(XKp_hls_stem *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_GIE, 1);
}

void XKp_hls_stem_InterruptGlobalDisable(XKp_hls_stem *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_GIE, 0);
}

void XKp_hls_stem_InterruptEnable(XKp_hls_stem *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IER);
    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IER, Register | Mask);
}

void XKp_hls_stem_InterruptDisable(XKp_hls_stem *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IER);
    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IER, Register & (~Mask));
}

void XKp_hls_stem_InterruptClear(XKp_hls_stem *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKp_hls_stem_WriteReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_ISR, Mask);
}

u32 XKp_hls_stem_InterruptGetEnabled(XKp_hls_stem *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_IER);
}

u32 XKp_hls_stem_InterruptGetStatus(XKp_hls_stem *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XKp_hls_stem_ReadReg(InstancePtr->Ctrl_BaseAddress, XKP_HLS_STEM_CTRL_ADDR_ISR);
}

