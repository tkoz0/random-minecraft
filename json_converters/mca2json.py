import json,gzip,sys,struct,zlib
from nbt2json import nbt2json

def mca2json(mca):
    header = mca[:8192]
    # chunks are represented by {"timestamp":timestamp,"chunk":<chunk_obj>}
    chunks = [] # export as list
    for ci in range(1024):
        offset = struct.unpack('>i',b'\x00'+header[4*ci:4*ci+3])[0]
        if offset == 0: continue # chunk not present
        sectors = struct.unpack('>b',header[4*ci+3:4*ci+4])[0]
        timestamp = struct.unpack('>i',header[4096+4*ci:4096+4*ci+4])[0]
        start = 4096*offset
        length = struct.unpack('>i',mca[start:start+4])[0]
        compression_type = struct.unpack('>b',mca[start+4:start+5])[0]
        chunk_compressed_nbt = mca[start+5:start+4+length]
        if compression_type == 1: # unused
            chunk_nbt = gzip.decompress(chunk_compressed_nbt)
        elif compression_type == 2: # zlib
            chunk_nbt = zlib.decompress(chunk_compressed_nbt)
        else: assert 0
        chunk = nbt2json(chunk_nbt)[''] # content inside the root compound tag
        chunks.append(chunk)
    return chunks

if __name__ == '__main__':

    mca = open(sys.argv[1],'rb').read()

    print(json.dumps(mca2json(mca),indent=4))
