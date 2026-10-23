// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2024.1 (64-bit)
// Tool Version Limit: 2024.05
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef XKWS_ACCEL_H
#define XKWS_ACCEL_H

#ifdef __cplusplus
extern "C" {
#endif

/***************************** Include Files *********************************/
#ifndef __linux__
#include "xil_types.h"
#include "xil_assert.h"
#include "xstatus.h"
#include "xil_io.h"
#else
#include <stdint.h>
#include <assert.h>
#include <dirent.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
#include <stddef.h>
#endif
#include "xkws_accel_hw.h"

/**************************** Type Definitions ******************************/
#ifdef __linux__
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef uint64_t u64;
#else
typedef struct {
#ifdef SDT
    char *Name;
#else
    u16 DeviceId;
#endif
    u64 Control_BaseAddress;
} XKws_accel_Config;
#endif

typedef struct {
    u64 Control_BaseAddress;
    u32 IsReady;
} XKws_accel;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XKws_accel_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XKws_accel_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XKws_accel_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XKws_accel_ReadReg(BaseAddress, RegOffset) \
    *(volatile u32*)((BaseAddress) + (RegOffset))

#define Xil_AssertVoid(expr)    assert(expr)
#define Xil_AssertNonvoid(expr) assert(expr)

#define XST_SUCCESS             0
#define XST_DEVICE_NOT_FOUND    2
#define XST_OPEN_DEVICE_FAILED  3
#define XIL_COMPONENT_IS_READY  1
#endif

/************************** Function Prototypes *****************************/
#ifndef __linux__
#ifdef SDT
int XKws_accel_Initialize(XKws_accel *InstancePtr, UINTPTR BaseAddress);
XKws_accel_Config* XKws_accel_LookupConfig(UINTPTR BaseAddress);
#else
int XKws_accel_Initialize(XKws_accel *InstancePtr, u16 DeviceId);
XKws_accel_Config* XKws_accel_LookupConfig(u16 DeviceId);
#endif
int XKws_accel_CfgInitialize(XKws_accel *InstancePtr, XKws_accel_Config *ConfigPtr);
#else
int XKws_accel_Initialize(XKws_accel *InstancePtr, const char* InstanceName);
int XKws_accel_Release(XKws_accel *InstancePtr);
#endif

void XKws_accel_Start(XKws_accel *InstancePtr);
u32 XKws_accel_IsDone(XKws_accel *InstancePtr);
u32 XKws_accel_IsIdle(XKws_accel *InstancePtr);
u32 XKws_accel_IsReady(XKws_accel *InstancePtr);
void XKws_accel_EnableAutoRestart(XKws_accel *InstancePtr);
void XKws_accel_DisableAutoRestart(XKws_accel *InstancePtr);

void XKws_accel_Set_audio(XKws_accel *InstancePtr, u64 Data);
u64 XKws_accel_Get_audio(XKws_accel *InstancePtr);
void XKws_accel_Set_len(XKws_accel *InstancePtr, u32 Data);
u32 XKws_accel_Get_len(XKws_accel *InstancePtr);
u32 XKws_accel_Get_cls_out(XKws_accel *InstancePtr);
u32 XKws_accel_Get_cls_out_vld(XKws_accel *InstancePtr);
u32 XKws_accel_Get_scores_BaseAddress(XKws_accel *InstancePtr);
u32 XKws_accel_Get_scores_HighAddress(XKws_accel *InstancePtr);
u32 XKws_accel_Get_scores_TotalBytes(XKws_accel *InstancePtr);
u32 XKws_accel_Get_scores_BitWidth(XKws_accel *InstancePtr);
u32 XKws_accel_Get_scores_Depth(XKws_accel *InstancePtr);
u32 XKws_accel_Write_scores_Words(XKws_accel *InstancePtr, int offset, word_type *data, int length);
u32 XKws_accel_Read_scores_Words(XKws_accel *InstancePtr, int offset, word_type *data, int length);
u32 XKws_accel_Write_scores_Bytes(XKws_accel *InstancePtr, int offset, char *data, int length);
u32 XKws_accel_Read_scores_Bytes(XKws_accel *InstancePtr, int offset, char *data, int length);

void XKws_accel_InterruptGlobalEnable(XKws_accel *InstancePtr);
void XKws_accel_InterruptGlobalDisable(XKws_accel *InstancePtr);
void XKws_accel_InterruptEnable(XKws_accel *InstancePtr, u32 Mask);
void XKws_accel_InterruptDisable(XKws_accel *InstancePtr, u32 Mask);
void XKws_accel_InterruptClear(XKws_accel *InstancePtr, u32 Mask);
u32 XKws_accel_InterruptGetEnabled(XKws_accel *InstancePtr);
u32 XKws_accel_InterruptGetStatus(XKws_accel *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
