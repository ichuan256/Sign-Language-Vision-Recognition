"""Read-only diagnostics without importing the PYNQ runtime in every RPC."""
import mmap
import os
import struct


class Registers:
    def __init__(self, address, length=65536):
        self.address=address;self.length=length

    def read(self, offset):
        if offset % 4 or not 0 <= offset <= self.length-4:
            raise ValueError('Invalid register offset')
        fd=os.open('/dev/mem',os.O_RDONLY|os.O_SYNC)
        try:
            with mmap.mmap(fd,self.length,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ,offset=self.address) as page:
                return struct.unpack_from('<I',page,offset)[0]
        finally:os.close(fd)
