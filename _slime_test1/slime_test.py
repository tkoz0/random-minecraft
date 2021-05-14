from mclib.jrand import JavaRandom
import sys

def pyInt2Signed(a,bits):
    a %= (2**bits)
    return a if a < 2**(bits-1) else a - 2**bits

def toLong(a): return pyInt2Signed(a,64)
def toInt(a): return pyInt2Signed(a,32)
def toShort(a): return pyInt2Signed(a,16)
def toByte(a): return pyInt2Signed(a,8)

seed = toLong(int(sys.argv[1]))

for z in range(32):
    for x in range(32):
        randseed = seed
        randseed += toInt(x*x*0x4c1906)
        randseed += toInt(x*0x5ac0db)
        randseed += toInt(z*z) * 0x4307a7 # constant is a long literal in java
        randseed += toInt(z*0x5f24f)
        randseed = toLong(randseed)
        # perform the xor operation in python int representation
        if randseed < 0: randseed += 2**64
        randseed ^= 0x3ad8025f
        randseed = toLong(randseed)
        javarand = JavaRandom(randseed)
        num = javarand.nextInt(10)
        print('1' if num == 0 else '0',end='')
    print()
