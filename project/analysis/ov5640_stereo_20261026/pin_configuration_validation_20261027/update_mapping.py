"""One-time migration of the reviewed 2026-10-27 user wiring."""
import json
import shutil
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = HERE.parent
before = HERE / 'before'
before.mkdir(exist_ok=True)
for name in ('physical_pin_map_20261027.json','interface_and_pin_map.md','user_pin_review_20261027.md'):
    if not (before / name).exists():
        shutil.copy2(BASE / name, before / name)
mapping = json.loads((BASE/'physical_pin_map_20261027.json').read_text(encoding='utf-8-sig'))
if mapping.get('status') == 'physical_constraints_implemented_not_deployed':
    raise SystemExit('Already migrated; use generate_pin_constraints.py --check instead.')
pins = {
 'OV1': dict(SCL='W9',SDA='Y8',VSYNC='W10',HREF='A20',RESET='B19',D0='W8',D1='B20',D2='Y7',D3='Y17',D4='Y6',D5='F20',D6='Y16',D7='F19',PCLK='Y9',PWDN='R16'),
 'OV2': dict(SCL='V10',SDA='V8',VSYNC='U19',HREF='U18',RESET='U8',D0='V7',D1='W6',D2='W18',D3='C20',D4='V6',D5='Y19',D6='W19',D7='Y18',PCLK='U7',PWDN='U17'),
}
sys.path.insert(0,str(ROOT/'project/scripts/ov5640'))
from generate_pin_constraints import RPI, validate
reverse = {pad:physical for physical,pad in RPI.items()}
for row in mapping['signals']:
    camera, signal = row['camera'], row['signal']
    row['package_pin'] = pins[camera][signal]
    row.pop('clock_pin_function', None)
    if signal != 'PWDN': row['board_pin'] = reverse[row['package_pin']]
    if signal == 'PCLK': row['clock_pin_function'] = 'IO_L14P_T2_SRCC_13' if camera=='OV1' else 'IO_L11P_T1_SRCC_13'
mapping['status'] = 'physical_constraints_implemented_not_deployed'
mapping['orientation_note'] = 'OV1/OV2 follow module silkscreen; latest user wiring spans both header halves. Old contiguous partition is superseded.'
mapping['header_partition'] = {
 'policy':'latest user mapping with four clock corrections; no contiguous-half partition',
 'left':{'camera':'OV1','signal_pins':sorted(r['board_pin'] for r in mapping['signals'] if r['camera']=='OV1' and r['signal']!='PWDN')},
 'right':{'camera':'OV2','signal_pins':sorted(r['board_pin'] for r in mapping['signals'] if r['camera']=='OV2' and r['signal']!='PWDN')},
}
mapping['user_mapping_adjustments'] = [
 {'camera':'OV1','signal':'PCLK','user_pin':'W10','package_pin':'Y9'},
 {'camera':'OV1','signal':'VSYNC','user_pin':'Y9','package_pin':'W10'},
 {'camera':'OV2','signal':'PCLK','user_pin':'W18','package_pin':'U7'},
 {'camera':'OV2','signal':'D2','user_pin':'U7','package_pin':'W18'},
]
mapping['physical_xdc'] = 'project/fpga/xdc/ov5640_stereo_pins.xdc'
validate(mapping)
(BASE/'physical_pin_map_20261027.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
def table(camera):
    lines=['| 相机信号 | 摄像头 P1 脚 | PYNQ-Z2 接头 | 接头物理脚/丝印 | FPGA 封装脚 |','|---|---:|---|---|---|']
    for r in mapping['signals']:
        if r['camera']!=camera: continue
        header = str(r['board_pin']) if r['signal']!='PWDN' else f"{r['board_label']} / J4-{r['board_pin']}"
        lines.append(f"| {camera}_{r['signal']} | {r['camera_pin']} | {r['board_connector']} | {header} | {r['package_pin']} |")
    return chr(10).join(lines)
text=(BASE/'interface_and_pin_map.md').read_text(encoding='utf-8')
old='状态：OV5640 的 720p30 RGB565 配置、完整冷启动 RTL 和软件/RTL 验证已完成；按用户指定物理分区，左相机 OV1 使用 Raspberry Pi 23～40 脚区域的 14 个 IO，右相机 OV2 使用 1～22 脚区域的 14 个 IO，两路 PWDN 分别使用 Arduino D6/D7，30 根信号分配已落表。剩余工作是电气/引脚占用复核、完整 XDC、整板采集链路集成和真实相机验收。'
new='状态：720p30 RGB565 配置与完整冷启动 RTL 保持既有版本；本次将用户最新版引脚安排及四处 PCLK 修正写入统一 JSON，并生成 30 根信号的物理 XDC。OV1/OV2 现跨 RPi 两端分区，旧连续分区方案已取代；PWDN 沿用 Arduino D6/D7。剩余为板级电气/输入时序、整板采集链路及真实相机验收。'
if old not in text: raise RuntimeError('Missing status anchor')
text=text.replace(old,new)
text=text.replace('其余 28 根已按下节左右物理分区逐脚分配','其余 28 根已按下节最新版接线逐脚分配')
text=text.replace('sign_glove_master.xdc 第 65 行将 D6–D13 标为调试与扩展预留','sign_glove_master.xdc 将 D6–D13 标为调试与扩展预留')
text=text.replace('此处仅记录候选接线，不代表综合网表或板端验证。后续须在候选顶层引出 ov1_pwdn/ov2_pwdn 并绑定 R16/U17，生成并验收配套 bit/HWH。','本次物理 XDC 已将 ov1_pwdn/ov2_pwdn 绑定 R16/U17；综合网表验证见本次验收目录，配套系统 bit/HWH 与板端验收仍待完成。')
start=text.index('## 按物理距离分配左右相机')
end=text.index('## 剩余接线、集成与板上验收项目',start)
section='''## 当前接线分配（2026-10-27 已落地）

采用旧对话最后一版完整用户列表，DO 规范为 D0、VSNC 为 VSYNC、RST 为 RESET；为直接 PCLK 采样，只调整四项：OV1 交换 PCLK/VSYNC，OV2 交换 PCLK/D2。两路 PCLK 分别为 Y9、U7，均为时钟能力 P 端。其余用户信号保持原安排，两路 PWDN 沿用 R16/U17。

这版跨越 RPi 两半区；旧“OV1=23～40、OV2=1～22”的连续分区不再适用。左右相机以模块 OV1/OV2 丝印和安装方向核对。RPi 脚号采用 TUL v1.1 表22并与官方 PYNQ v3.0.1 base.xdc 核对；v1.0 截图中的旧映射不再使用。

### 左摄像头 OV1

''' + table('OV1') + '''

### 右摄像头 OV2

''' + table('OV2') + '''

### 约束与验证边界

- [physical_pin_map_20261027.json](physical_pin_map_20261027.json) 为唯一机读映射；[物理XDC](../../fpga/xdc/ov5640_stereo_pins.xdc) 由生成器派生。30 根信号无重复，28 根 RPi IO 加 2 根 Arduino PWDN，均不占电源/地针。
- 生成器支持 --check 检查JSON/XDC一致。XDC在赋值前检查全部端口及管脚冲突，避免误加载进没有相机端口的W6。
- XDC只设置PACKAGE_PIN/IOSTANDARD；不虚构传感器延迟，不加入专用时钟布线绕过，不自动修改W6 XPR/BD。84 MHz为配置计算值，实际频率和延迟仍待测量。
- SCCB由现有RTL维持只拉低/高阻，使用模组上的2.8 V上拉，本XDC不启用FPGA上拉。P1-38=3.3V、P1-37/39=GND，P1-40不作相机供电。
- Pmod A共享八个IO属于这28根RPi IO，不能同时另接SPI；旧SPI外部端口与约束已在源码移除，板上旧固件尚未更新。
- 独立综合/布局布线、pad、时钟资源和测试结果见[本次验证](pin_configuration_validation_20261027/README.md)。这些检查不等同于整板HDMI/音频/DDR集成或真实相机验收，未生成或部署新bit/HWH。

'''
text=text[:start]+section+text[end:]
text=text.replace('按已落表的 30 根信号分配，确认相机候选顶层端口，补齐完整 XDC；核验两路 PCLK 的时钟资源/布线和输入时序；','30 根物理约束已生成；在整板接入时复核与其他 IO/时钟的集成，并补足基于实测/规格的输入时序约束；')
text=text.replace('本次已确定接线分配，不代表已完成所有电气与实现验收；在相应证据齐备前，不将其直接加入当前运行 W6 工程的活动约束或作为正式发布固件。','本次已将接线落实为可校验的物理XDC，只适用于含相机端口的顶层。电气、外部输入时序及整板/实物验收未完成前，不作为正式发布固件。')
(BASE/'interface_and_pin_map.md').write_text(text,encoding='utf-8')
review='''# 2026-10-27 最新版摄像头引脚修改记录

状态：已完成统一JSON和物理XDC落地，取代原建议。旧候选只改四项：

| 相机/信号 | 用户候选 | 本次采用 | RPi物理脚 |
|---|---|---|---:|
| OV1 PCLK | W10 | Y9 | 40 |
| OV1 VSYNC | Y9 | W10 | 23 |
| OV2 PCLK | W18 | U7 | 11 |
| OV2 D2 | U7 | W18 | 3 |

其余26根含两路沿用的PWDN保持原安排。W10/W18是普通IO；Y9=IO_L14P_T2_SRCC_13、U7=IO_L11P_T1_SRCC_13满足单端时钟P侧要求。没有专用时钟布线绕过。DO、VSNC、RST分别规范为D0、VSYNC、RESET。

完整表见[当前接线](interface_and_pin_map.md)，唯一机读来源[JSON](physical_pin_map_20261027.json)，生成结果[物理XDC](../../fpga/xdc/ov5640_stereo_pins.xdc)。旧分区版本保存在本次验证目录before/，已被取代。

Pmod A/B旧SPI外部端口及约束已释放，内部传感器/DMA/KWS仍保留，见[SPI释放记录](../pmod_spi_release_20261027/README.md)。camera XDC不自动加入没有这些端口的W6。

实际检查及未覆盖边界见[本次验收](pin_configuration_validation_20261027/README.md)。未修改已发布bit/HWH，未部署/运行中加载固件。真实接线、电平、采图及外部输入时序仍待验收。

依据：本目录保留的TUL v1.1表22、PYNQ v3.0.1 base.xdc，以及AMD本地库UG472 Clock-Capable Inputs。
'''
(BASE/'user_pin_review_20261027.md').write_text(review,encoding='utf-8')
rtl=ROOT/'project/fpga/rtl/ov5640_stereo/README.md'
t=rtl.read_text(encoding='utf-8')
t=t.replace('未完成真实相机验证、物理引脚约束、异步 FIFO、DDR/VDMA 或 HDMI 接入。','已完成30根物理引脚约束；未完成真实相机验证、外部输入时序、异步 FIFO、DDR/VDMA 或 HDMI 接入。')
t += chr(10)+'''## 2026-10-27 摄像头物理约束

最新版接线已写入统一JSON并派生project/fpga/xdc/ov5640_stereo_pins.xdc。OV1 PCLK=Y9、OV2 PCLK=U7；OV1 VSYNC=W10、OV2 D2=W18，其余按用户最新版，PWDN=R16/U17。当前映射跨RPi两半区，取代旧连续分区。

XDC应用于具备30根相机端口的顶层，全部端口/冲突检查先于赋值，不自动加入无相机端口的W6。生成器--check和独立Vivado检查见../../../analysis/ov5640_stereo_20261026/pin_configuration_validation_20261027/README.md。物理约束完成不代表外部输入时序、系统集成或板上采图通过。
'''
rtl.write_text(t,encoding='utf-8')
print('MAPPING_MIGRATION_PASS')
