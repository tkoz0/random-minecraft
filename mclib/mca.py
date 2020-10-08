'''
Implementation of the MCA region file format. Uses the entire binary data from
the MCA file, but only decodes chunks into NBT objects when requested. Results
written are optimized a bit compared to what Minecraft may be using.

When writing a (possibly modified) MCA file, the sector padding at the end of
chunk data is zeroed (to improve compressibility) and unused sectors are
eliminated, packing chunks into the minimum amount of 4KiB sectors required.
Unmodified chunks are written binary exact to how they were read (with the
padding zeroed), and modified chunks are compressed using zlib/deflate (code 2)
which is the same as the official Minecraft client uses.
'''

import gzip
from mclib.nbt import decode_nbt 
import random
import struct
import zlib

# compression types
COMPRESS_GZIP = 1
COMPRESS_ZLIB = 2
COMPRESS_NONE = 3

# map compression to compressor function (byte string -> byte string)
COMPRESSOR = dict()
COMPRESSOR[COMPRESS_GZIP] = gzip.compress
COMPRESSOR[COMPRESS_ZLIB] = zlib.compress
COMPRESSOR[COMPRESS_NONE] = lambda x : x
DECOMPRESSOR = dict()
DECOMPRESSOR[COMPRESS_GZIP] = gzip.decompress
DECOMPRESSOR[COMPRESS_ZLIB] = zlib.decompress
DECOMPRESSOR[COMPRESS_NONE] = lambda x : x

class MCAError(Exception): pass

# chunk index conversions
def _chunk2index(x,z):
    if not (x in range(32) and z in range(32)): raise ValueError()
    return 32*z + x
def _chunk2xz(ci):
    if not (ci in range(1024)): raise ValueError()
    return (ci%32,ci//32)

class RegionFile:
    def __init__(self,file):
        ''' initialize with byte string or file name '''
        if type(file) != bytes: # get MCA byte string with file path
            file = open(file,'rb').read()
        if len(file) & 0xFFF != 0:
            raise MCAError('file not a multiple of 4KiB')
        if len(file) < 8192:
            raise MCAError('incomplete mca header')
        # None if chunk doesnt exist, (compression_id,raw_bytes) otherwise
        self._chunk_bytes = [None] * 1024
        # stores None, replaced with NBT object when existing chunk is loaded
        self._chunks = [None] * 1024
        self._timestamps = [None] * 1024
        self._changed = [False] * 1024
        # mark chunk that each sector is used for, -1 = unused, -2 = mca header
        sectors = [-1]*(len(file)//4096)
        sectors[0] = sectors[1] = -2
        for ci in range(1024):
            timestamp_bytes = file[4096+4*ci:4100+4*ci]
            self._timestamps[ci] = struct.unpack('>i',timestamp_bytes)[0]
            sector_offset = struct.unpack('>i',b'\x00'+file[4*ci:4*ci+3])[0]
            sector_count = struct.unpack('>B',file[4*ci+3:4*ci+4])[0]
            if sector_offset == 0 and sector_count == 0:
                continue # chunk does not exist
            x,z = _chunk2xz(ci)
            if sector_offset < 2:
                raise MCAError('chunk (%d,%d) offset = %d'%(x,z,sector_offset))
            if sector_count == 0:
                raise MCAError('chunk (%d,%d) is empty'%(x,z))
            byte_off = sector_offset * 4096
            byte_end = byte_off + (sector_count * 4096)
            chunk_length = struct.unpack('>i',file[byte_off:byte_off+4])[0]
            compression_id = struct.unpack('>b',file[byte_off+4:byte_off+5])[0]
            if compression_id not in COMPRESSOR:
                raise MCAError('chunk (%d,%d) unknown compression id %d'
                               %(x,z,compression_id))
            if chunk_length < 1:
                raise MCAError('chunk (%d,%d) length is not positive'%(x,z))
            if byte_off + 4 + chunk_length >= byte_end:
                raise MCAError('chunk (%d,%d) length exceeds its sectors'%(x,z))
            for sector in range(sector_offset,sector_offset+sector_count):
                if sector >= len(sectors):
                    raise MCAError('chunk (%d,%d) goes past end of file'%(x,z))
                if sectors[sector] == -1:
                    sectors[sector] = ci
                else:
                    raise MCAError('sector %d is shared by > 1 chunk'%sector)
            chunk_bytes = file[byte_off+5:byte_off+4+chunk_length]
            self._chunk_bytes[ci] = (compression_id,chunk_bytes)
    def loadChunk(self,x,z):
        '''
        loads chunk data from input binary data
        overwrites changes if any were made
        '''
        if self._chunk_bytes[_chunk2index(x,z)] is None: return
        compression_id,raw_bytes = self._chunk_bytes[_chunk2index(x,z)]
        uncompressed_chunk = DECOMPRESSOR[compression_id](raw_bytes)
        self._chunks[_chunk2index(x,z)] = decode_nbt(uncompressed_chunk)
        self._changed[_chunk2index(x,z)] = True
    def loadAllChunks(self):
        ''' loads every chunk in the region file from the binary data '''
        for z in range(32):
            for x in range(32):
                self.loadChunk(x,z)
    def chunkExists(self,x,z):
        ''' does the chunk exist in this region file '''
        return self._chunk_bytes[_chunk2index(x,z)] is not None
    def getTimestamp(self,x,z):
        ''' returns the chunk timestamp '''
        return self._timestamps[_chunk2index(x,z)]
    def setTimestamp(self,x,z,timestamp=0):
        ''' changes the chunk timestamp '''
        if type(timestamp) != int or timestamp < -2**31 or timestamp >= 2**31:
            raise ValueError()
        self._timestamps[_chunk2index(x,z)] = timestamp
    def getChunk(self,x,z):
        ''' returns the chunk data, None if not loaded or not present '''
        return self._chunks[_chunk2index(x,z)]
    def setChunk(self,x,z,chunk=None):
        ''' sets the chunk data, must be None or a TAG_Compound '''
        if chunk is not None and type(chunk) != nbt.TAG_Compound:
            raise ValueError()
        self._chunks[_chunk2index(x,z)] = chunk
        self._changed[_chunk2index(x,z)] = True
    def encodeMCA(self,compression=COMPRESS_ZLIB):
        ''' produces a byte string for MCA output '''
        locations = [0]*4096
        timestamps = list(b''.join(struct.pack('>i',self._timestamps[ci])
                                   for ci in range(1024)))
        chunk_sectors = b''
        for ci in range(1024):
            chunk_data = None # change to byte string if including chunk
            if self._changed[ci]: # include nonnull chunk in data
                if self._chunks[ci] is not None:
                    chunk_nbt = self._chunks[ci].encodeTag()
                    chunk_data = COMPRESSOR[compression](chunk_nbt)
            else: # keep same chunk if it was in input
                if self._chunk_bytes[ci] is not None:
                    compression_id,raw_bytes = self._chunk_bytes[ci]
                    if compression_id == compression:
                        chunk_data = raw_bytes
                    else:
                        uncompressed = DECOMPRESSOR[compression_id](raw_bytes)
                        chunk_data = COMPRESSOR[compression](uncompressed)
            if chunk_data is None: # nothing to encode, zero the timestamp
                timestamps[4*ci:4*ci+4] = [0,0,0,0]
                continue
            x,z = _chunk2xz(ci)
            length = len(chunk_data) + 1
            alloc_bytes = length + 4 # include length bytes
            if alloc_bytes & 0xFFF != 0: # pad to 4KiB multiple
                alloc_bytes += 4096 - (alloc_bytes % 4096)
            offset = 2 + (len(chunk_sectors) // 4096)
            sectors = alloc_bytes // 4096
            if offset >= 2**24: raise MCAError('chunk offset too large')
            if sectors >= 256: raise MCAError('chunk (%d,%d) too large'%(x,z))
            # write location info to header
            locations[4*ci:4*ci+3] = list(struct.pack('>i',offset)[1:])
            locations[4*ci+3] = sectors
            # append chunk sectors
            chunk_info = struct.pack('>i',length) + bytes([compression])
            chunk_padding = b'\x00' * (alloc_bytes - length - 4)
            chunk_sectors += chunk_info + chunk_data + chunk_padding
        return bytes(locations) + bytes(timestamps) + bytes(chunk_sectors)
    def writeFile(self,file):
        ''' writes the chunk data as a region file to the specified filename '''
        fileout = open(file,'wb')
        fileout.write(self.encodeMCA())
        fileout.flush();
        fileout.close()
    def _shuffleChunks(self):
        ''' randomizes chunk positions, mostly for testing '''
        mapping = list(range(1024))
        random.shuffle(mapping)
        # make new variables
        old_chunk_bytes = self._chunk_bytes
        old_chunks = self._chunks
        old_timestamps = self._timestamps
        old_changed = self._changed
        self._chunk_bytes = [None]*1024
        self._chunks = [None]*1024
        self._timestamps = [None]*1024
        self._changed = [None]*1024
        for ci in range(1024): # move old mapping[ci] chunk to index ci
            self._chunk_bytes[ci] = old_chunk_bytes[mapping[ci]]
            self._chunks[ci] = old_chunks[mapping[ci]]
            self._timestamps[ci] = old_timestamps[mapping[ci]]
            self._changed[ci] = old_timestamps[mapping[ci]]

