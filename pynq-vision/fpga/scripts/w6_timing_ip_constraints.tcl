# rgb2dvi's legacy LATE XDC creates SerialClk from PixelClk, but W6 supplies
# both externally: MMCM -> BUFIO(serial), and the parallel BUFR /5(pixel).
# Keep automatic primitive-derived clocks, OOC clocks and CDC constraints.
set legacy [get_files -all -quiet */rgb2dvi_clocks.xdc]
if {[llength $legacy] != 1} {error "Expected exactly one rgb2dvi_clocks.xdc"}
set_property USED_IN_SYNTHESIS false $legacy
set_property USED_IN_IMPLEMENTATION false $legacy
puts "W6: disabled invalid legacy pixel-to-serial clock declaration: $legacy"
