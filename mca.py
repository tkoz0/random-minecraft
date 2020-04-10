import struct,gzip,zlib

class RegionFile:
    def __init__(self,mca): # initialize with binary mca data
        self.mca = mca
        self.chunk_offsets = [struct.unpack('>i',b'\x00'+mca[4*i:4*i+3])[0]
                              for i in range(1024)]
        self.chunk_sectors = [struct.unpack('>b',mca[4*i+3:4*i+4])[0]
                              for i in range(1024)]
        self.timestamps = [struct.unpack('>i',mca[4096+4*i:4096+4*i+4])[0]
                           for i in range(1024)]
        self.chunk_exists = [False]*1024
        self.chunk_lengths = [0]*1024
        self.compression_type = [0]*1024
        for c in range(1024):
            offset = self.chunk_offsets[c]
            if offset != 0: # chunk exists
                assert offset >= 2 # after timestamp table
                self.chunk_exists[c] = True
                self.chunk_lengths[c] = \
                    struct.unpack('>i',mca[4096*offset:4096*offset+4])[0]
                assert self.chunk_lengths[c] > 0
                self.compression_type[c] = \
                    struct.unpack('>b',mca[4096*offset+4:4096*offset+5])[0]
                assert self.compression_type[c] in [1,2]
                # ensure all chunk data fits
                assert 4096*offset+4+self.chunk_lengths[c] <= len(mca)
    def chunkExists(self,x,z):
        assert x in range(32) and z in range(32)
        return self.chunk_exists[32*z+x]
    def getChunkNBT(self,x,z):
        assert x in range(32) and z in range(32)
        c = 32*z+x # chunk index
        start_byte = 4096*self.chunk_offsets[c]
        length = self.chunk_lengths[c]
        if not self.chunk_exists[c]: return None
        if self.compression_type[c] == 1:
            return gzip.decompress(self.mca[start_byte+5:start_byte+4+length])
        elif self.compression_type[c] == 2:
            return zlib.decompress(self.mca[start_byte+5:start_byte+4+length])
        else: assert 0
    def getChunkTimestamp(self,x,z):
        assert x in range(32) and z in range(32)
        if not self.chunk_exists[c]: return 0
        return self.timestamps[32*z+x]
