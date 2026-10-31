set status_cache_scripts [file dirname [file normalize [info script]]]
source [file join $status_cache_scripts w6_timing_ip_constraints.tcl]
set status_cache [file normalize [file join $status_cache_scripts ../../_tmp/ov1_av_status_20261031/vivado/snapshot.cache/ip]]
if {![file isdirectory $status_cache]} {error "Expected validated 2024.1 IP synthesis cache absent"}
config_ip_cache -use_cache_location $status_cache
set_property IP_CACHE_PERMISSIONS {read write} [current_project]
puts "AV_STATUS_MANAGED_IP_CACHE $status_cache"
