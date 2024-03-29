/*
C++ implementation of (parts of) java.util.Random

Integer outputs match exactly, floating point is close but not exact. The
floating point results use java.lang.StrictMath
*/

#pragma once

#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <ctime>

// macros for optimization
#define likely(x)   __builtin_expect(!!(x),1)
#define unlikely(x) __builtin_expect(!!(x),0)

namespace mclib
{

size_t _nanotime()
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC,&t);
    return 1000000000uLL*t.tv_sec + t.tv_nsec;
}

// constants
const int64_t _mult = 0x5deece66dLL;
const int64_t _add = 0xbLL;
const size_t _ss = 48;
const int64_t _su_init = 8682522807148012L;
const int64_t _su_mult = 181783497276652981L;

class Random
{
private:
    int64_t state;
    bool has_g;
    double next_g;
    // extract next bits (up to 32)
    // uses higher bits to increase period length
    int32_t _next(size_t bits)
    {
        state = (state*_mult + _add) & ((1LL << _ss) - 1);
        return state >> (_ss - bits);
    }
    // seed uniquifier function
    static int64_t _su()
    {
        static int64_t su = _su_init;
        return su *= _su_mult;
    }
public:
    // initialize with random seed
    Random() { setSeed(); }
    // initialize with provided seed
    Random(int64_t seed) { setSeed(seed); }
    // set seed randomly
    void setSeed()
    {
        setSeed(_su() ^ _nanotime());
    }
    // set seed with provided seed
    void setSeed(int64_t seed)
    {
        state = (seed ^ _mult) & ((1LL << _ss) - 1);
        has_g = false;
    }
    // write `len` random bytes to `arr`
    void nextBytes(int8_t *arr, size_t len)
    {
        size_t mult4len = len & (-4uL);
        int32_t *ptr = (int32_t*) arr;
        int32_t *mult4end = (int32_t*) (arr + mult4len);
        while (ptr < mult4end)
            *(ptr++) = _next(32);
        int8_t *ptre = (int8_t*) mult4end;
        if (ptre < arr + len)
        {
            int32_t last_bytes = _next(32);
            while (ptre < arr + len)
            {
                *(ptre++) = (last_bytes & 0xFF);
                last_bytes >>= 8;
            }
        }
    }
    // next 32 bit integer
    int32_t nextInt() { return _next(32); }
    // random integer in [0,n)
    int32_t nextInt(int32_t n)
    {
        if (unlikely(n <= 0))
            throw "bound must be positive";
        if ((n & -n) == n)
            return (int32_t)((n * (int64_t)_next(31)) >> 31);
        int32_t bits, val;
        do
        {
            bits = _next(31);
            val = bits % n;
        }
        while (unlikely(bits - val + (n - 1) < 0));
        return val;
    }
    // next 64 bit integer
    int64_t nextLong()
    {
        int32_t hi = _next(32);
        int32_t lo = _next(32);
        return ((int64_t)hi << 32) + lo;
    }
    // next boolean
    bool nextBool() { return _next(1); }
    // next single precision float in [0,1)
    float nextFloat() { return _next(24) / (float) 0x1000000; }
    // next double precision float in [0,1)
    double nextDouble()
    {
        int32_t hi = _next(26);
        int32_t lo = _next(27);
        return (((int64_t)hi << 27) + lo) / (double) 0x20000000000000L;
    }
    // next gaussian double precision (mean 0, stdev 1)
    double nextGaussian()
    {
        if (has_g)
        {
            has_g = false;
            return next_g;
        }
        double v1, v2, s;
        do
        {
            v1 = 2.0*nextDouble() - 1.0;
            v2 = 2.0*nextDouble() - 1.0;
            s = v1*v1 + v2*v2;
        }
        while (s >= 1.0);
        // not using java.lang.StrictMath sqrt and log so results differ a bit
        double norm = sqrt(-2.0*log(s)/s);
        next_g = v2*norm;
        has_g = true;
        return v1*norm;
    }
};

}

#undef likely
#undef unlikely
