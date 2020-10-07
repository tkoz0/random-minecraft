'''
Implementation of the NBT (named binary tag) format. Each type of tag has a
value. For compatibility with Java, all integer types are signed and all numeric
types are encoded in big endian. Tags are initialized with a name and value. The
not as intuitive value types are TAG_List using (type,list_of_values) and
TAG_Compound using dict that maps tag name to tag value (with the same name).
'''

import gzip
import json
import struct

# this is a base class, should never be instantiated
class NBTTag:
    ID = -1
    def __init__(self,name): # subclass should also initialize self.value
        self.name = name
    def __eq__(self,other):
        return type(self) == type(other) and self.name == other.name \
            and self.value == other.value
    # below functions should be overridden when needed
    def encodeValue(self): assert 0 # to byte string
    def valueValid(value): assert 0 # is value allowed for the tag
    def __str__(self): return self._namestr_() + ': ' + str(self.value)
    # this function may need to be overridden
    def setValue(self,value):
        if not type(self).valueValid(value): raise ValueError()
        self.value = value
    def __len__(self): return len(self.value)
    def __iter__(self): return iter(self.value)
    # below functions should not be overridden
    def _namestr_(self):
        return type(self).__name__ + '(' + json.dumps(self.name) + ')'
    def getValue(self): return self.value
    # making self.name immutable for safety
    #def setName(self,name):
    #    if type(name) != str: raise TypeError('name not a string')
    #    self.name = name
    def getName(self): return self.name
    def encodeTag(self):
        return bytes([type(self).ID]) + TAG_String('',self.name).encodeValue() \
            + self.encodeValue()
    def __repr__(self): return self.__str__()
    def writeFile(self,file):
        fileout = open(file,'wb')
        fileout.write(gzip.compress(self.encodeTag()))
        fileout.close()

# used to mark the end of compound named tag lists
# this should never explicitly be used in nbt data structures
class TAG_End(NBTTag):
    ID = 0
    def __init__(self): super().__init__('')
    def __eq__(self,_): return True # all end tags are identical
    def encodeTag(self): return b'\x00'
    def encodeValue(self): return b''
    def valueValid(v): return True
    def __str__(self): return type(self).__name__

class TAG_Byte(NBTTag):
    ID = 1
    def __init__(self,name,value=0):
        super().__init__(name)
        self.setValue(value)
    def encodeValue(self): return struct.pack('>b',self.value)
    def valueValid(v): return type(v) == int and -2**7 <= v < 2**7

class TAG_Short(NBTTag):
    ID = 2
    def __init__(self,name,value=0):
        super().__init__(name)
        self.setValue(value)
    def encodeValue(self): return struct.pack('>h',self.value)
    def valueValid(v): return type(v) == int and -2**15 <= v < 2**15

class TAG_Int(NBTTag):
    ID = 3
    def __init__(self,name,value=0):
        super().__init__(name)
        self.setValue(value)
    def encodeValue(self): return struct.pack('>i',self.value)
    def valueValid(v): return type(v) == int and -2**31 <= v < 2**31

class TAG_Long(NBTTag):
    ID = 4
    def __init__(self,name,value=0):
        super().__init__(name)
        self.setValue(value)
    def encodeValue(self): return struct.pack('>q',self.value)
    def valueValid(v): return type(v) == int and -2**63 <= v < 2**63

class TAG_Float(NBTTag):
    ID = 5
    def __init__(self,name,value=0.0):
        super().__init__(name)
        self.setValue(value)
    def encodeValue(self): return struct.pack('>f',self.value)
    def valueValid(v): return type(v) == float

class TAG_Double(NBTTag):
    ID = 6
    def __init__(self,name,value=0.0):
        super().__init__(name)
        self.setValue(value)
    def encodeValue(self): return struct.pack('>d',self.value)
    def valueValid(v): return type(v) == float

class TAG_Byte_Array(NBTTag):
    ID = 7
    def __init__(self,name,value=[]):
        super().__init__(name)
        self.setValue(value)
    def setValue(self,value):
        if not type(self).valueValid(value): raise ValueError()
        self.value = [b for b in value]
    def encodeValue(self): 
        return struct.pack('>i',len(self.value)) \
            + b''.join(map(lambda b: struct.pack('>b',b),self.value))
    def valueValid(v):
        v = [b for b in v]
        for b in v:
            if not TAG_Byte.valueValid(b): return False
        return True
    def append(self,obj):
        if not TAG_Byte.valueValid(obj): raise ValueError()
        self.value.append(obj)
    def pop(self,i=-1): return self.value.pop(i)
    def __setitem__(self,k,v):
        if not TAG_Byte.valueValid(obj): raise ValueError()
        self.value[k] = v
    def __getitem__(self,k): return self.value[k]

class TAG_String(NBTTag):
    ID = 8
    def __init__(self,name,value=''):
        super().__init__(name)
        self.setValue(value)
    def encodeValue(self):
        b = self.value.encode()
        return struct.pack('>h',len(b)) + b
    def valueValid(v): return type(v) == str
    def __str__(self): return self._namestr_() + ': ' + json.dumps(self.value)

# stores a list of values as nbt tag types, names are ignored
class TAG_List(NBTTag):
    ID = 9
    def __init__(self,name,value=(TAG_End,[])):
        super().__init__(name)
        self.setValue(value)
    def setValue(self,value):
        if not type(self).valueValid(value): raise ValueError()
        self.value = (value[0],[o for o in value[1]])
    def encodeValue(self):
        return bytes([TYPE2ID[self.value[0]]]) \
            + struct.pack('>i',len(self.value[1])) \
            + b''.join(self.value[0]('',o).encodeValue() for o in self.value[1])
    def valueValid(v):
        if not (type(v) == tuple and len(v) == 2): return False
        if not (v[0] in TYPE2ID): return False
        for o in v[1]:
            if not v[0].valueValid(o): return False
        return True
    def __str__(self):
        entrystrs = []
        for entry in self.value[1]:
            tag = self.value[0]('',entry)
            taglines = str(tag).splitlines()
            # remove tag name from first line
            i = taglines[0].find('(')
            assert taglines[0][i:i+4] == '("")', 'bug in __str__ implementation'
            taglines[0] = taglines[0][:i] + taglines[0][i+4:]
            entrystrs += taglines
        return self._namestr_() + ': %d entries of type %s'%(len(self.value[1]),
                                                    self.value[0].__name__) \
            + '\n{\n' + '\n'.join(' '*4+s for s in entrystrs) \
            + ('\n' if len(self.value[1]) > 0 else '') + '}'
    def append(self,obj):
        if not self.value[0].validValue(obj): raise ValueError()
        self.value.append(obj)
    def pop(self,i=-1): return self.value.pop(i)
    def __setitem__(self,k,v):
        if not self.value[0].valueValid(v): raise ValueError()
        self.value[1][k] = v
    def __getitem__(self,k): return self.value[1][k]
    def __len__(self): return len(self.value[1])
    def __iter__(self): return iter(self.value[1])

class TAG_Compound(NBTTag):
    ID = 10
    def __init__(self,name,value=dict()):
        super().__init__(name)
        self.setValue(value)
    def setValue(self,value):
        if type(value) != dict: raise ValueError()
        for k in value:
            if type(value[k]) == TAG_End: raise ValueError()
            if not (type(value[k]) in TYPE2ID): raise ValueError()
            if k != value[k].name: raise ValueError()
        self.value = value
    def encodeValue(self): # include end tag '\x00'
        return b''.join(o.encodeTag() for o in self.value.values()) + b'\x00'
    def valueValid(val): 
        if type(val) != dict: return False
        for k in val:
            v = val[k]
            if type(k) != str: return False
            if type(v) == TAG_End or not (type(v) in TYPE2ID): return False
            if k != v.getName(): return False
        return True
    def __str__(self):
        return self._namestr_() + ': %d entries'%len(self.value) \
            + '\n{\n' \
            + '\n'.join('\n'.join(' '*4+line
                                  for line in str(tag).splitlines())
                        for tag in self.value.values()) \
            + ('\n' if len(self.value) > 0 else '') + '}'
    def insert(self,v):
        if type(v) == TAG_End or not (type(v) in TYPE2ID): raise ValueError()
        self.value[v.name] = v
    def pop(self,name): return self.value.pop(name)
    def __getitem__(self,k): return self.value[k]
    def __iter__(self): return iter(self.value.values())

class TAG_Int_Array(NBTTag):
    ID = 11
    def __init__(self,name,value=[]):
        super().__init__(name)
        self.setValue(value)
    def setValue(self,value):
        if not type(self).valueValid(value): raise ValueError()
        self.value = [i for i in value]
    def encodeValue(self): 
        return struct.pack('>i',len(self.value)) \
            + b''.join(map(lambda i: struct.pack('>i',i),self.value))
    def valueValid(v):
        v = [i for i in v]
        for i in v:
            if not TAG_Int.valueValid(i): return False
        return True
    def append(self,obj):
        if not TAG_Int.valueValid(obj): raise ValueError()
        self.value.append(obj)
    def pop(self,i=-1): return self.value.pop(i)
    def __setitem__(self,k,v):
        if not TAG_Int.valueValid(v): raise ValueError()
        self.value[k] = v
    def __getitem__(self,k): return self.value[k]

class TAG_Long_Array(NBTTag):
    ID = 12
    def __init__(self,name,value=[]):
        super().__init__(name)
        self.setValue(value)
    def setValue(self,value):
        if not type(self).valueValid(value): raise ValueError()
        self.value = [l for l in value]
    def encodeValue(self): 
        return struct.pack('>i',len(self.value)) \
            + b''.join(map(lambda l: struct.pack('>q',l),self.value))
    def valueValid(v):
        v = [l for l in v]
        for l in v: 
            if not TAG_Long.valueValid(l): return False
        return True
    def append(self,obj):
        if not TAG_Long.valueValid(obj): raise ValueError()
        self.value.append(obj)
    def pop(self,i=-1): return self.value.pop(i)
    def __setitem__(self,k,v):
        if not TAG_Long.valueValid(v): raise ValueError()
        self.value[k] = v
    def __getitem__(self,k): return self.value[k]

ID2TYPE = [TAG_End,
           TAG_Byte,
           TAG_Short,
           TAG_Int,
           TAG_Long,
           TAG_Float,
           TAG_Double,
           TAG_Byte_Array,
           TAG_String,
           TAG_List,
           TAG_Compound,
           TAG_Int_Array,
           TAG_Long_Array]

TYPE2ID = {TAG_End:        0,
           TAG_Byte:       1,
           TAG_Short:      2,
           TAG_Int:        3,
           TAG_Long:       4,
           TAG_Float:      5,
           TAG_Double:     6,
           TAG_Byte_Array: 7,
           TAG_String:     8,
           TAG_List:       9,
           TAG_Compound:   10,
           TAG_Int_Array:  11,
           TAG_Long_Array: 12}

class NBTError(Exception): pass

# given a byte string, index, and tag id, decode tag value starting at index
# returns (tag_value,end_index) where end_index is 1 byte after the value bytes
# the caller (decode_named_tag()) will package the value into a tag object
def _decode_tag_value(nbt,i,tagid):
    if tagid == 0: # end tag has no payload
        return (None,i)
    if tagid == 1: # signed byte
        v = struct.unpack('>b',nbt[i:i+1])[0]
        i += 1
    elif tagid == 2: # signed short
        v = struct.unpack('>h',nbt[i:i+2])[0]
        i += 2
    elif tagid == 3: # signed int
        v = struct.unpack('>i',nbt[i:i+4])[0]
        i += 4
    elif tagid == 4: # signed long
        v = struct.unpack('>q',nbt[i:i+8])[0]
        i += 8
    elif tagid == 5: # ieee754 float
        v = struct.unpack('>f',nbt[i:i+4])[0]
        i += 4
    elif tagid == 6: # ieee754 double
        v = struct.unpack('>d',nbt[i:i+8])[0]
        i += 8
    elif tagid == 7: # byte array
        l = struct.unpack('>i',nbt[i:i+4])[0] # length
        i += 4
        v = list(struct.unpack('>'+l*'b',nbt[i:i+l]))
        i += l
    elif tagid == 8: # string
        l = struct.unpack('>h',nbt[i:i+2])[0] # length
        i += 2
        v = nbt[i:i+l].decode()
        i += l
    elif tagid == 9: # list
        listtagid = struct.unpack('>b',nbt[i:i+1])[0] # tag type
        i += 1
        l = struct.unpack('>i',nbt[i:i+4])[0] # length
        i += 4
        v = []
        for _ in range(l):
            t,i = _decode_tag_value(nbt,i,listtagid)
            v.append(t)
        v = (ID2TYPE[listtagid],v)
    elif tagid == 10: # compound
        v = dict()
        while True:
            t,i = _decode_named_tag(nbt,i)
            if t == TAG_End(): break # end tag
            if t.name in v: raise NBTError('tag name %s duplicated'%t.name)
            v[t.name] = t
    elif tagid == 11: # int array
        l = struct.unpack('>i',nbt[i:i+4])[0] # length
        i += 4
        v = list(struct.unpack('>'+l*'i',nbt[i:i+4*l]))
        i += 4*l
    elif tagid == 12: # long array
        l = struct.unpack('>i',nbt[i:i+4])[0] # length
        i += 4
        v = list(struct.unpack('>'+l*'q',nbt[i:i+8*l]))
        i += 8*l
    else: raise NBTError('invalid tag id %d'%tagid)
    return (v,i)

# given a byte string and index, decodes a named binary tag starting at index
# returns (tag_object,end_index) where end_index is 1 past the last tag byte
def _decode_named_tag(nbt,i=0):
    tagid = struct.unpack('>b',nbt[i:i+1])[0] # tag type
    i += 1
    if tagid == 0: return (TAG_End(),i)
    name,i = _decode_tag_value(nbt,i,8) # name is string payload
    value,i = _decode_tag_value(nbt,i,tagid)
    if tagid == 1: return (TAG_Byte(name,value),i)
    if tagid == 2: return (TAG_Short(name,value),i)
    if tagid == 3: return (TAG_Int(name,value),i)
    if tagid == 4: return (TAG_Long(name,value),i)
    if tagid == 5: return (TAG_Float(name,value),i)
    if tagid == 6: return (TAG_Double(name,value),i)
    if tagid == 7: return (TAG_Byte_Array(name,value),i)
    if tagid == 8: return (TAG_String(name,value),i)
    if tagid == 9:  return (TAG_List(name,value),i)
    if tagid == 10: return (TAG_Compound(name,value),i)
    if tagid == 11: return (TAG_Int_Array(name,value),i)
    if tagid == 12: return (TAG_Long_Array(name,value),i)
    raise NBTError('invalid tag id %d'%tagid)

# decodes binary nbt data
def decode_nbt(nbt): return _decode_named_tag(nbt)[0]

# loads nbt from a file, tries gzip and raw
def load_file(file):
    data = open(file,'rb').read()
    try: data = gzip.decompress(data)
    except: pass
    return decode_nbt(data)

if __name__ == '__main__':
    # brief equality test on a sample level.dat file below
    leveldat1 = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x00}VMl#I\x15.\xc7?qw\xe2\xc4\x99dW\xec\xee\x85\x1bBB#fwf\xc5\x014\x89\xed$\x93\xc5a\xac8a\xc2h\x10*\xbb\x9f\xedR\xaa\xbb\x9a\xaa\xead\rg\xc4\x05\x89\x0b\x12\x0c\xe20\\8rBH\x1c\x10\xa3= !f%$.\x1cV\\\x10\x12\x87E\x82\x0b\x12\x074|U\xdd\xed\xc4\xcb.\x96J\xee\xae~U\xef\xbd\xef\xbd\xf7\xbd\x172\x16\xb2Z\x8f[^e\xaf?\xe2IDZ$\xd3S\xcd\xf10L\xf9U\xd2\x9d\xf1dL\x8c\xb1\xd7j,<\x81\x80\x8a\x87D\xd1\x93?|\xf0\xdd\xdf\x8e\xff\xf8\xfb&kM)!\xcd\xad\xd2_\xe11\xb1\xd5\x88&<\x93\xb6\xc1Z\x1d\xa5qK\x97\x12K\xfa1+~\x15\x16\xf6\xc4d"\xc6\x90\x99\xaf\xd4\xd8\xad\\j(\xbeE}\xd2\xe9\xa9\x88\xe9ZtUs\x91\xc0\x1e\xd8\xd8\xea\xe1Kb\x84J\x9c\xb1!\xab\xdc\t\xd9ZO\xf3\xa9J\x0e\xc4tf\x03\xd6<\xe4\x96\xae\xf8\xdcTqv\x07k\x03k\x13k\x15\xcb\xed\xb5\xb0\x9aX\x01\xd6\x1aV\x03\xab\x86\xb5\x8e\xb5\x82\xb5\x85\xb5]\xe8\x0e\xb1\xda\xde\x06\xc6\xeaX\xb7*l=\xd7\xf6e!%E\x95\nk\x0f4]\n\x95\x199/\xf6\xfc}\xb5k\x17VFUgUL\xa7\xf3\xd4mU\x02\xb6>$}I\xba\xa3\x81\xa4i\xe6N^\xf2\x04\xe7y\x85\xad\x1d\xf3\xf4\x80\xb8\xcd4\x99\xcaG\x00</Qi\xb0\x9d|\xbf\xc7c>\xa5\x01.\x93j|q\xffwO\xdd\xef\xc7\r\xb6\x9d\x7f~\xc4\xb5\x83\xce\x7f4\xbb;\x1f9\xbc\xc0\x9b\xeb)\xd9\xbd\xef\xfd\xe4\x0b\xb9\xd7\xab_%\xed@\xae\xb0\xe60\xe1\xa9\x99)\x0b\xecV\x8e"@\xf7\xcb&\xab\xf9\x187\xee\xdc\xbes\xef\xf6\x9bpv\xb5\xc7\xe77\xfd\x85\x0f\x08\x98\x15\\\xe2~\x07R\xf0\x88\x9bc\x15E\x14\xc1\xd3\x16\x97R]uU\x1c;\xef+H(g\xc6\xc3\xa4\'\xccE\xe9^\x95\xbd\xf6qi\xd8#\xc9\xe7\x8c}\xfdy\xc8\xda\xdd\xccX\x15w\x941\xfb\x97\xc0\xc6\xc0\xec\xc0\xa1|\x92I\x02\xa6a\xa4\x0e\x84\xa6S1\xbe`5\xab3j\xb2Wb\xfen\xa1\x16\xf9,\x92>%S;c\xf5\xb7\xef\xdd{\xebm\x9c\x98@>\x87\xb3<\xd1\xd6\x14ec\x8az4\xca\xa6G\xc9D\xb1\xfa\x84K\x83/\xafG\xc2\xf0\x91\xa4}9\xb7\x9a\x1f\xabKB^\xda\xee\x8c\xa0\xae\x94\xd9\xe1I\xa22\xd4\xcd^t\xe9\xca\'\xf6f\x16WoDZ]\xb9\xd0,k\xbc5\xce\r\xf4\x01{\x98\xd94\xb3\xe5\xa7V\xa4\x8e\xd5\xc8\xe3\xe0\x8a\xa1\xd8\xdd\x82S\xfb\x89\x15v\xde\xd5<\x8e\xdd\x97\x957\xef6\xd9za\xe0\t\x17\x91Y\x98\xb4\x11\xa9GH\xad\x19\xf2i>\x96\x0b\xad\x9b\x91B\x08\xa5\xab\xa0\xa5\xfd-D\xfe\xaa\xe7\x0e\x1c\x9310sa\xfeZ\xa4N\x85\xa4\x9eV\xe9b\x0f\x90\x1f%F\xc5\x89\xe0\x0bw\xb0\x15\xc7\x14\t\x14\xe5\t\x19g\xfb\xc2\x96\xed\xc4\xe58\x97\'Tp\x07\x12\xae<\x17x_\xfbJ-\xbc\x0fqJ.c\xd5\xba J\x8f\x12\x17}\xa5\xe7\x8b{\x81S\x0e\xc8\x92q[\x91\xea\x8bXX\x8a\x80\xd3\xc4:\x9c\xca\x03k\xb1\x1a\x1djA\x93\x1b\xb0njOr.}\x86)\xb9\xbc}\x0b\x82\xde\x81\x13\x1e\x89\xcc\xb0\x95;\x9fG\x82\x00\x86\xeb\xf4\xbcq\xbe-\xd5t/B8\xca</?|\xca\xa44\xb6\x8e(\xcda\xee6ugYr\xb1\x10\xd86\x84\xfc\xccO\x1d@\xf3\x88_g0\xd4\r\xb8\xd5J.\xabC\xea7\x06\xa8\x0c\xd2!\xabw\x1c[\x86\xac\x19S\xac\xe0\x94q\xc5\xb4\xf9 \xd3\xb6\xe3k\xd4X\x1e\xa7\xbeLQw\x12\x00\xbaM\xed\xe80\xdc\xb3V\x8bQf\xc98\xdek6X\xad\xc3\r\xed\xde\xcdK\xb2,\xfb-\x1f-1\xbe\x8d\xc4{@\\\xa2\x82\n\xc9\xb2xK\xc97J\xc9\x8b\x04\xc9\xec\xfc@\n\x08\x18\xe0ZIq\xe6\xfe\xaf\x9e>}v\xe3\xcc+\x8b\xdb\x8b\x92\xca\xd1\xff\x04\r\xadR\x9ak8\xfbIR\xaf.I\x9d\xaal:K\x90\xce\x0b\x13\xfe\xb1,\xbe\xb3\x10\xb7\x166\x179W\xa2\xd1^\x16\xde^\x16\xfe\xbf\xd6\xae\x97\xb22CH\xd1J\x90\xbb\x99t9\x80:u-\xf1\x00)~ \xe7.\xaeU\xb61P\xdar\xd9UJF`\n\xe6[P{od\x94N]\xa9\xec\xc5\xe0\x16\x9b\xf3u\xc0GB\x82p\xd10\xd8\xba\xb8q+\xb8\xb7\x11\xf3\xf9D\xce\xf1\x14\x8a\x04\xe0\x8f2!\xa3J\x9d\x05W\\\xe6\xf6~\xe9\xc5\x8b\xf7\xc1\xf4\x90\xeb\xf8o83\xc9\xad\xa8\xb3&\x9er\xa1\xfe\x8b\xf7\xf1\xbe\xeel\xec\x95A\xf4\xcaCMc\x91RG\xa9\x8b\x00\xbd\xda\xbf\x98\xa2u\xef\x08s \xa4\xf5<\xee\xeb\xce\xbb\x1a\xb0\x96U\x1d\xc25\xa9\xcb\xda\xa8\x10nC8\xd3\t\x1f\xd3a&\x1e\xa6\x94`/\x10\xe6\xfa\xe5\x8d\x85\xc0\xc7\\\x8a\x84\x0e<U\xe5\x9d\xa8\xca\x1a\xe7\xa9\x9bQ\xf2v\xb2z\x9e\x9e*\xc0\x99\xbfmx\xbd\xfafSF\xcf2DI\x17\x8c/\xc0\xd2\x01k\x1c+\x07s\xa3\x18\x1b\xfc\xef7\xbf\xb8U\x7f\xef\xfbO>[\xbe\xd7Xpvv\xd4\xeb\x137\xf6\x87?\xfa\xf7\x17\xff\xf4\xe7\'\xdf\xa9\xb3F^\x16{\xcf\\\xc4\xb6\'JEC\xcft\xee\xba>]\x92\xdc}\xe6\xac\xad\xee\t]\xf9\x1c\x80\x7f\x98\x1cj\xc42\xaaT\xe1A9\xdf0?\xa24O`\xb4;\xe7\xa6\x8f\x95\xf7\xfe\xf2\xcf\xf9}\xf5\x99w\xbc;\xfe\xa6\xdc\x9d\xfap\xac4\xe5\x065\x9dA\xc7\xca\xd8\x1f\xfcu\xff\xec\xc3\xbfu\xbf\x1d\xb0\xea@\x19\xef\xc6s\xe5+\x9f\xed\x9e\xec\xfa\xff\xe7g\x9f\xce;6\xab\xb9^\xf9\xf2\xc3:\xab\x9e\xa7\x83\\u\xb8\xef\xfa\xef\x91\xa5\xd8\x14-y\xcd\xcd\\\xc5d\xe0\x06\x01\x98\xeb\x9c+\r\xd9)\x9c\xdd\x7fw\xc6\xd1\x9bKgs\x05M\xc7@ed\xdaC\x92 A\x8a\xdc\xedC\xa9l\xae1\xb8\xe6\xf2\\a\xcb]\xe7(\xb8\xe0(\xbf\xd9\xf0\xdc\xf75<?\xc0\\\xe5\xc8\xce_[\xf9\xd9\xab\xb0\xd0\x82Jau\xaeH\xff\xa7\x94~\xfc\xf2\xe5\xcb\x9f\x02\xe9\x19\xd7\x91\x87\n\xc9v=\x7f\xf6\xc1N\xc8\x93R\xf8\x1c\xc2\xceH\xf4A\xae\x8bnYN7(\xa2BE^\xa4\xed\xc5\xd8\xbb\xc0\x85!\x8c\xab\x97\xe5\xdb;\xbfn\xb0\x8db\xd8\xe2\x13z\xac\x12*\xa70\x0c>}\xe4\xcd\xa0(\x81\xca7\xcf~\xfe\xf7\x7f5\xd8\xd6\xd2\xe0\xe6\x14\xef\xde\xce\x0f\x04ls8\x9ea"\xc1\x94Y\xcc<9\xbd\x04\x1eh\xcf1\x9b`o{\xf7\x1b O}\xa5\xb4\x8c\x1a,\xbc\x1e\xf5\xca\x01\xef\x7fC\t\nq;\x03P\x98A\x11\xef\'\xae\xa4\xa2\xe5\xc9\x14\xd9\xd8\xcbg\x8a\xa8\xcc\xff\xff\x02\x16\x82bB8\x0c\x00\x00'
    leveldat1nbt = gzip.decompress(leveldat1)
    nbtobj = decode_nbt(leveldat1nbt)
    nbtdat = nbtobj.encodeTag()
    print(leveldat1nbt == nbtdat)
    print(nbtobj)
