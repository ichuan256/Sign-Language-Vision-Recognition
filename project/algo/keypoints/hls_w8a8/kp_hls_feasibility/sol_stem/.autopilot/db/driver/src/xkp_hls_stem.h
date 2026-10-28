// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2024.1 (64-bit)
// Tool Version Limit: 2024.05
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef XKP_HLS_STEM_H
#define XKP_HLS_STEM_H

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
#include "xkp_hls_stem_hw.h"

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
    u64 Ctrl_BaseAddress;
} XKp_hls_stem_Config;
#endif

typedef struct {
    u64 Ctrl_BaseAddress;
    u32 IsReady;
} XKp_hls_stem;

typedef u32 word_type;

/***************** Macros (Inline Functions) Definitions *********************/
#ifndef __linux__
#define XKp_hls_stem_WriteReg(BaseAddress, RegOffset, Data) \
    Xil_Out32((BaseAddress) + (RegOffset), (u32)(Data))
#define XKp_hls_stem_ReadReg(BaseAddress, RegOffset) \
    Xil_In32((BaseAddress) + (RegOffset))
#else
#define XKp_hls_stem_WriteReg(BaseAddress, RegOffset, Data) \
    *(volatile u32*)((BaseAddress) + (RegOffset)) = (u32)(Data)
#define XKp_hls_stem_ReadReg(BaseAddress, RegOffset) \
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
int XKp_hls_stem_Initialize(XKp_hls_stem *InstancePtr, UINTPTR BaseAddress);
XKp_hls_stem_Config* XKp_hls_stem_LookupConfig(UINTPTR BaseAddress);
#else
int XKp_hls_stem_Initialize(XKp_hls_stem *InstancePtr, u16 DeviceId);
XKp_hls_stem_Config* XKp_hls_stem_LookupConfig(u16 DeviceId);
#endif
int XKp_hls_stem_CfgInitialize(XKp_hls_stem *InstancePtr, XKp_hls_stem_Config *ConfigPtr);
#else
int XKp_hls_stem_Initialize(XKp_hls_stem *InstancePtr, const char* InstanceName);
int XKp_hls_stem_Release(XKp_hls_stem *InstancePtr);
#endif

void XKp_hls_stem_Start(XKp_hls_stem *InstancePtr);
u32 XKp_hls_stem_IsDone(XKp_hls_stem *InstancePtr);
u32 XKp_hls_stem_IsIdle(XKp_hls_stem *InstancePtr);
u32 XKp_hls_stem_IsReady(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_EnableAutoRestart(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_DisableAutoRestart(XKp_hls_stem *InstancePtr);

void XKp_hls_stem_Set_in_r(XKp_hls_stem *InstancePtr, u64 Data);
u64 XKp_hls_stem_Get_in_r(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_Set_w(XKp_hls_stem *InstancePtr, u64 Data);
u64 XKp_hls_stem_Get_w(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_Set_bias(XKp_hls_stem *InstancePtr, u64 Data);
u64 XKp_hls_stem_Get_bias(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_Set_M(XKp_hls_stem *InstancePtr, u64 Data);
u64 XKp_hls_stem_Get_M(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_Set_F(XKp_hls_stem *InstancePtr, u32 Data);
u32 XKp_hls_stem_Get_F(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_Set_out_r(XKp_hls_stem *InstancePtr, u64 Data);
u64 XKp_hls_stem_Get_out_r(XKp_hls_stem *InstancePtr);

void XKp_hls_stem_InterruptGlobalEnable(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_InterruptGlobalDisable(XKp_hls_stem *InstancePtr);
void XKp_hls_stem_InterruptEnable(XKp_hls_stem *InstancePtr, u32 Mask);
void XKp_hls_stem_InterruptDisable(XKp_hls_stem *InstancePtr, u32 Mask);
void XKp_hls_stem_InterruptClear(XKp_hls_stem *InstancePtr, u32 Mask);
u32 XKp_hls_stem_InterruptGetEnabled(XKp_hls_stem *InstancePtr);
u32 XKp_hls_stem_InterruptGetStatus(XKp_hls_stem *InstancePtr);

#ifdef __cplusplus
}
#endif

#endif
