# 单路抓图测试契约

2026-10-27。独立 PS7 工程，不改 W6，不含 HDMI/音频；默认只启动/采集 OV1（左目）。
1280×720 RGB565 LE，每帧1843200字节。AXI DMA simple S2MM，每32位含两个像素，TLAST仅在整帧最后一拍。不是VDMA逐行TLAST协议。

GPIO 0x41200000：CH1输出 bit0 reset_release、bit1 init_start上升沿、bit2 arm_toggle；CH2输入 bit0 init_busy、1 init_done、2 init_error、3 capture_busy、4 capture_done、5 capture_error、6 fifo_overflow、11:8 init_error_code、13:12 failed_cameras、16 PCLK heartbeat。AXI DMA 0x40400000，长度宽23，无SG/MM2S。

软件必须先分配缓冲并启动DMA接收，再翻转arm；等采集成功且DMA完成并核对接收字节数。坏帧/超时/溢出必须停止或复位DMA、确认停止后才能释放缓冲，禁止把部分图像当成功。硬件错误保持至reset_release拉低复位。

候选只能冷启动加载；读帧程序只允许download=False，不能改变启动项或运行中加载bit。外部I/O延迟仍须规格/实测，不编造。
