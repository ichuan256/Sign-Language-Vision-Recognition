# PYNQ-Z2 R19 is HDMI_TX_HPDN (inverted hot-plug INPUT), not a TX enable.
# Keep legacy AXI GPIO addresses for software compatibility, but remove its
# output from the physical R19 pin. Read HPD through the diagnostic GPIO.
set hpd_scripts [file dirname [file normalize [info script]]]
source [file join $hpd_scripts ov5640_snapshot_hdmi_audio_status_bd.tcl]
current_bd_instance /
set flag [get_bd_pins video_flags_concat/In6]
set net [get_bd_nets -of_objects $flag]
disconnect_bd_net $net $flag
set port [get_bd_ports hdmi_out_hpd]
set net [get_bd_nets -of_objects $port]
disconnect_bd_net $net $port
delete_bd_objs $port
create_bd_port -dir I -from 0 -to 0 hdmi_out_hpd
connect_bd_net [get_bd_ports hdmi_out_hpd] $flag
validate_bd_design
puts "PYNQ_Z2_HPD_FIXED R19=INPUT inverted HPD; legacy GPIO output has no physical pad"
