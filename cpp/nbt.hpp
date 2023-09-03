/*
NBT format as used in Minecraft - C++ library by TKoz

Everything is in the nbt:: namespace. Names starting with an underscare are not
meant to be used by client code. The library is provided as a single header file
because the NBT format is simple and precompiling this is not really saving any
time.

TODO
- make this library work on big endian systems
- add links to documentation used
*/

#pragma once

#include <cassert>
#include <cstdint>
#include <cstring>
#include <sstream>
#include <streambuf>
#include <string>
#include <unordered_map>
#include <vector>

// my own custom header for checking system endian
// nbt stores data in big endian because java stores data in big endian
// this code is most likely to be used on x86 which is little endian
#include "endian.hpp"

// TODO add support for big endian systems
// for now just make sure the system is little endian
// and warn the user if it is not
static_assert(TKOZ_LITTLE_ENDIAN);

// keep everything inside its own namespace, the string "nbt" is short
// people can put "using namespace nbt;" in their code if they want
namespace nbt
{

// forward declarations for classes
// some libraries make TAG_End its own class, my library uses nullptr for it
class TAG;
class TAG_Byte;
class TAG_Short;
class TAG_Int;
class TAG_Long;
class TAG_Float;
class TAG_Double;
class TAG_Byte_Array;
class TAG_String;
class TAG_List;
class TAG_Compound;
class TAG_Int_Array;
class TAG_Long_Array;

// type used for binary file data
typedef std::vector<char> bytes_t;

// typedefs for some nbt data types
typedef std::vector<int8_t> byte_array_t;
typedef std::vector<int16_t> short_array_t;
typedef std::vector<int32_t> int_array_t;
typedef std::vector<int64_t> long_array_t;
typedef std::vector<TAG*> list_t;
typedef std::unordered_map<std::string,TAG*> compound_t;

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

// way to get tag id from type
// TAG_End is 0 but does not have its own class in this library
template <typename T> struct tagid {};
template <> struct tagid<TAG_Byte> { static const int8_t value = 1; };
template <> struct tagid<TAG_Short> { static const int8_t value = 2; };
template <> struct tagid<TAG_Int> { static const int8_t value = 3; };
template <> struct tagid<TAG_Long> { static const int8_t value = 4; };
template <> struct tagid<TAG_Float> { static const int8_t value = 5; };
template <> struct tagid<TAG_Double> { static const int8_t value = 6; };
template <> struct tagid<TAG_Byte_Array> { static const int8_t value = 7; };
template <> struct tagid<TAG_String> { static const int8_t value = 8; };
template <> struct tagid<TAG_List> { static const int8_t value = 9; };
template <> struct tagid<TAG_Compound> { static const int8_t value = 10; };
template <> struct tagid<TAG_Int_Array> { static const int8_t value = 11; };
template <> struct tagid<TAG_Long_Array> { static const int8_t value = 12; };

// abstract base class for NBT tags
class TAG
{
    // friend declarations so they can use the protected print with depth
    // subclasses can use the protected constructor but not the functions?
    friend class TAG_List;
    friend class TAG_Compound;
private:
    const std::string name;
    TAG(){}
    // decode NBT tag using bytes in [ptr,end)
    // move ptr to 1 byte past the end of what is decoded
    static TAG *decodeTag(const char *&ptr, const char *end);
    // decode NBT tag payload in [ptr,end)
    // move ptr to 1 byte past the end of what is decoded
    static TAG *decodePayload(const char *&ptr, const char *end, int8_t tid,
            const std::string &name);
protected:
    // construct common part to all tags (the name)
    // (except TAG_End which is handled with nullptr in this library)
    TAG(const std::string &s): name(s)
    {
        if (s.size() >= 0x10000) 
            throw "nbt tag name cannot be longer than 65535 bytes";
    }
    // string name for the tag type (used in printing)
    virtual std::string _type() const = 0;
    // tag name part for printing output
    virtual std::string _namestr() const final
    {
        // TODO FIXME escape special characters
        return _type() + "('" + name + "')";
    }
    // print the value part (depends on tag type)
    virtual std::string printValue(size_t depth, size_t space) const = 0;
    // output readable format based on Notch's specification
    virtual std::string printTag(size_t depth, size_t space) const final
    {
        return std::string(space*depth,' ') + _namestr() + ": "
            + printValue(depth,space);
    }
public:
    // custom destructors not used but this is required for abstract base class
    virtual ~TAG(){}
    // the tag name
    virtual const std::string &getName() const final { return name; }
    // tag ID
    virtual int8_t id() const = 0;
    // length of payload bytes
    virtual size_t payloadSize() const = 0;
    // length of full tag in NBT
    virtual size_t nbtSize() const final
    { return 3 + name.size() + payloadSize(); }
    // write payload bytes (must have space for payloadSize() bytes)
    virtual void writePayload(char *p) const = 0;
    // write the full tag bytes (must have space for nbtSize() bytes)
    virtual void writeNbt(char *p) const final
    {
        // type byte, name length, name, payload
        _to_bytes(p,id());
        _to_bytes(p+1,(int64_t)(name.size()));
        memcpy(p+3,name.data(),name.size());
        writePayload(p+3+name.size());
    }
    // convert to a binary bytes object (for saving as file)
    virtual bytes_t encode() const final
    {
        bytes_t ret;
        ret.resize(nbtSize());
        writeNbt(ret.data());
        return ret;
    }
    // create a human readable representation of the NBT data
    virtual std::string printTag(size_t space = 4) const final
    { return printTag(0,space); }
    // decode NBT data from bytes object
    static TAG *decode(const bytes_t &data);
    // decode NBT data from C array
    static TAG *decode(const char *data, size_t len);
};

// tag for 1 byte integer
class TAG_Byte: public TAG
{
    friend class TAG;
private:
    int8_t value;
    static TAG_Byte *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+1 > end)
            throw "nbt parsing tag_byte, not enough data";
        int8_t value = _from_bytes_byte(ptr);
        ptr += 1;
        return new TAG_Byte(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Byte"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        return std::to_string(value);
    }
public:
    TAG_Byte(const std::string &s, int8_t v): TAG(s), value(v) {}
    int8_t id() const override { return 1; }
    size_t payloadSize() const override { return 1; }
    void writePayload(char *p) const override
    {
        _to_bytes(p,value);
    }
};

// tag for 2 byte integer
class TAG_Short: public TAG
{
    friend class TAG;
private:
    int16_t value;
    static TAG_Short *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+2 > end)
            throw "nbt parsing tag_short, not enough data";
        int16_t value = _from_bytes_short(ptr);
        ptr += 2;
        return new TAG_Short(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Short"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        return std::to_string(value);
    }
public:
    TAG_Short(const std::string &s, int16_t v): TAG(s), value(v) {}
    int8_t id() const override { return 2; }
    size_t payloadSize() const override { return 2; }
    void writePayload(char *p) const override
    {
        _to_bytes(p,value);
    }
};

// tag for 4 byte integer
class TAG_Int: public TAG
{
    friend class TAG;
private:
    int32_t value;
    static TAG_Int *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+4 > end)
            throw "nbt parsing tag_int, not enough data";
        int32_t value = _from_bytes_int(ptr);
        ptr += 4;
        return new TAG_Int(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Int"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        return std::to_string(value);
    }
public:
    TAG_Int(const std::string &s, int32_t v): TAG(s), value(v) {}
    int8_t id() const override { return 3; }
    size_t payloadSize() const override { return 4; }
    void writePayload(char *p) const override
    {
        _to_bytes(p,value);
    }
};

// tag for 8 byte integer
class TAG_Long: public TAG
{
    friend class TAG;
private:
    int64_t value;
    static TAG_Long *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+8 > end)
            throw "nbt parsing tag_long, not enough data";
        int64_t value = _from_bytes_long(ptr);
        ptr += 8;
        return new TAG_Long(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Long"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        return std::to_string(value);
    }
public:
    TAG_Long(const std::string &s, int64_t v): TAG(s), value(v) {}
    int8_t id() const override { return 4; }
    size_t payloadSize() const override { return 8; }
    void writePayload(char *p) const override
    {
        _to_bytes(p,value);
    }
};

// tag for 4 byte float
class TAG_Float: public TAG
{
    friend class TAG;
private:
    float value;
    static TAG_Float *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+4 > end)
            throw "nbt parsing tag_float, not enough data";
        float value = _from_bytes_float(ptr);
        ptr += 4;
        return new TAG_Float(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Float"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        // TODO FIXME std::to_string uses a bad format for floating point
        return std::to_string(value);
    }
public:
    TAG_Float(const std::string &s, float v): TAG(s), value(v) {}
    int8_t id() const override { return 5; }
    size_t payloadSize() const override { return 4; }
    void writePayload(char *p) const override
    {
        _to_bytes(p,value);
    }
};

// tag for 8 byte float
class TAG_Double: public TAG
{
    friend class TAG;
private:
    double value;
    static TAG_Double *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+8 > end)
            throw "nbt parsing tag_double, not enough data";
        double value = _from_bytes_double(ptr);
        ptr += 8;
        return new TAG_Double(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Double"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        // TODO FIXME std::to_string uses a bad format for floating point
        return std::to_string(value);
    }
public:
    TAG_Double(const std::string &s, double v): TAG(s), value(v) {}
    int8_t id() const override { return 6; }
    size_t payloadSize() const override { return 8; }
    void writePayload(char *p) const override
    {
        _to_bytes(p,value);
    }
};

// tag for array of 1 byte integers
class TAG_Byte_Array: public TAG
{
    friend class TAG;
private:
    byte_array_t value;
    static TAG_Byte_Array *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+4 > end)
            throw "nbt parsing tag_byte_array, cannot parse length";
        size_t len = (uint32_t)_from_bytes_int(ptr);
        ptr += 4;
        if (ptr+len > end)
            throw "nbt parsing tag_byte_array, not enough data";
        byte_array_t value;
        value.resize(len);
        for (size_t i = 0; i < len; ++i)
        {
            value[i] = _from_bytes_byte(ptr);
            ++ptr;
        }
        return new TAG_Byte_Array(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Byte_Array"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        std::string ret = "[";
        if (value.size())
            ret += std::to_string(value[0]);
        for (size_t i = 1; i < value.size(); ++i)
        {
            ret += ",";
            ret += std::to_string(value[0]);
        }
        ret += "]";
        return ret;
    }
public:
    TAG_Byte_Array(const std::string &s, const byte_array_t &v):
            TAG(s), value(v)
    {
        if (v.size() >= 0x80000000)
            throw "nbt byte array cannot be longer than 2147483647";
    }
    int8_t id() const override { return 7; }
    size_t payloadSize() const override { return 4 + value.size(); }
    void writePayload(char *p) const override
    {
        _to_bytes(p,(int32_t)(value.size()));
        p += 4;
        for (size_t i = 0; i < value.size(); ++i)
            _to_bytes(p+i,value[i]);
    }
};

// tag for string
class TAG_String: public TAG
{
    friend class TAG;
private:
    std::string value;
    static TAG_String *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+2 > end)
            throw "nbt parsing tag_string, cannot parse length";
        size_t len = (uint16_t)_from_bytes_short(ptr);
        ptr += 2;
        if (ptr+len > end)
            throw "nbt parsing tag_string, not enough data";
        std::string value(ptr,len);
        ptr += len;
        return new TAG_String(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_String"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        // TODO FIXME escape special characters
        return "'" + value + "'";
    }
public:
    TAG_String(const std::string &s, const std::string &v): TAG(s), value(v)
    {
        if (v.size() >= 0x10000)
            throw "nbt string cannot be longer than 65535 bytes";
    }
    int8_t id() const override { return 8; }
    size_t payloadSize() const override { return 2 + value.size(); }
    void writePayload(char *p) const override
    {
        _to_bytes(p,(int16_t)(value.size()));
        memcpy(p+2,value.data(),value.size());
    }
};

// tag for list of tags (all of the same type)
class TAG_List: public TAG
{
    friend class TAG;
private:
    list_t value;
    int8_t tid;
    static TAG_List *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr > end)
            throw "nbt parsing tag_list, cannot parse tag type id";
        int8_t tid = (int8_t)(*(ptr++));
        if (ptr+4 > end)
            throw "nbt parsing tag_list, cannot parse length";
        size_t len = (uint32_t)_from_bytes_int(ptr);
        ptr += 4;
        list_t value;
        value.resize(len);
        for (size_t i = 0; i < len; ++i)
            value[i] = TAG::decodePayload(ptr,end,tid,"");
        return new TAG_List(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_List"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        std::string spacestr(space*depth,' ');
        std::string ret = std::to_string(value.size()) + " entries\n";
        ret += spacestr + "{\n";
        for (size_t i = 0; i < value.size(); ++i)
            if (value[i])
                ret += value[i]->printTag(depth+1,space) + "\n";
        ret += spacestr + "}";
        return ret;
    }
public:
    TAG_List(const std::string &s, const list_t &v, int8_t tid = -1):
            TAG(s), value(v)
    {
        // tid == -1 means infer type from provided vector
        if (v.size() >= 0x80000000)
            throw "nbt list cannot be longer than 2147483647";
        if (tid == -1) // infer tag type id, use TAG_End if list is empty
            tid = v.size() ? v[0]->id() : 0;
        for (size_t i = 0; i < v.size(); ++i)
        {
            if ((!v[i] && tid != 0) || (v[i] && v[i]->id() != tid))
                throw "nbt list cannot contain mixed tag types";
            // this check could be ignored since tag names are ignored anyway
            if (v[i] && v[i]->getName() != "")
                throw "nbt list tags must be unnamed";
        }
    }
    int8_t id() const override { return 9; }
    size_t payloadSize() const override
    {
        size_t ret = 5;
        for (size_t i = 0; i < value.size(); ++i)
            if (value[i])
                ret += value[i]->payloadSize();
        return ret;
    }
    void writePayload(char *p) const override
    {
        _to_bytes(p,tid);
        _to_bytes(p+1,(int32_t)(value.size()));
        p += 5;
        for (size_t i = 0; i < value.size(); ++i)
            if (value[i])
            {
                value[i]->writePayload(p);
                p += value[i]->payloadSize();
            }
    }
};

// tag for sequence of tags (varying type)
// TODO keep track of tag order in unordered_map
// (will require writing a new data structure based on unordered_map and list)
class TAG_Compound: public TAG
{
    friend class TAG;
private:
    compound_t value;
    static TAG_Compound *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        compound_t value;
        TAG *item;
        // decode tags until finding TAG_End
        while ((item = TAG::decodeTag(ptr,end)))
        {
            const std::string &itemname = item->getName();
            auto it = value.find(itemname);
            if (it != value.end())
                throw "nbt parsing tag_compound, duplicate tag name";
            value[itemname] = item;
        }
        return new TAG_Compound(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Compound"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        std::string spacestr(space*depth,' ');
        std::string ret = std::to_string(value.size()) + " entries\n";
        ret += spacestr + "{\n";
        for (auto it = value.begin(); it != value.end(); ++it)
            ret += it->second->printTag(depth+1,space) + "\n";
        ret += spacestr + "}";
        return ret;
    }
public:
    TAG_Compound(const std::string &s, const compound_t &v): TAG(s), value(v)
    {
        for (auto it = v.begin(); it != v.end(); ++it)
            if (!it->second)
                throw "nbt compound cannot contain tag_end";
    }
    int8_t id() const override { return 10; }
    size_t payloadSize() const override
    {
        size_t ret = 1;
        for (auto it = value.begin(); it != value.end(); ++it)
            ret += it->second->nbtSize();
        return ret;
    }
    void writePayload(char *p) const override
    {
        for (auto it = value.begin(); it != value.end(); ++it)
        {
            it->second->writeNbt(p);
            p += it->second->nbtSize();
        }
        *p = '\0'; // TAG_End
    }
};

// tag for array of 4 byte integers
class TAG_Int_Array: public TAG
{
    friend class TAG;
private:
    int_array_t value;
    static TAG_Int_Array *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+4 > end)
            throw "nbt parsing tag_int_array, cannot parse length";
        size_t len = (uint32_t)_from_bytes_int(ptr);
        ptr += 4;
        if (ptr + len*4 > end)
            throw "nbt parsing tag_int_array, not enough data";
        int_array_t value;
        value.resize(len);
        for (size_t i = 0; i < len; ++i)
        {
            value[i] = _from_bytes_int(ptr);
            ptr += 4;
        }
        return new TAG_Int_Array(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Int_Array"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        std::string ret = "[";
        if (value.size())
            ret += std::to_string(value[0]);
        for (size_t i = 1; i < value.size(); ++i)
        {
            ret += ",";
            ret += std::to_string(value[0]);
        }
        ret += "]";
        return ret;
    }
public:
    TAG_Int_Array(const std::string &s, const int_array_t &v):
        TAG(s), value(v)
    {
        if (v.size() >= 0x80000000)
            throw "nbt array cannot be longer than 2147483647";
    }
    int8_t id() const override { return 11; }
    size_t payloadSize() const override { return 4 + value.size()*4; }
    void writePayload(char *p) const override
    {
        _to_bytes(p,(int32_t)(value.size()));
        p += 4;
        for (size_t i = 0; i < value.size(); ++i)
            _to_bytes(p+i*4,value[i]);
    }
};

// tag for array of 8 byte integers
class TAG_Long_Array: public TAG
{
    friend class TAG;
private:
    long_array_t value;
    static TAG_Long_Array *decodePayload(const char *&ptr, const char *end,
            const std::string &name)
    {
        if (ptr+4 > end)
            throw "nbt parsing tag_long_array, cannot parse length";
        size_t len = (uint32_t)_from_bytes_int(ptr);
        ptr += 4;
        if (ptr + len*8 > end)
            throw "nbt parsing tag_long_array, not enough data";
        long_array_t value;
        value.resize(len);
        for (size_t i = 0; i < len; ++i)
        {
            value[i] = _from_bytes_long(ptr);
            ptr += 8;
        }
        return new TAG_Long_Array(name,value);
    }
protected:
    virtual std::string _type() const override { return "TAG_Long_Array"; }
    std::string printValue(size_t depth, size_t space) const override
    {
        (void)(depth+space); // suppress unused variable warning/error
        std::string ret = "[";
        if (value.size())
            ret += std::to_string(value[0]);
        for (size_t i = 1; i < value.size(); ++i)
        {
            ret += ",";
            ret += std::to_string(value[0]);
        }
        ret += "]";
        return ret;
    }
public:
    TAG_Long_Array(const std::string &s, const long_array_t &v):
            TAG(s), value(v)
    {
        if (v.size() >= 0x80000000)
            throw "nbt array cannot be longer than 2147483647";
    }
    int8_t id() const override { return 12; }
    size_t payloadSize() const override { return 4 + value.size()*8; }
    void writePayload(char *p) const override
    {
        _to_bytes(p,(int32_t)(value.size()));
        p += 4;
        for (size_t i = 0; i < value.size(); ++i)
            _to_bytes(p+i*8,value[i]);
    }
};

// currently unused
class _icharbuf : private std::streambuf
{
    _icharbuf(const char *beg, const char *end)
    {
        // have to cast to char* for streambuf, use read only functions
        char *b = const_cast<char*>(beg);
        char *e = const_cast<char*>(end);
        setg(b,b,e);
    }
    int next() { return sbumpc(); }
};

TAG *TAG::decodePayload(const char *&ptr, const char *end, int8_t tid,
        const std::string &name)
{
    switch (tid)
    {
    case 0: // TAG_End
        return nullptr;
    case 1: // TAG_Byte
        return TAG_Byte::decodePayload(ptr,end,name);
    case 2: // TAG_Short
        return TAG_Short::decodePayload(ptr,end,name);
    case 3: // TAG_Int
        return TAG_Int::decodePayload(ptr,end,name);
    case 4: // TAG_Long
        return TAG_Long::decodePayload(ptr,end,name);
    case 5: // TAG_Float
        return TAG_Float::decodePayload(ptr,end,name);
    case 6: // TAG_Double
        return TAG_Double::decodePayload(ptr,end,name);
    case 7: // TAG_Byte_Array
        return TAG_Byte_Array::decodePayload(ptr,end,name);
    case 8: // TAG_String
        return TAG_String::decodePayload(ptr,end,name);
    case 9: // TAG_List
        return TAG_List::decodePayload(ptr,end,name);
    case 10: // TAG_Compound
        return TAG_Compound::decodePayload(ptr,end,name);
    case 11: // TAG_Int_Array
        return TAG_Int_Array::decodePayload(ptr,end,name);
    case 12: // TAG_Long_Array
        return TAG_Long_Array::decodePayload(ptr,end,name);
    default:
        throw "nbt parsing payload, invalid tag type id";
    }
}

TAG *TAG::decodeTag(const char *&ptr, const char *end)
{
    if (ptr == end)
        throw "nbt parsing cannot decode tag from empty data";
    int8_t id = (int8_t)(*(ptr++));
    if (id == 0) // TAG_End
        return nullptr;
    if (ptr+2 > end)
        throw "nbt parsing cannot decode tag name length";
    size_t len = (uint16_t)_from_bytes_short(ptr);
    ptr += 2;
    if (ptr+len > end)
        throw "nbt parsing cannot decode tag name string";
    std::string name(ptr,len);
    ptr += len;
    return decodePayload(ptr,end,id,name);
}

TAG *TAG::decode(const bytes_t &data)
{
    return decode(data.data(),data.size());
}

TAG *TAG::decode(const char *data, size_t len)
{
    const char *ptr = data;
    const char *end = data+len;
    TAG *ret = decodeTag(ptr,end);
    if (ptr != end)
    {
        delete ret;
        throw "nbt parsing terminated with extra data at end";
    }
    return ret;
}

}
