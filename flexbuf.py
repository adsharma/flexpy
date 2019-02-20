# Flexbuffer decoder in python

import struct
from typing import Any, List, Optional
from enum import IntEnum


#
# Some constants from flexbuffer.h
#
# These are used in the lower 2 bits of a type field to determine the size of
# the elements (and or size field) of the item pointed to (e.g. vector).
class BitWidth(IntEnum):
    BIT_WIDTH_8 = 0
    BIT_WIDTH_16 = 1
    BIT_WIDTH_32 = 2
    BIT_WIDTH_64 = 3


byte_widths = [1, 2, 4, 8]


# These are used as the upper 6 bits of a type field to indicate the actual
# type.
class FlexBufferType(IntEnum):
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
    FBT_VECTOR = 10  # Untyped.
    FBT_VECTOR_INT = 11  # Typed any size (stores no type table).
    FBT_VECTOR_UINT = 12
    FBT_VECTOR_FLOAT = 13
    FBT_VECTOR_KEY = 14
    FBT_VECTOR_STRING = 15
    FBT_VECTOR_INT2 = 16  # Typed tuple (no type table, no size field).
    FBT_VECTOR_UINT2 = 17
    FBT_VECTOR_FLOAT2 = 18
    FBT_VECTOR_INT3 = 19  # Typed triple (no type table, no size field).
    FBT_VECTOR_UINT3 = 20
    FBT_VECTOR_FLOAT3 = 21
    FBT_VECTOR_INT4 = 22  # Typed quad (no type table, no size field).
    FBT_VECTOR_UINT4 = 23
    FBT_VECTOR_FLOAT4 = 24
    FBT_BLOB = 25
    FBT_BOOL = 26
    FBT_VECTOR_BOOL = 36  # To Allow the same type of conversion of type to vector type


def decode_typed_vec(buf) -> List:
    size = struct.unpack(f"<b", buf[:1])[0]
    type_bytes = buf[-size:]
    off = 1
    vec = []
    for i in range(size):
        num_bytes = byte_widths[type_bytes[i] & 0x3]
        vec.append(decode_type(buf[off: off + num_bytes], 0, None, type_bytes[i]))
        off += num_bytes
    return vec


def scalarify(t: FlexBufferType) -> FlexBufferType:
    """Returns a scalar type for a given vector type."""
    known = {
        FlexBufferType.FBT_VECTOR_INT: FlexBufferType.FBT_INT,
        FlexBufferType.FBT_VECTOR_STRING: FlexBufferType.FBT_STRING,
    }
    if t in known:
        return known[t]
    else:
        return t


def decode_untyped_vec(buf, size: int, bit_width: BitWidth, t: FlexBufferType) -> List:
    """Like decode_typed_vec, but the type and element width are passed in."""
    off = 0
    if bit_width is None:
        bit_width = BitWidth.BIT_WIDTH_8
    vec = []
    scalar_type = scalarify(t)
    for _ in range(size):
        if scalar_type == FlexBufferType.FBT_STRING:
            num_bytes = buf[off] + 1  # For the size byte
        else:
            num_bytes = byte_widths[bit_width]
        vec.append(
            decode_type(
                buf[off: off + num_bytes],
                0,
                None,
                FlexBufferType(scalar_type << 2 | bit_width),
            )
        )
        off += num_bytes
    return vec


def decode_key_string(buf, off: int) -> str:
    """Decodes a byte array at buf[off:] into string, stripping off null terminator"""
    i = buf[off:].find(b"\0")
    if i == -1:
        return buf[off:]
    return buf[off: off + i].decode("utf-8")


def element_width(t: FlexBufferType, bit_width: BitWidth) -> int:
    """Returns width in bytes. """
    widths = {
        FlexBufferType.FBT_BLOB: None,
        FlexBufferType.FBT_VECTOR_BOOL: 1,
        FlexBufferType.FBT_VECTOR_INT: None,
        FlexBufferType.FBT_VECTOR_STRING: 1,
        FlexBufferType.FBT_STRING: 1,
    }
    if t in widths:
        return widths[t] or 1 << bit_width
    raise Exception("unknown type")


def decode_offset_type(buf, off: int, bit_width: BitWidth, t: FlexBufferType) -> Any:
    size = buf[-off]
    num_bytes = size * element_width(t, bit_width)
    buf = buf[-off + 1:]
    if t != FlexBufferType.FBT_VECTOR_STRING:
        assert len(buf) == num_bytes
    if t == FlexBufferType.FBT_STRING:
        return buf[:-1].decode("utf-8")
    if t == FlexBufferType.FBT_KEY:
        return decode_key_string(buf, 0)
    if t == FlexBufferType.FBT_BLOB:
        return buf
    if is_vector(t):
        return decode_untyped_vec(buf, size, bit_width, t)


def is_vector(t: FlexBufferType) -> bool:
    return (
        t >= FlexBufferType.FBT_VECTOR
        and t <= FlexBufferType.FBT_VECTOR_FLOAT4
        or t == FlexBufferType.FBT_MAP
    )


def is_inline_type(t: FlexBufferType) -> bool:
    return t in {
        FlexBufferType.FBT_INT,
        FlexBufferType.FBT_UINT,
        FlexBufferType.FBT_FLOAT,
        FlexBufferType.FBT_BOOL,
        FlexBufferType.FBT_NULL,
    }


def is_offset_type(t: FlexBufferType) -> bool:
    return not is_inline_type(t)


def has_size_field(t: FlexBufferType) -> bool:
    return is_inline_type(t) or t in {FlexBufferType.FBT_VECTOR_INT}


def decode_type(
    orig_buf, off: int, input_bit_width: Optional[BitWidth], input_t: int
) -> Any:
    if input_bit_width is None and has_size_field(FlexBufferType(input_t >> 2)):
        bit_width = BitWidth(input_t & 0x3)
    elif input_bit_width is not None:
        bit_width = BitWidth(input_bit_width)
    else:
        bit_width = BitWidth.BIT_WIDTH_8
    t = FlexBufferType(input_t >> 2)
    buf = orig_buf
    if t == FlexBufferType.FBT_NULL:
        return b"0"
    if t == FlexBufferType.FBT_BOOL:
        return struct.unpack(f"<B", buf)[0]
    if t == FlexBufferType.FBT_INT:
        fmt_char = ["b", "h", "i", "l"][bit_width]
        return struct.unpack(f"<{fmt_char}", buf)[0]
    if t == FlexBufferType.FBT_UINT:
        fmt_char = ["B", "H", "I", "L"][bit_width]
        return struct.unpack(f"<{fmt_char}", buf)[0]
    if t == FlexBufferType.FBT_FLOAT:
        assert bit_width >= 2
        fmt_char = ["f", "f", "f", "d"][bit_width]
        return struct.unpack(f"<{fmt_char}", buf)[0]
    if t == FlexBufferType.FBT_VECTOR:
        off = buf[-1]
        # off is relative to buf[-1]. We need another -1 to
        # include the size byte, so we end up with -off-2
        return decode_typed_vec(buf[-off - 1 - 1: -1])
    if t == FlexBufferType.FBT_VECTOR_KEY:
        size = buf[-off - 1]
        vec = []
        for i in range(size):
            elem_off = -off + i
            relative_off = buf[elem_off]
            vec.append(decode_key_string(buf, elem_off - relative_off))
        return vec
    if t == FlexBufferType.FBT_MAP:
        buf = orig_buf[-off:]
        value_vec = decode_typed_vec(buf)
        buf = orig_buf[:-off]
        # Decode offset to key vec and width
        bit_width = buf[-1]
        off = int(buf[-2])
        buf = buf[:-2]
        key_vec = decode_type(buf, off, bit_width, FlexBufferType.FBT_VECTOR_KEY << 2)
        d = dict(zip(key_vec, value_vec))
        return d
    if is_offset_type(t):
        return decode_offset_type(buf, off, bit_width, t)
    raise Exception("unknown type")


def decode(buffer):
    root_width = struct.unpack("B", buffer[-1:])[0]
    root_type = struct.unpack("B", buffer[-2:-1])[0]
    off = root_width
    if is_offset_type(root_type >> 2):
        off += 1  # to include the size byte
    return decode_type(buffer[:-2], off, None, root_type)
