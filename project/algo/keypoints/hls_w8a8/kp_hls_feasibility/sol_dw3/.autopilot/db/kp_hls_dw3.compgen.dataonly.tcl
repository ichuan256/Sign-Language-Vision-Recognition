# This script segment is generated automatically by AutoPilot

set axilite_register_dict [dict create]
set port_ctrl {
in_r { 
	dir I
	width 64
	depth 1
	mode ap_none
	offset 16
	offset_end 27
}
w { 
	dir I
	width 64
	depth 1
	mode ap_none
	offset 28
	offset_end 39
}
bias { 
	dir I
	width 64
	depth 1
	mode ap_none
	offset 40
	offset_end 51
}
M { 
	dir I
	width 64
	depth 1
	mode ap_none
	offset 52
	offset_end 63
}
F { 
	dir I
	width 32
	depth 1
	mode ap_none
	offset 64
	offset_end 71
}
out_r { 
	dir I
	width 64
	depth 1
	mode ap_none
	offset 72
	offset_end 83
}
ap_start { }
ap_done { }
ap_ready { }
ap_idle { }
interrupt {
}
}
dict set axilite_register_dict ctrl $port_ctrl


