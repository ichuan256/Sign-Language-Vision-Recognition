// Diagnostic extension of the unchanged teacher wrapper. No FPGA access.
#include "tflite_runner.cpp"
#include <tensorflow/lite/core/api/profiler.h>
#include <tensorflow/lite/schema/schema_generated.h>
#include <chrono>
#include <map>
#include <sstream>
#include <vector>

namespace {
std::string quoted(const char* value) {
  std::ostringstream s; s << '"';
  for (const unsigned char c : std::string(value ? value : "")) {
    if (c == '"' || c == '\\') s << '\\' << c;
    else if (c >= 32) s << c;
  }
  s << '"'; return s.str();
}
struct Trace : public tflite::Profiler {
  bool enabled = false;
  struct Event { std::string tag; int type; int64_t node, subgraph;
    std::chrono::steady_clock::time_point start; double us; bool ended; };
  std::vector<Event> events;
  uint32_t BeginEvent(const char* tag, EventType type, int64_t a, int64_t b) override {
    if (!enabled) return UINT32_MAX;
    events.push_back({tag ? tag : "", static_cast<int>(type), a, b,
                      std::chrono::steady_clock::now(), 0., false});
    return static_cast<uint32_t>(events.size()-1);
  }
  void EndEvent(uint32_t h) override {
    if (h >= events.size()) return;
    auto& e = events[h];
    e.us = std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now()-e.start).count();
    e.ended = true;
  }
  void AddEvent(const char* tag, EventType type, uint64_t us, int64_t a, int64_t b) override {
    if (!enabled) return;
    events.push_back({tag ? tag : "",static_cast<int>(type),a,b,
                      std::chrono::steady_clock::now(),static_cast<double>(us),true});
  }
};
std::map<void*, std::unique_ptr<Trace>> traces;
std::string result;
void ints(std::ostringstream& s, const TfLiteIntArray* a) {
  s << '[';
  if (a) for (int i=0;i<a->size;++i) { if (i) s << ','; s << a->data[i]; }
  s << ']';
}
}

extern "C" {
int hands_probe_abi() { return 1; }
// Diagnostics only: expose two small block boundaries as extra interpreter
// outputs before XNNPACK preparation. The .tflite bytes and four original
// outputs are unchanged. Retention can alter allocation/fusion, so this is
// never used as the production timing baseline.
void* hands_probe_create_boundaries(const char* path, int threads) {
  if (!path || threads < 1 || threads > 2) return nullptr;
  auto runner = std::make_unique<Runner>();
  runner->model = tflite::FlatBufferModel::BuildFromFile(path);
  if (!runner->model) return nullptr;
  tflite::ops::builtin::BuiltinOpResolver resolver;
  if (tflite::InterpreterBuilder(*runner->model,resolver)(&runner->interpreter)!=kTfLiteOk) return nullptr;
  auto& interpreter = *runner->interpreter;
  if (interpreter.inputs() != std::vector<int>{0} ||
      interpreter.outputs() != std::vector<int>({165,164,162,166})) return nullptr;
  const std::vector<int> boundaries{134,138,142};
  for (const int id : boundaries) {
    const TfLiteTensor* t=interpreter.tensor(id);
    if (!t || t->type!=kTfLiteFloat32 || t->dims->size!=4 ||
        t->dims->data[0]!=1 || t->dims->data[1]!=14 ||
        t->dims->data[2]!=14 || t->dims->data[3]!=112) return nullptr;
  }
  auto outputs=interpreter.outputs();
  outputs.insert(outputs.end(),boundaries.begin(),boundaries.end());
  if (interpreter.SetOutputs(outputs)!=kTfLiteOk) return nullptr;
  interpreter.SetNumThreads(threads);
  interpreter.SetAllowFp16PrecisionForFp32(false);
  if (interpreter.AllocateTensors()!=kTfLiteOk) return nullptr;
  return runner.release();
}
const char* hands_probe_execution_json(void* handle) {
  if (!handle) return nullptr;
  auto& interpreter = *cast(handle)->interpreter;
  std::ostringstream s; s << "{\"nodes\":["; bool first = true;
  for (const int id : interpreter.execution_plan()) {
    const auto* pair = interpreter.node_and_registration(id);
    if (!pair) return nullptr;
    if (!first) s << ','; first = false;
    const auto& n = pair->first; const auto& r = pair->second;
    s << "{\"node\":" << id << ",\"builtin\":" << r.builtin_code
      << ",\"name\":" << quoted(tflite::EnumNameBuiltinOperator(static_cast<tflite::BuiltinOperator>(r.builtin_code)))
      << ",\"custom\":" << quoted(r.custom_name)
      << ",\"delegated\":" << (n.delegate ? "true" : "false") << ",\"inputs\":";
    ints(s,n.inputs); s << ",\"outputs\":"; ints(s,n.outputs); s << '}';
  }
  s << "]}"; result = s.str(); return result.c_str();
}
int hands_probe_profile_begin(void* handle) {
  auto found = traces.find(handle);
  if (found == traces.end() || found->second->enabled) return 1;
  found->second->events.clear(); found->second->enabled=true; return 0;
}
const char* hands_probe_profile_end(void* handle) {
  auto found = traces.find(handle);
  if (found == traces.end()) return nullptr;
  // Keep the profiler attached until interpreter destruction. In TF 2.12.1,
  // SetProfiler(nullptr) does not refresh the subgraph's raw profiler pointer.
  found->second->enabled = false;
  std::ostringstream s; s << '['; bool first = true;
  for (const auto& e : found->second->events) {
    if (!first) s << ','; first = false;
    s << "{\"tag\":" << quoted(e.tag.c_str()) << ",\"type\":" << e.type
      << ",\"node\":" << e.node << ",\"subgraph\":" << e.subgraph
      << ",\"elapsed_us\":" << e.us << ",\"ended\":" << (e.ended ? "true" : "false") << '}';
  }
  s << ']'; result = s.str(); return result.c_str();
}
void hands_probe_destroy(void* handle) {
  hands_tflite_destroy(handle); // Trace must outlive the interpreter and subgraphs.
  traces.erase(handle);
}
void* hands_probe_create_profiled(const char* path, int threads, int builtin_only) {
  if (!path || threads < 1 || threads > 2) return nullptr;
  auto runner = std::make_unique<Runner>();
  runner->model = tflite::FlatBufferModel::BuildFromFile(path);
  if (!runner->model) return nullptr;
  if (builtin_only) {
    tflite::ops::builtin::BuiltinOpResolverWithoutDefaultDelegates resolver;
    if (tflite::InterpreterBuilder(*runner->model,resolver)(&runner->interpreter)!=kTfLiteOk) return nullptr;
  } else {
    tflite::ops::builtin::BuiltinOpResolver resolver;
    if (tflite::InterpreterBuilder(*runner->model,resolver)(&runner->interpreter)!=kTfLiteOk) return nullptr;
  }
  runner->interpreter->SetNumThreads(threads);
  runner->interpreter->SetAllowFp16PrecisionForFp32(false);
  // XNNPACK decides whether to enable its internal timing at preparation.
  // Attach before AllocateTensors, never to an already prepared XNN runtime.
  auto trace = std::make_unique<Trace>();
  runner->interpreter->SetProfiler(trace.get());
  if (runner->interpreter->AllocateTensors()!=kTfLiteOk) {
    runner.reset(); return nullptr;
  }
  traces[runner.get()] = std::move(trace);
  return runner.release();
}
}
