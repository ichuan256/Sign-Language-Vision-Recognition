// Minimal ARMv7 C ABI around the unmodified TensorFlow Lite C++ interpreter.
// Python owns camera, MediaPipe ROI geometry, tracking and display; no teacher labels are inputs.
#include <tensorflow/lite/interpreter.h>
#include <tensorflow/lite/kernels/register.h>
#include <tensorflow/lite/model.h>

#include <algorithm>
#include <cstring>
#include <memory>
#include <string>

namespace {
struct Runner {
  std::unique_ptr<tflite::FlatBufferModel> model;
  std::unique_ptr<tflite::Interpreter> interpreter;
  std::string error;
};
Runner* cast(void* handle) { return static_cast<Runner*>(handle); }
bool copy_tensor(const TfLiteTensor* tensor, const float* source, size_t count) {
  if (!tensor || tensor->type != kTfLiteFloat32 ||
      static_cast<size_t>(tensor->bytes) != count * sizeof(float)) return false;
  std::memcpy(tensor->data.f, source, tensor->bytes);
  return true;
}
}  // namespace

extern "C" {
void* hands_tflite_create(const char* model_path, int threads) {
  if (!model_path || threads < 1 || threads > 2) return nullptr;
  auto runner = std::make_unique<Runner>();
  runner->model = tflite::FlatBufferModel::BuildFromFile(model_path);
  if (!runner->model) return nullptr;
  tflite::ops::builtin::BuiltinOpResolver resolver;
  if (tflite::InterpreterBuilder(*runner->model, resolver)(&runner->interpreter) != kTfLiteOk ||
      !runner->interpreter) return nullptr;
  runner->interpreter->SetNumThreads(threads);
  runner->interpreter->SetAllowFp16PrecisionForFp32(false);
  if (runner->interpreter->AllocateTensors() != kTfLiteOk) return nullptr;
  if (runner->interpreter->inputs().size() != 1) return nullptr;
  return runner.release();
}
void hands_tflite_destroy(void* handle) { delete cast(handle); }
int hands_tflite_input_count(void* handle) {
  if (!handle) return -1;
  const TfLiteTensor* tensor = cast(handle)->interpreter->input_tensor(0);
  return tensor ? static_cast<int>(tensor->bytes / sizeof(float)) : -1;
}
int hands_tflite_output_count(void* handle, int output_index) {
  if (!handle) return -1;
  auto& interpreter = *cast(handle)->interpreter;
  if (output_index < 0 || output_index >= static_cast<int>(interpreter.outputs().size())) return -1;
  const TfLiteTensor* tensor = interpreter.output_tensor(output_index);
  return tensor && tensor->type == kTfLiteFloat32
      ? static_cast<int>(tensor->bytes / sizeof(float)) : -1;
}
int hands_tflite_input_dims(void* handle, int* dims, int capacity) {
  if (!handle || !dims || capacity < 4) return -1;
  const TfLiteTensor* tensor = cast(handle)->interpreter->input_tensor(0);
  if (!tensor || tensor->dims->size != 4) return -1;
  for (int i = 0; i < 4; ++i) dims[i] = tensor->dims->data[i];
  return 4;
}
int hands_tflite_output_dims(void* handle, int output_index, int* dims, int capacity) {
  if (!handle || !dims || capacity < 4) return -1;
  auto& interpreter = *cast(handle)->interpreter;
  if (output_index < 0 || output_index >= static_cast<int>(interpreter.outputs().size())) return -1;
  const TfLiteTensor* tensor = interpreter.output_tensor(output_index);
  if (!tensor || tensor->dims->size > capacity) return -1;
  const int rank = tensor->dims->size;
  for (int i = 0; i < rank; ++i) dims[i] = tensor->dims->data[i];
  return rank;
}
int hands_tflite_read_output(void* handle, float* output, size_t output_count,
                             int output_index) {
  if (!handle || !output) return -1;
  const TfLiteTensor* tensor = cast(handle)->interpreter->output_tensor(output_index);
  if (!tensor || tensor->type != kTfLiteFloat32 ||
      static_cast<size_t>(tensor->bytes) != output_count * sizeof(float)) return -4;
  std::memcpy(output, tensor->data.f, tensor->bytes);
  return 0;
}
int hands_tflite_invoke(void* handle, const float* input, size_t input_count,
                        float* output, size_t output_count, int output_index) {
  if (!handle || !input || !output) return -1;
  Runner& runner = *cast(handle);
  if (!copy_tensor(runner.interpreter->input_tensor(0), input, input_count)) return -2;
  if (runner.interpreter->Invoke() != kTfLiteOk) return -3;
  return hands_tflite_read_output(handle, output, output_count, output_index);
}
}
