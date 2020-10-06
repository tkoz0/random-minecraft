'''
An implementation of java.util.Random. It is a 48 bit LCG that uses the higher
32 bits of its state for each value in the sequence.
'''

import math
import struct
import sys
import time

MULTIPLIER = 0x5DEECE66D
ADDEND = 0xB
MASK = (1<<48)-1
DOUBLE_UNIT = 1.0 / (1<<53)
SEED_UNIQUIFIER = 8682522807148012

def _initialScramble(seed):
    ''' how java creates the seed using the lower 48 bits '''
    if seed < 0: seed += 2**64 # convert to unsigned for python3 use
    assert 0 <= seed < 2**64
    return (seed ^ MULTIPLIER) & MASK
def _systemTime():
    ''' get precise time similar to java.lang.System.nanoTime() '''
    return int(time.time() * 1000000)
def _seedUniquifier():
    ''' helps make unseeded instantiations have unique seeds '''
    SEED_UNIQUIFIER = (SEED_UNIQUIFIER * 181783497276652981) & ((1<<64)-1)
    return SEED_UNIQUIFIER

class JavaRandom:
    def __init__(self,seed=None):
        if seed is None: # default constructor
            seed = _seedUniquifier() ^ _systemTime()
        self._seed = _initialScramble(seed)
        self._nextNextGaussian = None # either float type or None
    def setSeed(self,seed):
        ''' changes state as if self was constructed with the new seed '''
        self._seed = _initialScramble(seed)
        self._nextNextGaussian = None
    # random number generators
    def _next(self,bits):
        '''
        extracts bits from the next random number in the stream
        should use 0 < bits <= 32, result is singed like in java
        '''
        assert 0 < bits <= 32
        self._seed = (self._seed * MULTIPLIER + ADDEND) & MASK # advance state
        ret = self._seed >> (48 - bits) # take bits
        if ret >= 2**31: ret -= 2**32 # convert to signed
        return ret
    def nextBytes(self,bytes_arr):
        '''
        places random bytes into bytes_arr (should be a list)
        results are signed (-128..127)
        '''
        for i in range(0,len(bytes_arr),4):
            rnd = self.nextInt()
            n = min(len(bytes_arr)-i,4) # handle array not multiple of 4 bytes
            for j in range(n): # takes 8 bits at a time
                b = rnd & 0xFF
                if b >= 128: b -= 256 # convert to signed
                bytes_arr[i+j] = b
                rnd >>= 8
    def nextInt(self,bound=None):
        '''
        extract a 32 bit integer (-2**31..2**31-1)
        if bound is specified, it will be in [0,bound)
        '''
        if bound is None: return self._next(32)
        assert 0 < bound < 2**31
        r = self._next(31)
        m = bound - 1
        # use random bits directly for a power of 2
        # LCGs have shorter periods in lower order bits so by using this to get
        # the higher order bits, the randomness is improved
        if (bound & m) == 0:
            return (bound * r) >> 31
        # generate values skipping those that are too high
        # the returned value is computed modulo the bound
        # list the ranges 0..bound-1, bound..2*bound-1, ..., remain < 2**31
        # let [k*bound,(k+1)*bound) be the first range with (k+1)*bound > 2**31
        # for uniform distribution, we cannot use an incomplete range, so we
        # must not go past the maximum value returned by _next(31)
        # below, u - r = the start of the range being used to extract a number
        # if adding m=bound-1 causes java integer overflow, or in python it
        # exceeds the max value from _next(31), reject it, range is incomplete
        # this allows the maximum number of complete ranges to be used
        u = r
        r = u % bound
        while u - r + m >= 2**31: # java integer overflow
            u = self._next(31)
            r = u % bound
        return r
    def nextLong(self):
        ''' extracts a 64 bit integer (-2**63..2**63-1) '''
        return (self._next(32) << 32) + self._next(32)
    def nextBoolean(self):
        ''' extracts a boolean true/false value '''
        return self._next(1) != 0
    def nextFloat(self):
        '''
        extracts a single precision float value [0,1)
        in python3 it will be double precision with extra precision
        '''
        return self._next(24) / float(1<<24)
    def nextDouble(self):
        ''' extracts a double precision float value [0,1) '''
        return ((self._next(26) << 27) + self._next(27)) / float(1<<53)
    def nextGaussian(self):
        '''
        returns a gaussian distributed value as a double precision float
        mean is 0.0 and standard deviation is 1.0
        '''
        if self._nextNextGaussian is None:
            # generate a pair with the Marsaglia polar method
            # finds a uniform random point in the unit circle by using the
            # uniform doubles to get uniform points in the [-1,1]x[-1,1] square
            s = 0.0
            while s >= 1.0 or s == 0.0: # random point (x,y) in the unit circle
                x = 2.0 * self.nextDouble() - 1.0
                y = 2.0 * self.nextDouble() - 1.0
                s = x*x + y*y # vector magnitude < 1 for inside unit circle
            # x/sqrt(s) and y/sqrt(s) are the cosine and sine of vector angles
            # TODO incomplete explanation of Marsaglia polar method
            multiplier = math.sqrt(-2.0 * math.log(s) / s)
            self._nextNextGaussian = y * multiplier
            return x * multiplier
        else:
            ret = self._nextNextGaussian
            self._nextNextGaussian = None
            return ret

# java_random.py <output_file> <function_calls> <seed> <function> [param]
if __name__ == '__main__':
    if len(sys.argv) == 5:
        outf,calls,seed,func = sys.argv[1:]
        param = None
    elif len(sys.argv) == 6:
        outf,calls,seed,func,param = sys.argv[1:]
        param = int(param)
    else: assert 0
    calls = int(calls)
    seed = int(seed)
    # output file, use stdout if specified as -
    if outf == '-':
        outf = sys.stdout.buffer
    else:
        outf = open(outf,'wb')
    jrand = JavaRandom(seed)
    # generate random numbers and write as binary data
    # for compatibility with java, using big endian
    if func == 'nextBytes':
        numbytes = int(param)
        byte_arr = [None]*numbytes
        for _ in range(calls):
            jrand.nextBytes(byte_arr)
            outf.write(b''.join(struct.pack('>b',b) for b in byte_arr))
    elif func == 'nextInt':
        if param is not None:
            param = int(param)
        for _ in range(calls):
            outf.write(struct.pack('>i',jrand.nextInt(param)))
    elif func == 'nextLong':
        for _ in range(calls):
            outf.write(struct.pack('>q',jrand.nextLong()))
    elif func == 'nextBoolean':
        for _ in range(calls):
            b = 1 if jrand.nextBoolean() else 0
            outf.write(struct.pack('>b',b))
    elif func == 'nextFloat':
        for _ in range(calls):
            outf.write(struct.pack('>f',jrand.nextFloat()))
    elif func == 'nextDouble':
        for _ in range(calls):
            outf.write(struct.pack('>d',jrand.nextDouble()))
    elif func == 'nextGaussian':
        for _ in range(calls):
            outf.write(struct.pack('>d',jrand.nextGaussian()))
    else: assert 0
    outf.flush()
    outf.close()
