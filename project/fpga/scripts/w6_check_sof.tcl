# Read-only structural regression gate, usable without opening a project.
# Set w6_sof_netlist to the generated system.v before sourcing this file.
if {![info exists w6_sof_netlist] || ![file isfile $w6_sof_netlist]} {
    error "Missing generated HDMI netlist: set w6_sof_netlist first."
}
set sof_file [open $w6_sof_netlist r]
set sof_text [read $sof_file]
close $sof_file
# Check both ends of every SOF/EOL hop. This deliberately rejects constant
# tie-offs even when the HLS component.xml advertises an incorrect width.
foreach {port net} {
    stream_out_24_TUSER pixel_unpack_stream_out_24_TUSER
    s_axis_tuser pixel_unpack_stream_out_24_TUSER
    m_axis_tuser axis_register_slice_0_M_AXIS_TUSER
    stream_in_24_TUSER axis_register_slice_0_M_AXIS_TUSER
    stream_out_24_TUSER color_convert_stream_out_24_TUSER
    video_in_tuser color_convert_stream_out_24_TUSER
    stream_out_24_TLAST pixel_unpack_stream_out_24_TLAST
    s_axis_tlast pixel_unpack_stream_out_24_TLAST
    m_axis_tlast axis_register_slice_0_M_AXIS_TLAST
    stream_in_24_TLAST axis_register_slice_0_M_AXIS_TLAST
    stream_out_24_TLAST color_convert_stream_out_24_TLAST
    video_in_tlast color_convert_stream_out_24_TLAST
} {
    if {[string first ".${port}($net)" $sof_text] < 0} {
        error "HDMI sideband regression: expected $port connected to $net in $w6_sof_netlist"
    }
}
puts "HDMI_SOF_CHECK_PASS: pixel_unpack -> register_slice -> color_convert -> frontend (SOF + EOL)"
