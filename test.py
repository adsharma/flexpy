import flexbuf
import unittest
import struct

FlexBufferType = flexbuf.FlexBufferType

class FlexBufTest(unittest.TestCase):
    def test_int(self):
        minus_13 = struct.pack('b', -13)
        self.assertEqual(flexbuf.decode(minus_13 + bytearray([4, 1])), -13)

    def test_uint(self):
        self.assertEqual(flexbuf.decode(bytearray([13, 8, 1])), 13)

    def test_null(self):
        self.assertEqual(flexbuf.decode(bytearray([0, 0, 1])), b'0')

    def test_vec(self):
        self.assertEqual(flexbuf.decode(bytearray([3, 1, 2, 3, 4, 4, 4, FlexBufferType.FBT_VECTOR << 2, 6])), [1, 2, 3])


if __name__ == '__main__':
    unittest.main()
