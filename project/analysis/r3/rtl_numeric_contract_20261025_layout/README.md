# RTL 第一步：定点基础与缺失产物

状态：部分完成。不是完整逐层契约，不可作为旧模型RTL等价验收依据。

## 已核实格式（脚本或历史报告，非恢复的生成头文件）

| 项 | W | I（含符号） | F | 舍入 | 溢出 |
|---|---:|---:|---:|---|---|
| input | 40 | 2 | 38 | AP_TRN | AP_WRAP |
| output | 24 | 10 | 14 | AP_TRN | AP_WRAP |
| bn_scale | 40 | 16 | 24 | AP_TRN | AP_WRAP |
| bn_bias | 40 | 16 | 24 | AP_TRN | AP_WRAP |
| bn_result | 44 | 24 | 20 | AP_TRN | AP_WRAP |

AP_TRN向负无穷取整；AP_WRAP模回绕。规则作用于赋值边界，不代表表达式内部精度。

## 输入映射

256个uint8值经binary32归一化再转40位定点，直接用有理数p/255替代时有254项不同，最大差8160个输入LSB。
此表是软件建模结果，未经原NumPy或Vitis交叉验收，不是原网络golden。

## 逐层来源索引

|序号|操作|基线脚本行|生成类型/累加/截断|
|---|---|---:|---|
| 0 | Input | 87 | 未知，见contract.json |
| 1 | Conv | 88 | 未知，见contract.json |
| 2 | BatchNormalization | 89 | 未知，见contract.json |
| 3 | Act | 90 | 未知，见contract.json |
| 4 | MaxPooling2D | 91 | 未知，见contract.json |
| 5 | Conv | 92 | 未知，见contract.json |
| 6 | BatchNormalization | 93 | 未知，见contract.json |
| 7 | Act | 94 | 未知，见contract.json |
| 8 | MaxPooling2D | 95 | 未知，见contract.json |
| 9 | Conv | 96 | 未知，见contract.json |
| 10 | BatchNormalization | 97 | 未知，见contract.json |
| 11 | Act | 98 | 未知，见contract.json |
| 12 | MaxPooling2D | 99 | 未知，见contract.json |
| 13 | Conv | 100 | 未知，见contract.json |
| 14 | BatchNormalization | 101 | 未知，见contract.json |
| 15 | Act | 102 | 未知，见contract.json |
| 16 | GlobalAveragePooling2D | 103 | 未知，见contract.json |
| 17 | QDense | 105 | 未知，见contract.json |

## 缺口

- trained quantized weights and convolution/Dense biases
- BN moving mean, variance, gamma, beta, epsilon and transformed scale/bias
- generated product/accumulator types, rounding and assignment/cast sites
- generated activation, pooling and GAP intermediate semantics
- generated weight layout, layer ordering/fusions and expression promotion
- original tensors, label order, holdout indices and per-layer golden tensors

必须恢复原.keras、tensors.npz与HLS工程；若遗失，需另建新模型基线，重新训练/评测/导出，不能冒称恢复原权重。

仅需Python标准库；输出目录必须不存在。conversion_vectors.json为人工边界输入赋值参考，不是网络golden。
未运行RTL、Vitis CSim、综合或上板。历史196个logit一致不证明逐层参考已经存在。
来源与导出器SHA-256已记录在contract.json。
AMD UG1399: https://docs.amd.com/r/2024.1-English/ug1399-vitis-hls/Overview-of-Arbitrary-Precision-Fixed-Point-Data-Types
