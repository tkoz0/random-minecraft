'''
Some functions to make Python3 work with Java types a bit easier.
'''

def _py_int_to_signed(a,b):
    ''' converts integer a (unsigned, b bits) to signed value '''
    a %= 2**b
    return a if a < 2**(b-1) else a - 2**b

''' converts python integers to java signed integers '''
def toLong(a):  return _py_int_to_signed(a,64)
def toInt(a):   return _py_int_to_signed(a,32)
def toShort(a): return _py_int_to_signed(a,16)
def toByte(a):  return _py_int_to_signed(a,8)

def hashString(s):
    ''' computes the java string hashcode '''
    h = 0
    for c in s:
        h = (31*h + ord(c)) % 2**32
    return toInt(h)
