import json,gzip,sys,struct

# extracts l bytes starting at nbt[i], returns (bytes,i+l)
def take_bytes(nbt,i,l):
    return (nbt[i:i+l],i+l)

# returns (obj,last_index+1) so caller can continue from end
# obj = {"tag_name":<tag_value>}
# value is int/number/list where it makes sense, dict for compound
# payload_only is used for lists, reads a nameless tag of type
def make_obj(nbt,i,payload_only=None):
    j = i
    if payload_only == None: # read header
        id,j = take_bytes(nbt,j,1)
        id = id[0]
        if id == 0: return (None,j)
        l,j = take_bytes(nbt,j,2) # name length
        l = struct.unpack('>H',l)[0]
        s,j = take_bytes(nbt,j,l)
        s = s.decode()
    else: id = payload_only # read payload only for tag type
    if id == 1: # byte
        v,j = take_bytes(nbt,j,1)
        v = struct.unpack('>b',v)[0]
    elif id == 2: # short
        v,j = take_bytes(nbt,j,2)
        v = struct.unpack('>h',v)[0]
    elif id == 3: # int
        v,j = take_bytes(nbt,j,4)
        v = struct.unpack('>i',v)[0]
    elif id == 4: # long
        v,j = take_bytes(nbt,j,8)
        v = struct.unpack('>q',v)[0]
    elif id == 5: # float
        v,j = take_bytes(nbt,j,4)
        v = struct.unpack('>f',v)[0]
    elif id == 6: # double
        v,j = take_bytes(nbt,j,8)
        v = struct.unpack('>d',v)[0]
    elif id == 7: # byte array
        l,j = take_bytes(nbt,j,4) # length
        l = struct.unpack('>i',l)[0]
        v,j = take_bytes(nbt,j,l)
        v = struct.unpack('>'+'b'*l,v)
    elif id == 8: # string
        l,j = take_bytes(nbt,j,2) # length
        l = struct.unpack('>H',l)[0]
        v,j = take_bytes(nbt,j,l)
        v = v.decode()
    elif id == 9: # list
        tid,j = take_bytes(nbt,j,1) # tag type
        tid = tid[0]
        l,j = take_bytes(nbt,j,4) # length
        l = struct.unpack('>i',l)[0]
        v = []
        for _ in range(l):
            t,j = make_obj(nbt,j,tid)
            v.append(t)
    elif id == 10: # compound
        comp = dict()
        while True:
            t,j = make_obj(nbt,j)
            if t == None: # tag end
                break
            k = list(t.keys())[0]
            v = t[k]
            assert not (k in comp)
            comp[k] = v
        v = comp
    elif id == 11: # int array
        l,j = take_bytes(nbt,j,4) # length
        l = struct.unpack('>i',l)[0]
        v,j = take_bytes(nbt,j,4*l)
        v = struct.unpack('>'+'i'*l,v)
    elif id == 12: # long array
        l,j = take_bytes(nbt,j,4) # length
        l = struct.unpack('>i',l)[0]
        v,j = take_bytes(nbt,j,8*l)
        v = struct.unpack('>'+'q'*l,v)
    else: assert 0 # unknown tag id
    return (v,j) if payload_only != None else ({s:v},j)

def nbt2json(nbt):
    return make_obj(nbt,0)[0]

if __name__ == '__main__':

    nbt = gzip.decompress(open(sys.argv[1],'rb').read())

    obj = nbt2json(nbt)

    print(json.dumps(obj,indent=4))
