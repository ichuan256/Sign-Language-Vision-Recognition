// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2024.1 (64-bit)
// Tool Version Limit: 2024.05
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
/***************************** Include Files *********************************/
#include "xkws_accel.h"

/************************** Function Implementation *************************/
#ifndef __linux__
int XKws_accel_CfgInitialize(XKws_accel *InstancePtr, XKws_accel_Config *ConfigPtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(ConfigPtr != NULL);

    InstancePtr->Control_BaseAddress = ConfigPtr->Control_BaseAddress;
    InstancePtr->IsReady = XIL_COMPONENT_IS_READY;

    return XST_SUCCESS;
}
#endif

void XKws_accel_Start(XKws_accel *InstancePtr) {
    u32 Data;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AP_CTRL) & 0x80;
    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AP_CTRL, Data | 0x01);
}

u32 XKws_accel_IsDone(XKws_accel *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AP_CTRL);
    return (Data >> 1) & 0x1;
}

u32 XKws_accel_IsIdle(XKws_accel *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AP_CTRL);
    return (Data >> 2) & 0x1;
}

u32 XKws_accel_IsReady(XKws_accel *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AP_CTRL);
    // check ap_start to see if the pcore is ready for next input
    return !(Data & 0x1);
}

void XKws_accel_EnableAutoRestart(XKws_accel *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AP_CTRL, 0x80);
}

void XKws_accel_DisableAutoRestart(XKws_accel *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AP_CTRL, 0);
}

void XKws_accel_Set_audio(XKws_accel *InstancePtr, u64 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AUDIO_DATA, (u32)(Data));
    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AUDIO_DATA + 4, (u32)(Data >> 32));
}

u64 XKws_accel_Get_audio(XKws_accel *InstancePtr) {
    u64 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AUDIO_DATA);
    Data += (u64)XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_AUDIO_DATA + 4) << 32;
    return Data;
}

void XKws_accel_Set_len(XKws_accel *InstancePtr, u32 Data) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_LEN_DATA, Data);
}

u32 XKws_accel_Get_len(XKws_accel *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_LEN_DATA);
    return Data;
}

u32 XKws_accel_Get_cls_out(XKws_accel *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_CLS_OUT_DATA);
    return Data;
}

u32 XKws_accel_Get_cls_out_vld(XKws_accel *InstancePtr) {
    u32 Data;

    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Data = XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_CLS_OUT_CTRL);
    return Data & 0x1;
}

u32 XKws_accel_Get_scores_BaseAddress(XKws_accel *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Control_BaseAddress + XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE);
}

u32 XKws_accel_Get_scores_HighAddress(XKws_accel *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (InstancePtr->Control_BaseAddress + XKWS_ACCEL_CONTROL_ADDR_SCORES_HIGH);
}

u32 XKws_accel_Get_scores_TotalBytes(XKws_accel *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return (XKWS_ACCEL_CONTROL_ADDR_SCORES_HIGH - XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + 1);
}

u32 XKws_accel_Get_scores_BitWidth(XKws_accel *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XKWS_ACCEL_CONTROL_WIDTH_SCORES;
}

u32 XKws_accel_Get_scores_Depth(XKws_accel *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XKWS_ACCEL_CONTROL_DEPTH_SCORES;
}

u32 XKws_accel_Write_scores_Words(XKws_accel *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XKWS_ACCEL_CONTROL_ADDR_SCORES_HIGH - XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(int *)(InstancePtr->Control_BaseAddress + XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + (offset + i)*4) = *(data + i);
    }
    return length;
}

u32 XKws_accel_Read_scores_Words(XKws_accel *InstancePtr, int offset, word_type *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length)*4 > (XKWS_ACCEL_CONTROL_ADDR_SCORES_HIGH - XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(int *)(InstancePtr->Control_BaseAddress + XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + (offset + i)*4);
    }
    return length;
}

u32 XKws_accel_Write_scores_Bytes(XKws_accel *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XKWS_ACCEL_CONTROL_ADDR_SCORES_HIGH - XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(char *)(InstancePtr->Control_BaseAddress + XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + offset + i) = *(data + i);
    }
    return length;
}

u32 XKws_accel_Read_scores_Bytes(XKws_accel *InstancePtr, int offset, char *data, int length) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr -> IsReady == XIL_COMPONENT_IS_READY);

    int i;

    if ((offset + length) > (XKWS_ACCEL_CONTROL_ADDR_SCORES_HIGH - XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + 1))
        return 0;

    for (i = 0; i < length; i++) {
        *(data + i) = *(char *)(InstancePtr->Control_BaseAddress + XKWS_ACCEL_CONTROL_ADDR_SCORES_BASE + offset + i);
    }
    return length;
}

void XKws_accel_InterruptGlobalEnable(XKws_accel *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_GIE, 1);
}

void XKws_accel_InterruptGlobalDisable(XKws_accel *InstancePtr) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_GIE, 0);
}

void XKws_accel_InterruptEnable(XKws_accel *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_IER);
    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_IER, Register | Mask);
}

void XKws_accel_InterruptDisable(XKws_accel *InstancePtr, u32 Mask) {
    u32 Register;

    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    Register =  XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_IER);
    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_IER, Register & (~Mask));
}

void XKws_accel_InterruptClear(XKws_accel *InstancePtr, u32 Mask) {
    Xil_AssertVoid(InstancePtr != NULL);
    Xil_AssertVoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    XKws_accel_WriteReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_ISR, Mask);
}

u32 XKws_accel_InterruptGetEnabled(XKws_accel *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_IER);
}

u32 XKws_accel_InterruptGetStatus(XKws_accel *InstancePtr) {
    Xil_AssertNonvoid(InstancePtr != NULL);
    Xil_AssertNonvoid(InstancePtr->IsReady == XIL_COMPONENT_IS_READY);

    return XKws_accel_ReadReg(InstancePtr->Control_BaseAddress, XKWS_ACCEL_CONTROL_ADDR_ISR);
}

