# ==============================================================
# Vitis HLS - High-Level Synthesis from C, C++ and OpenCL v2024.1 (64-bit)
# Tool Version Limit: 2024.05
# Copyright 1986-2022 Xilinx, Inc. All Rights Reserved.
# Copyright 2022-2024 Advanced Micro Devices, Inc. All Rights Reserved.
# 
# ==============================================================
cmake_minimum_required(VERSION 3.15)
project(kp_hls_pw3_v3)
find_package(common)
collector_create (PROJECT_LIB_SOURCES "${CMAKE_CURRENT_SOURCE_DIR}")
collect (PROJECT_LIB_SOURCES xkp_hls_pw3_v3.c)
collect (PROJECT_LIB_SOURCES xkp_hls_pw3_v3_sinit.c)
collect (PROJECT_LIB_SOURCES xkp_hls_pw3_v3_linux.c)
collect (PROJECT_LIB_SOURCES xkp_hls_pw3_v3_g.c)
collector_list (_sources PROJECT_LIB_SOURCES)
collector_create (PROJECT_LIB_HEADERS "${CMAKE_CURRENT_SOURCE_DIR}")
collect (PROJECT_LIB_HEADERS xkp_hls_pw3_v3.h)
collect (PROJECT_LIB_HEADERS xkp_hls_pw3_v3_hw.h)
collector_list (_headers PROJECT_LIB_HEADERS)
file(COPY ${_headers} DESTINATION ${CMAKE_BINARY_DIR}/include)
include_directories(${CMAKE_BINARY_DIR}/include)
add_library(kp_hls_pw3_v3 STATIC ${_sources})
set_target_properties(kp_hls_pw3_v3 PROPERTIES LINKER_LANGUAGE C)

