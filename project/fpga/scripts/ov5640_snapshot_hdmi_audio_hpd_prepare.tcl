set hpd_scripts [file dirname [file normalize [info script]]]
set snapshot_out [file normalize [file join $hpd_scripts ../../_tmp/ov1_av_hpd_20261101]]
set snapshot_bd_extension [file join $hpd_scripts ov5640_snapshot_hdmi_audio_hpd_bd.tcl]
source [file join $hpd_scripts ov5640_snapshot_hdmi_audio_status_prepare.tcl]
