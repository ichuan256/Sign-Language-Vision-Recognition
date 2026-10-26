# W6 audio / HDMI interface budgets. Units: ns.
# Pmod A/B SPI interfaces removed on 2026-10-27.
# PYNQ audio core: clk_cntr(4)=BCLK, clk_cntr(10)=LRCLK.
# BCLK rises on count 16 and falls on count 32. Deserializer CE samples
# one fabric cycle after the BCLK rising edge (17 cycles after falling).
# ADAU1761 Rev.F: ADC_SDATA tSOD<=50ns, DAC_SDATA/LRCLK tSU/tHD>=5ns.
# Reserve 10ns extra for PCB/clock skew. No audio data path is false-pathed.
set audio_counter {system_i/audio_codec_ctrl_0/U0/USER_LOGIC_I/clk_cntr_reg[4]/C}
create_generated_clock -name audio_bclk -source [get_pins $audio_counter] \
    -edges {33 65 97} [get_ports bclk]
set_input_delay -clock audio_bclk -clock_fall -max 60 [get_ports sdata_i]
set_input_delay -clock audio_bclk -clock_fall -min 0 [get_ports sdata_i]
set_multicycle_path 17 -setup -end -from [get_ports sdata_i]
set_multicycle_path 16 -hold -end -from [get_ports sdata_i]
set_output_delay -clock audio_bclk -max 15 [get_ports sdata_o]
set_output_delay -clock audio_bclk -min -15 [get_ports sdata_o]
# Serializer changes SDATA one fabric cycle after BCLK falling.
# Next allowed transition is 17 cycles after the sampling BCLK rising edge;
# hold=14+17=31 selects that next enabled launch, rather than a fast-clock edge.
set_multicycle_path 15 -setup -start -to [get_ports sdata_o]
set_multicycle_path 31 -hold -start -to [get_ports sdata_o]
# LRCLK is framing data to the codec, not a fabric clock. It changes on
# BCLK falling itself, one fabric cycle before serialized SDATA.
# Following enabled launch is 16 cycles after the sampling rising edge.
set_output_delay -clock audio_bclk -max 15 [get_ports lrclk]
set_output_delay -clock audio_bclk -min -15 [get_ports lrclk]
set_multicycle_path 16 -setup -start -to [get_ports lrclk]
set_multicycle_path 31 -hold -start -to [get_ports lrclk]

# GPIO used as a static panel enable: no receiving synchronous clock.
set_false_path -to [get_ports {hdmi_out_hpd[0]}]

# TMDS forwarded clock is the same 10:1 serializer as the data lanes, fed
# with 1111100000. Its serial clock is divided by 5 on the clock lane.
# Data-lane receiver aperture / cable skew are deliberately not invented.
create_generated_clock -name hdmi_forwarded -source \
    [get_pins system_i/video/hdmi_out/frontend/rgb2dvi_0/U0/ClockSerializer/SerializerMaster/CLK] \
    -divide_by 5 [get_ports hdmi_out_clk_p]
