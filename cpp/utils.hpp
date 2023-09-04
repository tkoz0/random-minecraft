#pragma once

#include <cstdint>

#include "endian.hpp"

static_assert(TKOZ_LITTLE_ENDIAN);

namespace mclib
{

// helper functions to read/write big endian data
// TODO support big endian, currently only supports little endian systems

// write 1 byte integer
static inline void _to_bytes(char *p, int8_t n)
{
    *p = (char)n;
}

// write 2 byte integer
static inline void _to_bytes(char *p, int16_t n)
{
    p[0] = (char)(n >> 8);
    p[1] = (char)(n >> 0);
}

// write 4 byte integer
static inline void _to_bytes(char *p, int32_t n)
{
    p[0] = (char)(n >> 24);
    p[1] = (char)(n >> 16);
    p[2] = (char)(n >> 8);
    p[3] = (char)(n >> 0);
}

// write 8 byte integer
static inline void _to_bytes(char *p, int64_t n)
{
    p[0] = (char)(n >> 56);
    p[1] = (char)(n >> 48);
    p[2] = (char)(n >> 40);
    p[3] = (char)(n >> 32);
    p[4] = (char)(n >> 24);
    p[5] = (char)(n >> 16);
    p[6] = (char)(n >> 8);
    p[7] = (char)(n >> 0);
}

// write single precision float
static inline void _to_bytes(char *p, float n)
{
    char *q = (char*)(&n);
    p[0] = q[3];
    p[1] = q[2];
    p[2] = q[1];
    p[3] = q[0];
}

// write double precision float
static inline void _to_bytes(char *p, double n)
{
    char *q = (char*)(&n);
    p[0] = q[7];
    p[1] = q[6];
    p[2] = q[5];
    p[3] = q[4];
    p[4] = q[3];
    p[5] = q[2];
    p[6] = q[1];
    p[7] = q[0];
}

// read 1 byte integer
static inline int8_t _from_bytes_byte(const char *p)
{
    return (int8_t)(*p);
}

// read 2 byte integer
static inline int16_t _from_bytes_short(const char *p)
{
    char q[2];
    q[0] = p[1];
    q[1] = p[0];
    return *((int16_t*)q);
}

// read 4 byte integer
static inline int32_t _from_bytes_int(const char *p)
{
    char q[4];
    q[0] = p[3];
    q[1] = p[2];
    q[2] = p[1];
    q[3] = p[0];
    return *((int32_t*)q);
}

// read 8 byte integer
static inline int64_t _from_bytes_long(const char *p)
{
    char q[8];
    q[0] = p[7];
    q[1] = p[6];
    q[2] = p[5];
    q[3] = p[4];
    q[4] = p[3];
    q[5] = p[2];
    q[6] = p[1];
    q[7] = p[0];
    return *((int64_t*)q);
}

// read single precision float
static inline float _from_bytes_float(const char *p)
{
    char q[4];
    q[0] = p[3];
    q[1] = p[2];
    q[2] = p[1];
    q[3] = p[0];
    return *((float*)q);
}

// read double precision float
static inline double _from_bytes_double(const char *p)
{
    char q[8];
    q[0] = p[7];
    q[1] = p[6];
    q[2] = p[5];
    q[3] = p[4];
    q[4] = p[3];
    q[5] = p[2];
    q[6] = p[1];
    q[7] = p[0];
    return *((double*)q);
}

}