# Source with the W6 system BD open. Releases external Pmod A/B SPI only.
# Internal legacy sensor/DMA/KWS removal is a separate M0b change.
if {[current_bd_design] ne {system}} {
    error {Open the W6 system BD before releasing Pmod SPI interfaces.}
}
set w6_spi_ports [get_bd_ports -quiet {spia_* spib_*}]
if {[llength $w6_spi_ports]} {
    set w6_spi_nets [get_bd_nets -quiet -of_objects $w6_spi_ports]
    if {[llength $w6_spi_nets]} {delete_bd_objs $w6_spi_nets}
    delete_bd_objs $w6_spi_ports
}
# Keep retained sensor input pins defined after removing their external ports.
set w6_spi_miso [get_bd_pins -quiet {sif_l/miso sif_r/miso}]
if {[llength $w6_spi_miso]} {
    set w6_spi_zero [get_bd_pins -quiet const_zero/dout]
    if {[llength $w6_spi_zero] != 1 ||
        [get_property CONFIG.CONST_VAL [get_bd_cells const_zero]] != 0 ||
        [get_property CONFIG.CONST_WIDTH [get_bd_cells const_zero]] != 1} {
        error {Expected a one-bit const_zero source for unused MISO inputs.}
    }
    foreach w6_spi_pin $w6_spi_miso {
        set w6_spi_old [get_bd_nets -quiet -of_objects $w6_spi_pin]
        set w6_spi_zero_net [get_bd_nets -quiet -of_objects $w6_spi_zero]
        if {[llength $w6_spi_old] && $w6_spi_old eq $w6_spi_zero_net} {continue}
        if {[llength $w6_spi_old]} {disconnect_bd_net $w6_spi_old $w6_spi_pin}
        connect_bd_net $w6_spi_zero $w6_spi_pin
    }
}
if {[llength [get_bd_ports -quiet {spia_* spib_*}]]} {
    error {Pmod SPI external ports still exist after removal.}
}
puts {Pmod A/B: external SPI ports removed; legacy MISO inputs tied low.}
