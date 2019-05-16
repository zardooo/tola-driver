# -*- coding:utf-8 -*-


from rtlsdr import *
from ctypes import *


class NRtlSdr(RtlSdr):
    
    def read_bytes(self, num_bytes=4096):
        ''' Read specified number of bytes from tuner. Does not attempt to unpack
        complex samples (see read_samples()), and data may be unsafe as buffer is
        reused.
        '''
        # FIXME: libsdrrtl may not be able to read an arbitrary number of bytes

        BUFFER = []
        num_bytes = int(num_bytes)

        # create buffer, as necessary
        array_type = (c_ubyte*num_bytes)
        BUFFER = array_type()
       
        result = librtlsdr.rtlsdr_read_sync(self.dev_p, BUFFER, num_bytes,\
                                            byref(self.num_bytes_read))
        if result < 0:
            self.close()
            raise IOError('Error code %d when reading %d bytes'\
                          % (result, num_bytes))

        if self.num_bytes_read.value != num_bytes:
            self.close()
            raise IOError('Short read, requested %d bytes, received %d'\
                          % (num_bytes, self.num_bytes_read.value))

        return BUFFER
