# Main tcl script sourced by hls
common::load_feature base
# Use HDI_APPROOT since RDI_APPROOT may be a search-path
if { [string match -nocase "window*" $::tcl_platform(os)] && [llength [glob -nocomplain $::env(HDI_APPROOT)/lib/win*/xv_hlstasks.dll]] } {
  rdi::load_library "vitis_hls" xv_hlstasks
} elseif { [llength [glob -nocomplain $::env(HDI_APPROOT)/lib/lnx*/libxv_hlstasks*]] } {
  rdi::load_library "vitis_hls" libxv_hlstasks
} else {
  rdi::load_library "vitis_hls" librdi_hlstasks
}

# No source tracing
common::set_param tcl.notrace 1

# No RDI Tcl interrupt handling.  HLS manages ctrl-c
common::set_param tcl.nosigint 1

# Reset message number limitation
common::set_param messaging.defaultLimit 1000000

namespace import -force common::version
namespace import -force common::set_param
namespace import -force common::get_param

proc hls_proc {name args} {
  set ::argv0 $name
  #puts "DBG:TCL-STARTUP: running hls_proc $name args=$args ::argv0=$::argv0 argv=$::argv"
  set args [lindex $args 0]
  set newargs [list]
  foreach arg $args { 
    # Handle args with spaces
    if { [string first {"} $arg] == -1 && [regexp {[[:space:]]} $arg] } { 
      set arg "\"$arg\"" 
    } 
    lappend newargs $arg 
  }
  if { $name eq "apcc" } {
    uplevel 1 hls::apcc {*}$newargs
  } else {
    uplevel 1 hls::main {*}$newargs; # See hls.cxx (this is also where tcl file arg is sourced)
  }
}

