// ==============================================================
// Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2024.1 (64-bit)
// Tool Version Limit: 2024.05
// Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
// Copyright 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
// 
// ==============================================================
#ifndef __linux__

#include "xstatus.h"
#ifdef SDT
#include "xparameters.h"
#endif
#include "xkp_hls_dw3.h"

extern XKp_hls_dw3_Config XKp_hls_dw3_ConfigTable[];

#ifdef SDT
XKp_hls_dw3_Config *XKp_hls_dw3_LookupConfig(UINTPTR BaseAddress) {
	XKp_hls_dw3_Config *ConfigPtr = NULL;

	int Index;

	for (Index = (u32)0x0; XKp_hls_dw3_ConfigTable[Index].Name != NULL; Index++) {
		if (!BaseAddress || XKp_hls_dw3_ConfigTable[Index].Ctrl_BaseAddress == BaseAddress) {
			ConfigPtr = &XKp_hls_dw3_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XKp_hls_dw3_Initialize(XKp_hls_dw3 *InstancePtr, UINTPTR BaseAddress) {
	XKp_hls_dw3_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XKp_hls_dw3_LookupConfig(BaseAddress);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XKp_hls_dw3_CfgInitialize(InstancePtr, ConfigPtr);
}
#else
XKp_hls_dw3_Config *XKp_hls_dw3_LookupConfig(u16 DeviceId) {
	XKp_hls_dw3_Config *ConfigPtr = NULL;

	int Index;

	for (Index = 0; Index < XPAR_XKP_HLS_DW3_NUM_INSTANCES; Index++) {
		if (XKp_hls_dw3_ConfigTable[Index].DeviceId == DeviceId) {
			ConfigPtr = &XKp_hls_dw3_ConfigTable[Index];
			break;
		}
	}

	return ConfigPtr;
}

int XKp_hls_dw3_Initialize(XKp_hls_dw3 *InstancePtr, u16 DeviceId) {
	XKp_hls_dw3_Config *ConfigPtr;

	Xil_AssertNonvoid(InstancePtr != NULL);

	ConfigPtr = XKp_hls_dw3_LookupConfig(DeviceId);
	if (ConfigPtr == NULL) {
		InstancePtr->IsReady = 0;
		return (XST_DEVICE_NOT_FOUND);
	}

	return XKp_hls_dw3_CfgInitialize(InstancePtr, ConfigPtr);
}
#endif

#endif

