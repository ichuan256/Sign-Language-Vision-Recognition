# PL 图像预处理 V2 接口契约

本轮实现范围是可综合模块、PS 参数生成/整数参考和自检仿真，不改现有相机/HDMI 发布包，不部署板卡。新 RTL 放在独立的 `project/fpga/rtl/vision_preprocess/`，不改冻结的 W6 RTL。

## 图像与采样

- 输入：DDR 中 RGB565_LE，基地址和行跨度均为 4 字节对齐；每行跨度至少 `align_up(width*2,4)`，调用者持有完整且已完成缓存一致性处理的输入帧（分配长度至少 stride×height，包含每行 padding）。CPU 写入后 flush；DMA 写入须先确认生产者完成，PS 要读取时 invalidate，禁止用脏的旧 CPU 缓存覆盖 DMA 数据。完整地址范围 base+stride×height 不得超过 2^32，等于 2^32 允许。
- 源宽高范围 1..4096；目标宽高范围 1..2048，主要使用 192×192 与 224×224。
- PS 提供六个有符号 Q16.16 系数，目标像素整数坐标 `(x,y)` 映射为 `sx=a*x+b*y+c`、`sy=d*x+e*y+f`。六个寄存器按 a,b,c,d,e,f 排列。坐标在 RTL 中用至少 48 位累加，禁止 32 位中间溢出回绕。
- 插值相位为 1/32 像素：先将 Q16.16 坐标按 `(coord+1024) >>> 11` 量化为带符号 Q5，再取 floor 和非负低 5 位小数。对负坐标同样使用算术右移。四个 RGB565 邻居分别位扩展到 RGB888；每个越界邻居单独用黑色，不能整点粗略裁零或读取帧外地址。
- 双线性每通道输出为 `(p00*(32-fx)*(32-fy)+p10*fx*(32-fy)+p01*(32-fx)*fy+p11*fx*fy+512) >> 10`。像素边界没有额外 +0.5 平移；letterbox/ROI 工厂负责生成正确的逆变换。
- 输出为逐行连续的 R,G,B 三个小端 IEEE754 float32，每通道严格等于 `np.float32(uint8_value) / np.float32(255)` 的 round-to-nearest-even 结果；每像素 12 字节。PL 内 256 项常量查表由精确整数除法及余数舍入生成，不能用乘以已舍入的 float32(1/255) 替代。RGB565 展开、Q5 坐标、双线性及整数舍入规则保持不变。
- 192×192 输出 442368 字节；224×224 输出 602112 字节。输入仍是 RGB565_LE，输入帧长度不受输出格式改变影响。
- 上述是明确的整数契约，可与 OpenCV 对量化坐标的 remap 独立对照；不声称所有任意浮点矩阵都与 OpenCV warpAffine 的内部系数量化逐位一致。

## RTL 分层

1. `vision_rgb565_affine`：start/busy/done/error_code、配置输入、一个在途的抽象 32 位对齐读端口、24 位 RGB 输出流。配置在空闲 start 时锁存；忙时 start 忽略。RGB `TDATA[7:0]=R,[15:8]=G,[23:16]=B`，TUSER 仅首像素，TLAST 仅最后像素（帧包）。
2. `rgb888_axis_fp32_normalize`：将 RGB888 像素转为 32 位 AXIS，按 R、G、B 顺序各输出一拍 float32，TKEEP 恒为 0xF，TUSER 仅全帧首个 R，TLAST 仅末像素 B。输出背压时数据和 sideband 均稳定。单像素缓冲在末 B 握手时可同时接收下一个像素；不要求输入连续。本外设只支持 V2 FP32 输出。
3. `vision_preprocess_axi`：AXI4-Lite 配置、32 位只读 AXI4 master 单拍访问、上述 sampler+normalizer、32 位 AXIS 输出。完成状态必须等最后一个 B 通道输出拍被消费。

采样器抽象读端口名：`rd_req_valid/ready/addr[31:0]`，`rd_rsp_valid/ready/data[31:0]/error`，一个请求对应一个响应，最多一个在途。四邻居可使用小型字缓存，零权重邻居可不读。

采样器配置端口名：`cfg_src_base[31:0]`、`cfg_src_stride[31:0]`、`cfg_src_width/height[15:0]`、`cfg_dst_width/height[15:0]`、有符号 `cfg_a/b/c/d/e/f[31:0]`；控制 `clk,reset_n,start,busy,done,error_code[7:0]`。目标 RGB 输出 `m_axis_tdata[23:0],m_axis_tvalid,m_axis_tready,m_axis_tuser,m_axis_tlast`。

归一化器端口为 `clk,reset_n`，24 位 `s_axis_*` 与 32 位 `m_axis_*`，输入无 TKEEP，输出 TKEEP[3:0] 恒为 0xF；无私有取消命令，避免背压中撤销合法的 VALID。

## 错误与内存所有权

错误码：0=正常，1=尺寸/行跨度非法，2=地址/行跨度不对齐，3=帧地址超出 32 位地址空间，4=AXI 读错误。

非法配置不产生读请求或输出，以 done/error 返回。合法任务遇读错误后不再读内存，将未完成的输出像素置黑以完成包的 TLAST，并保持非零错误码；**整张输出无效，PS 必须拒绝送模型**。这样 DMA 可结束事务，不把错误填充值当有效图像。

AXI adapter 必须在单拍读缺少 RLAST 时继续接收直到 RLAST，再向采样器报告一次错误；不得带着未结束读事务发下一请求。没有局部 abort/强制释放接口。全局 reset 只允许在系统总线协同 reset 的条件下中断事务。PS 超时不是 DMA/AXI 已停机的证明，不能因此释放硬件仍可能访问的缓冲。

## AXI4-Lite 寄存器

| 地址 | 内容 |
|---|---|
| 0x00 | 写 bit0 START、bit1 CLEAR_STATUS；读 0；忙时 START 返回 SLVERR，不扰动任务 |
| 0x04 | 只读 bit0 busy、bit1 done sticky、bit2 error sticky、bit3 read_adapter_idle |
| 0x08 | 只读 error_code |
| 0x0C | 只读本任务已握手输出的有效字节数 |
| 0x10/0x14 | SRC_BASE / SRC_STRIDE |
| 0x18/0x1C | SRC_WIDTH / SRC_HEIGHT |
| 0x20/0x24 | DST_WIDTH / DST_HEIGHT |
| 0x28..0x3C | a,b,c,d,e,f（每项 4 字节，Q16.16） |
| 0x40 | 只读版本 0x00020000 |
| 0x44 | 只读本任务 AXI AR 握手次数 |
| 0x48 | 只读本任务运行周期数（允许饱和） |

配置寄存器是 shadow；任务启动后修改只影响下一任务。AW 与 W 必须独立接收，WSTRB 生效，B/R 响应在背压下稳定。未知/只读地址写入及未知地址读取返回 SLVERR。busy 覆盖采样与归一化尾部排空。

输出是 AXI DMA 的一帧一个包，**不是** AXI4-Stream Video 的逐行 TLAST；不可直接接 HDMI/VDMA video 输入。


## PS 读取 V2 输出

`AffineJob.output_bytes` 按 12×宽×高计算，`Preprocessor` 仅接受版本 0x00020000，并在完成时严格核对输出字节数；V1 的 0x00010000 以及 RGB888 字节数不能混用。调用者配置同样长度的 S2MM，确认 IP 成功和 DMA IOC/Idle 后 invalidate 缓冲，再调用 `fp32_to_model_tensor(raw,width,height)`；该函数以 `np.frombuffer(dtype='<f4')` 返回形状 `(1,H,W,3)` 的连续 RGB NHWC 零拷贝视图，不再执行 astype 或除 255。模型使用期间必须保留缓冲所有权，不能让 DMA 覆盖其内容。错误、未完成或超时输出都不得送模型。

只支持 V2 FP32 输出，不提供 RGB888 输出及 PS 归一化支路，也没有可配置输出格式。采样器内部 RGB888 像素和整数参考仅服务于几何与舍入验证；本次未修改或部署现有固件和老师模型。
