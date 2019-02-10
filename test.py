import flexbuf
import unittest
import struct

FlexBufferType = flexbuf.FlexBufferType
BitWidth = flexbuf.BitWidth

class FlexBufTest(unittest.TestCase):
    def test_int(self):
        minus_13 = struct.pack('b', -13)
        self.assertEqual(flexbuf.decode(minus_13 + bytearray([4, 1])), -13)

    def test_uint(self):
        self.assertEqual(flexbuf.decode(bytearray([13, 8, 1])), 13)

    def test_float(self):
        test_float = -3.14
        bytes = struct.pack('<f', test_float)
        type_byte = FlexBufferType.FBT_FLOAT << 2 |  BitWidth.BIT_WIDTH_32
        self.assertAlmostEqual(flexbuf.decode(bytes + bytearray([type_byte, len(bytes) + 2])), test_float, places=5)

    def test_null(self):
        self.assertEqual(flexbuf.decode(bytearray([0, 0, 1])), b'0')

    def test_vec(self):
        self.assertEqual(flexbuf.decode(bytearray([3, 1, 2, 3, 4, 4, 4, FlexBufferType.FBT_VECTOR << 2, 6])), [1, 2, 3])

    def test_map(self):
        # Example from the documentation
        tmap = b'bar' + bytearray([0]) + b'foo' + bytearray([0])
        tmap += bytearray([2])  # key vec size
        tmap += bytearray([9, 6])  # offset to bar and foo
        tmap += bytearray([2, 1])  # offset to key vec and byte width
        tmap += bytearray([2])  # value vec size
        # value vec points here
        value_vec = bytearray([14, 13])  # values
        value_vec += bytearray([4, 4])  # types of values
        tmap += value_vec
        self.assertEqual(flexbuf.decode(tmap + bytearray([FlexBufferType.FBT_MAP << 2, len(value_vec)])), { 'foo' : 13, 'bar': 14 })


if __name__ == '__main__':
    unittest.main()
