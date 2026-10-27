#!/usr/bin/env bash
# Build on PYNQ-Z2 itself so glibc/libstdc++ exactly match the deployed board.
set -euo pipefail
ROOT="${1:?usage: build_native.sh /absolute/new/workdir}"
cd "$ROOT"
test -f tensorflow-2.12.1.tar.gz
test -f tflite_runner.cpp
test -f tflite_with_wrapper.CMakeLists.txt
if [[ ! -d tensorflow-2.12.1 ]]; then
  tar -xzf tensorflow-2.12.1.tar.gz
fi
cp tflite_with_wrapper.CMakeLists.txt tensorflow-2.12.1/tensorflow/lite/CMakeLists.txt
mkdir -p deps_src
for archive in deps/*.tar.gz; do
  name="$(basename "$archive" .tar.gz)"
  if [[ ! -d "deps_src/$name" ]]; then
    mkdir -p "deps_src/$name"
    tar -xzf "$archive" --strip-components=1 -C "deps_src/$name"
  fi
done
FLAGS="-march=armv7-a -mfpu=neon -mfloat-abi=hard -funsafe-math-optimizations -O3"
cmake -S tensorflow-2.12.1/tensorflow/lite -B tflite_build \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS="$FLAGS" \
  -DCMAKE_CXX_FLAGS="$FLAGS" \
  -DTFLITE_ENABLE_XNNPACK=ON \
  -DTFLITE_ENABLE_GPU=OFF \
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON \
  "-DFETCHCONTENT_SOURCE_DIR_ABSEIL-CPP=$ROOT/deps_src/abseil-cpp" \
  -DFETCHCONTENT_SOURCE_DIR_CPUINFO="$ROOT/deps_src/cpuinfo" \
  -DFETCHCONTENT_SOURCE_DIR_EIGEN="$ROOT/deps_src/eigen" \
  -DFETCHCONTENT_SOURCE_DIR_FARMHASH="$ROOT/deps_src/farmhash" \
  -DFETCHCONTENT_SOURCE_DIR_FFT2D="$ROOT/deps_src/fft2d" \
  -DFETCHCONTENT_SOURCE_DIR_FLATBUFFERS="$ROOT/deps_src/flatbuffers" \
  -DFETCHCONTENT_SOURCE_DIR_FP16_HEADERS="$ROOT/deps_src/fp16_headers" \
  -DFETCHCONTENT_SOURCE_DIR_GEMMLOWP="$ROOT/deps_src/gemmlowp" \
  -DFETCHCONTENT_SOURCE_DIR_NEON2SSE="$ROOT/deps_src/neon2sse" \
  -DFETCHCONTENT_SOURCE_DIR_RUY="$ROOT/deps_src/ruy" \
  -DFETCHCONTENT_SOURCE_DIR_XNNPACK="$ROOT/deps_src/xnnpack" \
  -DFP16_SOURCE_DIR="$ROOT/deps_src/fp16_headers" \
  -DFXDIV_SOURCE_DIR="$ROOT/deps_src/fxdiv" \
  -DPSIMD_SOURCE_DIR="$ROOT/deps_src/psimd" \
  -DPTHREADPOOL_SOURCE_DIR="$ROOT/deps_src/pthreadpool"
cmake --build tflite_build --target tensorflow-lite -j2
cmake --build tflite_build --target hands_tflite -j2
file libhands_tflite.so
sha256sum libhands_tflite.so palm_detection_full.tflite hand_landmark_full.tflite > SHA256SUMS
printf 'NATIVE_BUILD_COMPLETE\n'
