"""Extract existing board PS settings without modifying W6."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'project/fpga/project/glove/glove.srcs/sources_1/bd/system/system.bd'
OUT=ROOT/'project/analysis/ov5640_snapshot_20261027/ps_config.tcl'
def main():
    params=json.loads(SOURCE.read_text(encoding='utf-8'))['design']['components']['ps7']['parameters']
    names={'PCW_UIPARAM_DDR_PARTNO','PCW_UIPARAM_DDR_FREQ_MHZ','PCW_UIPARAM_DDR_BUS_WIDTH',
        'PCW_UIPARAM_DDR_MEMORY_TYPE','PCW_UIPARAM_DDR_ENABLE','PCW_UIPARAM_DDR_DRAM_WIDTH',
        'PCW_UIPARAM_DDR_BANK_ADDR_COUNT','PCW_UIPARAM_DDR_ROW_ADDR_COUNT','PCW_UIPARAM_DDR_COL_ADDR_COUNT',
        'PCW_UIPARAM_DDR_TRAIN_DATA_EYE','PCW_UIPARAM_DDR_TRAIN_READ_GATE','PCW_UIPARAM_DDR_TRAIN_WRITE_LEVEL',
        'PCW_UIPARAM_DDR_USE_INTERNAL_VREF','PCW_CRYSTAL_PERIPHERAL_FREQMHZ','PCW_APU_PERIPHERAL_FREQMHZ'}
    names.update(k for k in params if k.startswith('PCW_UIPARAM_DDR_DQS_TO_CLK_DELAY_') or k.startswith('PCW_UIPARAM_DDR_BOARD_DELAY'))
    settings={k:v['value'] for k,v in params.items() if k in names}
    settings.update(PCW_USE_S_AXI_HP0='1',PCW_USE_S_AXI_HP1='0',PCW_USE_S_AXI_HP2='0',
        PCW_USE_S_AXI_HP3='0',PCW_USE_M_AXI_GP0='1',PCW_USE_FABRIC_INTERRUPT='0',
        PCW_EN_CLK1_PORT='0',PCW_EN_CLK2_PORT='0',PCW_EN_CLK3_PORT='0',
        PCW_EN_I2C1='0',PCW_EN_EMIO_I2C1='0',PCW_I2C1_PERIPHERAL_ENABLE='0',
        PCW_EN_EMIO_GPIO='0',PCW_FPGA0_PERIPHERAL_FREQMHZ='100',PCW_EN_CLK0_PORT='1',PCW_EN_RST0_PORT='1')
    lines=['# Derived from W6 PS7; source SHA256: '+hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'set snapshot_ps_config [list '+chr(92)]
    for k,v in sorted(settings.items()):
        if any(c in str(v) for c in ('{','}',chr(92))): raise ValueError(k)
        lines.append('    CONFIG.'+k+' {'+str(v)+'} '+chr(92))
    lines.append(']')
    OUT.write_text(chr(10).join(lines)+chr(10),encoding='utf-8')
    print(f'Wrote {len(settings)} PS parameters: {OUT}')
if __name__=='__main__': main()
