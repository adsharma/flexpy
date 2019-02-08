# Flexbuffer decoder in python

import struct

#
# Some constants from flexbuffer.h
#
# These are used in the lower 2 bits of a type field to determine the size of
# the elements (and or size field) of the item pointed to (e.g. vector).
class BitWidth:
  BIT_WIDTH_8 = 0
  BIT_WIDTH_16 = 1
  BIT_WIDTH_32 = 2
  BIT_WIDTH_64 = 3

# These are used as the upper 6 bits of a type field to indicate the actual
# type.
class FlexBufferType:
  FBT_NULL = 0
  FBT_INT = 1
  FBT_UINT = 2
  FBT_FLOAT = 3
  # Types above stored inline, types below store an offset.
  FBT_KEY = 4
  FBT_STRING = 5
  FBT_INDIRECT_INT = 6
  FBT_INDIRECT_UINT = 7
  FBT_INDIRECT_FLOAT = 8
  FBT_MAP = 9
  FBT_VECTOR = 10,      # Untyped.
  FBT_VECTOR_INT = 11,  # Typed any size (stores no type table).
  FBT_VECTOR_UINT = 12
  FBT_VECTOR_FLOAT = 13
  FBT_VECTOR_KEY = 14
  FBT_VECTOR_STRING = 15
  FBT_VECTOR_INT2 = 16,  # Typed tuple (no type table, no size field).
  FBT_VECTOR_UINT2 = 17
  FBT_VECTOR_FLOAT2 = 18
  FBT_VECTOR_INT3 = 19,  # Typed triple (no type table, no size field).
  FBT_VECTOR_UINT3 = 20
  FBT_VECTOR_FLOAT3 = 21
  FBT_VECTOR_INT4 = 22,  # Typed quad (no type table, no size field).
  FBT_VECTOR_UINT4 = 23
  FBT_VECTOR_FLOAT4 = 24
  FBT_BLOB = 25
  FBT_BOOL = 26
  FBT_VECTOR_BOOL = 36,  # To Allow the same type of conversion of type to vector type

def decode_type(buf, t: FlexBufferType):
    bit_width = t & 0x3
    t = t >> 2
    if t == FlexBufferType.FBT_NULL:
        return b'0'
    if t == FlexBufferType.FBT_BOOL:
        return struct.unpack(f'<B', buf)[0]
    if t == FlexBufferType.FBT_INT:
        fmt_char = ['b', 'h', 'i', 'l'][bit_width]
        return struct.unpack(f'<{fmt_char}', buf)[0]
    if t == FlexBufferType.FBT_UINT:
        fmt_char = ['B', 'H', 'I', 'L'][bit_width]
        return struct.unpack(f'<{fmt_char}', buf)[0]
    if t == FlexBufferType.FBT_FLOAT:
        assert bit_width >= 2
        fmt_char = ['f', 'f', 'f', 'd'][bit_width]
        return struct.unpack(f'<{fmt_char}', buf)[0]
    raise "unknown type"

def decode(buffer):
    root_width = struct.unpack('B', buffer[-1:])[0]
    off = 1 + root_width
    root_type = struct.unpack('B', buffer[-off:-1])[0]
    return decode_type(buffer[:-off], root_type)
