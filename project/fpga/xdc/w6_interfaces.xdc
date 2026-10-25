# W6 source-synchronous interface budgets. Units: ns.
# SPI RTL: 100 MHz fabric, Mode 0, 1 MHz SCLK, receive CE on rising SCLK.
# MCP3008 DS20001295E: tDO<=200ns at 2.7V, tSU/tHD=50ns;
# reserve a further 50ns for module/wire/clock round-trip on input and output.
# This is an engineering wiring budget, not a measured cable characterization.
create_generated_clock -name spia_external -source \
    [get_pins system_i/sif_l/inst/u_spi/sclk_reg/C] \
    -divide_by 100 [get_ports spia_sclk]
set_input_delay -clock spia_external -clock_fall -max 250 [get_ports spia_miso]
set_input_delay -clock spia_external -clock_fall -min 0 [get_ports spia_miso]
# CE sample is 50 fabric cycles after the external falling edge, not
# the immediately following 100 MHz edge. Hold restores that edge pair.
set_multicycle_path 50 -setup -end -from [get_ports spia_miso]
set_multicycle_path 49 -hold -end -from [get_ports spia_miso]
set outputs [get_ports [list spia_mosi spia_cs*]]
set_output_delay -clock spia_external -max 100 $outputs
set_output_delay -clock spia_external -min -100 $outputs
# MOSI changes on SCLK falling; CS has a longer transaction guard time.
# Setup uses the preceding falling-edge CE; hold uses the FOLLOWING
# falling-edge CE (500ns after sample), not an arbitrary fast-clock edge.
set_multicycle_path 50 -setup -start -to $outputs
set_multicycle_path 99 -hold -start -to $outputs
create_generated_clock -name spib_external -source \
    [get_pins system_i/sif_r/inst/u_spi/sclk_reg/C] \
    -divide_by 100 [get_ports spib_sclk]
set_input_delay -clock spib_external -clock_fall -max 250 [get_ports spib_miso]
set_input_delay -clock spib_external -clock_fall -min 0 [get_ports spib_miso]
# CE sample is 50 fabric cycles after the external falling edge, not
# the immediately following 100 MHz edge. Hold restores that edge pair.
set_multicycle_path 50 -setup -end -from [get_ports spib_miso]
set_multicycle_path 49 -hold -end -from [get_ports spib_miso]
set outputs [get_ports [list spib_mosi spib_cs*]]
set_output_delay -clock spib_external -max 100 $outputs
set_output_delay -clock spib_external -min -100 $outputs
# MOSI changes on SCLK falling; CS has a longer transaction guard time.
# Setup uses the preceding falling-edge CE; hold uses the FOLLOWING
# falling-edge CE (500ns after sample), not an arbitrary fast-clock edge.
set_multicycle_path 50 -setup -start -to $outputs
set_multicycle_path 99 -hold -start -to $outputs
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
