# generate unittest code framework

import unittest
from nedis import NESP

# https://redis.io/docs/reference/protocol-spec/#resp-protocol-description

class TestNesp(unittest.TestCase):
    def test_simple_string(self):
        self.assertEqual(NESP.serialize(NESP.SimpleString("OK")), b"+OK\r\n")
        self.assertEqual(NESP.deserialize(b"+OK\r\n"), NESP.SimpleString("OK"))

    def test_simple_error(self):
        self.assertEqual(NESP.serialize(NESP.SimpleError("ERR")), b"-ERR\r\n")
        self.assertEqual(NESP.deserialize(b"-ERR\r\n"), NESP.SimpleError("ERR"))

    def test_integer(self):
        self.assertEqual(NESP.serialize(NESP.Integer(1000)), b":1000\r\n")
        self.assertEqual(NESP.deserialize(b":1000\r\n"), NESP.Integer(1000))
        # optional +
        self.assertEqual(NESP.deserialize(b":+1000\r\n"), NESP.Integer(1000))
        # optional -
        self.assertEqual(NESP.serialize(NESP.Integer(-1000)), b":-1000\r\n")
        self.assertEqual(NESP.deserialize(b":-1000\r\n"), NESP.Integer(-1000))
    
    def test_bulk_string(self):
        # So the string "hello" is encoded as follows:
        self.assertEqual(NESP.serialize(NESP.BulkString("hello")), b"$5\r\nhello\r\n")
        self.assertEqual(NESP.deserialize(b"$6\r\nhello\r\n"), NESP.BulkString("hello"))
        # The empty string's encoding is:
        self.assertEqual(NESP.serialize(NESP.BulkString("")), b"$0\r\n\r\n")
        self.assertEqual(NESP.deserialize(b"$0\r\n\r\n"), NESP.BulkString(""))
        # Null bulk strings
        self.assertEqual(NESP.serialize(NESP.BulkString(None)), b"$-1\r\n")
        self.assertEqual(NESP.deserialize(b"$-1\r\n"), NESP.BulkString(None))

    def test_array(self):
        # So an empty Array is just the following:
        self.assertEqual(NESP.serialize(NESP.Array([])), b"*0\r\n")
        self.assertEqual(NESP.deserialize(b"*0\r\n"), NESP.Array([]))
        # Whereas the encoding of an array consisting of the two bulk strings "hello" and "world" is:
        self.assertEqual(NESP.serialize(NESP.Array([NESP.BulkString("hello"), NESP.BulkString("world")])), b"*2\r\n$5\r\nhello\r\n$5\r\nworld\r\n")
        self.assertEqual(NESP.deserialize(b"*2\r\n$5\r\nhello\r\n$5\r\nworld\r\n"), NESP.Array([NESP.BulkString("hello"), NESP.BulkString("world")]))
        # For example, an Array of three integers is encoded as follows:
        self.assertEqual(NESP.serialize(NESP.Array([NESP.Integer(1), NESP.Integer(2), NESP.Integer(3)])), b"*3\r\n:1\r\n:2\r\n:3\r\n")
        self.assertEqual(NESP.deserialize(b"*3\r\n:1\r\n:2\r\n:3\r\n"), NESP.Array([NESP.Integer(1), NESP.Integer(2), NESP.Integer(3)]))
        # For instance, the following encoding is of a list of four integers and a bulk string:
        self.assertEqual(NESP.serialize(NESP.Array([NESP.Integer(1), NESP.Integer(2), NESP.Integer(3), NESP.Integer(4), NESP.BulkString("hello")])), b"*5\r\n:1\r\n:2\r\n:3\r\n:4\r\n$5\r\nhello\r\n")
        self.assertEqual(NESP.deserialize(b"*5\r\n:1\r\n:2\r\n:3\r\n:4\r\n$5\r\nhello\r\n"), NESP.Array([NESP.Integer(1), NESP.Integer(2), NESP.Integer(3), NESP.Integer(4), NESP.BulkString("hello")]))
        # For example, a nested array of two arrays is encoded as follows:
        self.assertEqual(NESP.serialize(NESP.Array([NESP.Array([NESP.Integer(1), NESP.Integer(2), NESP.Integer(3)]), NESP.Array([NESP.SimpleString("Hello"), NESP.SimpleError("World")])])), b"*2\r\n*3\r\n:1\r\n:2\r\n:3\r\n*2\r\n+Hello\r\n-World\r\n")
        self.assertEqual(NESP.deserialize(b"*2\r\n*3\r\n:1\r\n:2\r\n:3\r\n*2\r\n+Hello\r\n-World\r\n"), NESP.Array([NESP.Array([NESP.Integer(1), NESP.Integer(2), NESP.Integer(3)]), NESP.Array([NESP.SimpleString("Hello"), NESP.SimpleError("World")])]))
        # Null arrays
        self.assertEqual(NESP.serialize(NESP.Array(None)), b"*-1\r\n")
        self.assertEqual(NESP.deserialize(b"*-1\r\n"), NESP.Array(None))
        # Here's an example of an array reply containing a null element:
        self.assertEqual(NESP.serialize(NESP.Array([NESP.BulkString("hello"), NESP.BulkString(None), NESP.BulkString("world")])), b"*3\r\n$5\r\nhello\r\n$-1\r\n$5\r\nworld\r\n")
        self.assertEqual(NESP.deserialize(b"*3\r\n$5\r\nhello\r\n$-1\r\n$5\r\nworld\r\n"), NESP.Array([NESP.BulkString("hello"), NESP.BulkString(None), NESP.BulkString("world")]))

    def test_null(self):
        # Nulls' encoding is the underscore (_) character, followed by the CRLF terminator (\r\n). Here's Null's raw RESP encoding:
        self.assertEqual(NESP.serialize(NESP.Null()), b"_\r\n")
        self.assertEqual(NESP.deserialize(b"_\r\n"), NESP.Null())

    def test_boolean(self):
        self.assertEqual(NESP.serialize(NESP.Boolean(True)), b"#t\r\n")
        self.assertEqual(NESP.deserialize(b"#t\r\n"), NESP.Boolean(True))
        self.assertEqual(NESP.serialize(NESP.Boolean(False)), b"#f\r\n")
        self.assertEqual(NESP.deserialize(b"#f\r\n"), NESP.Boolean(False))

    def test_double(self):
        self.assertEqual(NESP.serialize(NESP.Double(1.23)), b",1.23\r\n")
        self.assertEqual(NESP.deserialize(b",1.23\r\n"), NESP.Double(1.23))
        self.assertEqual(NESP.serialize(NESP.Double(-1.23)), b",-1.23\r\n")
        self.assertEqual(NESP.deserialize(b",-1.23\r\n"), NESP.Double(-1.23))
        # The positive infinity, negative infinity and NaN values are encoded as follows:
        self.assertEqual(NESP.serialize(NESP.Double(float('inf'))), b",inf\r\n")
        self.assertEqual(NESP.deserialize(b",inf\r\n"), NESP.Double(float('inf')))
        self.assertEqual(NESP.serialize(NESP.Double(float('-inf'))), b",-inf\r\n")
        self.assertEqual(NESP.deserialize(b",-inf\r\n"), NESP.Double(float('-inf')))
        self.assertEqual(NESP.serialize(NESP.Double(float('nan'))), b",nan\r\n")
        # float('nan') == float('nan') is False
        self.assertNotEqual(NESP.deserialize(b",nan\r\n"), NESP.Double(float('nan')))
