// 0x00 : Control signals
//        bit 0  - ap_start (Read/Write/COH)
//        bit 1  - ap_done (Read/COR)
//        bit 2  - ap_idle (Read)
//        bit 3  - ap_ready (Read/COR)
//        bit 7  - auto_restart (Read/Write)
//        bit 9  - interrupt (Read)
//        others - reserved
// 0x04 : Global Interrupt Enable Register
//        bit 0  - Global Interrupt Enable (Read/Write)
//        others - reserved
// 0x08 : IP Interrupt Enable Register (Read/Write)
//        bit 0 - enable ap_done interrupt (Read/Write)
//        bit 1 - enable ap_ready interrupt (Read/Write)
//        others - reserved
// 0x0c : IP Interrupt Status Register (Read/TOW)
//        bit 0 - ap_done (Read/TOW)
//        bit 1 - ap_ready (Read/TOW)
//        others - reserved
// 0x10 : Data signal of in_r
//        bit 31~0 - in_r[31:0] (Read/Write)
// 0x14 : Data signal of in_r
//        bit 31~0 - in_r[63:32] (Read/Write)
// 0x18 : reserved
// 0x1c : Data signal of w
//        bit 31~0 - w[31:0] (Read/Write)
// 0x20 : Data signal of w
//        bit 31~0 - w[63:32] (Read/Write)
// 0x24 : reserved
// 0x28 : Data signal of bias
//        bit 31~0 - bias[31:0] (Read/Write)
// 0x2c : Data signal of bias
//        bit 31~0 - bias[63:32] (Read/Write)
// 0x30 : reserved
// 0x34 : Data signal of M
//        bit 31~0 - M[31:0] (Read/Write)
// 0x38 : Data signal of M
//        bit 31~0 - M[63:32] (Read/Write)
// 0x3c : reserved
// 0x40 : Data signal of F
//        bit 31~0 - F[31:0] (Read/Write)
// 0x44 : reserved
// 0x48 : Data signal of out_r
//        bit 31~0 - out_r[31:0] (Read/Write)
// 0x4c : Data signal of out_r
//        bit 31~0 - out_r[63:32] (Read/Write)
// 0x50 : reserved
// (SC = Self Clear, COR = Clear on Read, TOW = Toggle on Write, COH = Clear on Handshake)

#define CTRL_ADDR_AP_CTRL    0x00
#define CTRL_ADDR_GIE        0x04
#define CTRL_ADDR_IER        0x08
#define CTRL_ADDR_ISR        0x0c
#define CTRL_ADDR_IN_R_DATA  0x10
#define CTRL_BITS_IN_R_DATA  64
#define CTRL_ADDR_W_DATA     0x1c
#define CTRL_BITS_W_DATA     64
#define CTRL_ADDR_BIAS_DATA  0x28
#define CTRL_BITS_BIAS_DATA  64
#define CTRL_ADDR_M_DATA     0x34
#define CTRL_BITS_M_DATA     64
#define CTRL_ADDR_F_DATA     0x40
#define CTRL_BITS_F_DATA     32
#define CTRL_ADDR_OUT_R_DATA 0x48
#define CTRL_BITS_OUT_R_DATA 64
