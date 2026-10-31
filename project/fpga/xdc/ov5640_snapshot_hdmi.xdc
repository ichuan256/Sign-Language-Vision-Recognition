# Only static HDMI enable and forwarded clock; no invented sink/cable budget.
# The camera pre-opt constraint hook continues to own camera I/O and CDC.
set hpd_port [get_ports {hdmi_out_hpd[0]}]
if {[get_property DIRECTION $hpd_port] eq "IN"} {
    # Asynchronous monitor HPD input, sampled through the diagnostic XPM CDC.
    set_false_path -from $hpd_port
} else {
    # Compatibility with historical output-only candidates; not for new boards.
    set_false_path -to $hpd_port
}
create_generated_clock -name hdmi_forwarded -source \
    [get_pins system_i/video/hdmi_out/frontend/rgb2dvi_0/U0/ClockSerializer/SerializerMaster/CLK] \
    -divide_by 5 [get_ports hdmi_out_clk_p]
