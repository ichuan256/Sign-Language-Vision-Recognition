source [file join [file dir [info script]] hls_startup.tcl]

if [catch {hls_proc apcc $argv} result options] {
  puts $errorInfo
  return -code [dict get $options -code]
}

