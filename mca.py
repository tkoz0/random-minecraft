import struct,gzip,zlib,nbt

class MCAError(Exception): pass

def _chunk_i(x,z): # chunk_index
    if not (x in range(32) and z in range(32)): raise ValueError()
    return 32*z+x

class RegionFile:
    def __init__(self,file): # can be filename or byte string
        if type(file) != bytes: file = open(file,'rb').read()
        if len(file) % 0x1000 != 0: raise MCAError('not a multiple of 4KiB')
        if len(file) < 0x2000: raise MCAError('incomplete mca header')
        self.mca = file # input data
        self.chunks = [None]*0x400 # store each chunk
        self.loaded = [False]*0x400 # chunk NBT was loaded from MCA file?
        self.timestamps = [0]*0x400
        # map cluster to which chunk, indexes 0 and 1 are header reserved
        clustermap = [None]*(len(file)//0x1000)
        clustermap[0] = clustermap[1] = (-1,-1)
        for ci in range(0x400): # fill in clustermap
            self.timestamps[ci] = \
                struct.unpack('>i',file[0x1000+4*ci:0x1004+4*ci])[0]
            coords = (ci%32,ci//32) # x,z chunk coordinates relative to MCA file
            offset = struct.unpack('>i',b'\x00'+file[4*ci:4*ci+3])[0]
            sectors = struct.unpack('>B',file[4*ci+3:4*ci+4])[0]
            if offset == 0 and sectors == 0: continue # chunk does not exist
            if offset < 2:
                raise MCAError('chunk (%d,%d) offset overwrites header'%coords)
            if sectors == 0:
                raise MCAError('chunk (%d,%d) allocates 0 sectors'%coords)
            start_byte = 0x1000*offset
            length = struct.unpack('>i',file[start_byte:start_byte+4])[0]
            if length < 1:
                raise MCAError('chunk (%d,%d) has invalid length'%coords)
            compression = struct.unpack('>b',file[start_byte+4:start_byte+5])[0]
            if not (compression in [1,2]):
                raise MCAError('chunk (%d,%d) has invalid compression id %d'
                               %(coords+compression))
            for cluster in range(offset,offset+sectors): # mark chunk sectors
                if cluster > len(clustermap):
                    raise MCAError('chunk (%d,%d) goes past end of file'
                                   %coords)
                if clustermap[cluster] != None:
                    raise MCAError('chunk (%d,%d) overwrites chunk (%d,%d)'
                                   %(coords+clustermap[cluster]))
                clustermap[cluster] = coords
    def getTimestamp(self,x,z): return self.timestamps[_chunk_i(x,z)]
    def setTimestamp(self,x,z,t=0):
        assert type(t) == 0 and -2**31 <= t < 2**31
        self.timestamps[_chunk_i(x,z)] = t
    # load NBT data for a chunk from the MCA file
    # returns the chunk, which is None if the chunk does not exist
    def loadChunk(self,x,z):
        ci = _chunk_i(x,z)
        if self.loaded[ci]: return
        coords = (ci%32,ci//32)
        offset = struct.unpack('>i',b'\x00'+self.mca[4*ci:4*ci+3])[0]
        sectors = struct.unpack('>B',self.mca[4*ci+3:4*ci+4])[0]
        if offset == 0 and sectors == 0:
            self.loaded[ci] = True
            return None # chunk does not exist
        start = 0x1000*offset
        length = struct.unpack('>i',self.mca[start:start+4])[0]
        compression = struct.unpack('>b',self.mca[start+4:start+5])[0]
        chunkbytes = self.mca[start+5:start+4+length]
        if compression == 1:
            chunk = nbt.decode_nbt(gzip.decompress(chunkbytes))
        elif compression == 2:
            chunk = nbt.decode_nbt(zlib.decompress(chunkbytes))
        else: assert 0 # should never happen
        self.chunks[ci] = chunk
        self.loaded[ci] = True
        return chunk
    def loadAllChunks(self):
        for x in range(32):
            for z in range(32):
                self.loadChunk(x,z)
    def isChunkLoaded(self,x,z): return self.loaded[_chunk_i(x,z)]
    def getChunkNBT(self,x,z): # will automatically load chunk if necessary
        ci = _chunk_i(x,z)
        if not self.loaded[ci]: self.loadChunk(x,z)
        return self.chunks[ci]
    def encodeMCA(self):
        # header, need to generate location data for chunks
        mca = [0]*0x1000 + sum([list(struct.pack('>i',self.timestamps[ci]))
                              for ci in range(0x400)],[])
        assert len(mca) == 0x2000
        for ci in range(0x400): # append chunks in order
            coords = (ci%32,ci//32)
            chunknbt = self.getChunkNBT(coords[0],coords[1])
            if chunknbt == None: continue # skip empty chunks
            chunkbin = zlib.compress(chunknbt.encodeTag())
            length = len(chunkbin)+1 # extra byte for compression type
            bytesalloc = 5+len(chunkbin) # space to reserve in mca file
            if bytesalloc % 0x1000 != 0: # round up to 4KiB multiple
                bytesalloc += 0x1000 - (bytesalloc % 0x1000)
            assert bytesalloc % 0x1000 == 0
            offset = len(mca) // 0x1000 # start at end of data so far
            sectors = bytesalloc // 0x1000
            if offset >= 2**24: raise MCAError('chunk offset too large')
            if sectors >= 256: raise MCAError('chunk (%d,%d) too large'%coords)
            # store location info in header
            mca[4*ci:4*ci+4] = list(struct.pack('>i',offset)[1:]) + [sectors]
            # use code 2 compression (zlib)
            chunkbin = struct.pack('>i',length) + b'\x02' + chunkbin
            chunkbin += b'\x00'*(bytesalloc-len(chunkbin))
            assert len(chunkbin) == bytesalloc
            mca += chunkbin # chunkbin implicitly gets converted to a list
            assert len(mca) % 0x1000 == 0
        return bytes(mca)
    def writeFile(self,file):
        fileout = open(file,'wb')
        fileout.write(self.encodeMCA())
        fileout.close()
    def repack(filein,fileout): # compact a mca file by removing empty space
        data = RegionFile(filein)
        # copy timestamps, locations will get rewritten
        mca = [0]*0x1000 + list(data.mca[0x1000:0x2000])
        assert len(mca) == 0x2000
        for ci in range(0x400):
            coords = (ci%32,ci//32)
            offset = struct.unpack('>i',b'\x00'+data.mca[4*ci:4*ci+3])[0]
            sectors = struct.unpack('>B',data.mca[4*ci+3:4*ci+4])[0]
            if offset == 0 and sectors == 00: continue # chunk not present
            chunk = data.mca[0x1000*offset:0x1000*(offset+sectors)]
            # store new location data
            newoffset = len(mca) // 0x1000
            mca[4*ci:4*ci+4] = list(struct.pack('>i',newoffset)[1:]) + [sectors]
            mca += chunk
            assert len(mca) % 0x1000 == 0
        fileout = open(fileout,'wb')
        fileout.write(bytes(mca))
        fileout.close()
