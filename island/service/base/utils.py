"""
Various utils
"""
from io import BytesIO
from google.protobuf.message import Message


def encode_uvarint(number: int) -> bytes:
    """
    Encode varint into bytes
    """
    # Shift to int64
    buf = b""
    while True:
        towrite = number & 0x7F
        number >>= 7
        if number:
            buf += bytes((towrite | 0x80,))
        else:
            buf += bytes((towrite,))
            break
    return buf


def decode_uvarint(stream: BytesIO) -> int:
    """
    Decode bytes into int
    """
    shift = 0
    result = 0
    while True:
        i = _read_one(stream)
        result |= (i & 0x7F) << shift
        shift += 7
        if not (i & 0x80):
            break
    return result


def _read_one(stream: BytesIO) -> int:
    """
    Read 1 byte, converting it into an int
    """
    c = stream.read(1)
    if c == b"":
        raise EOFError("Unexpected EOF while reading bytes")
    return ord(c)


def write_message(message: Message) -> bytes:
    """
    Write length prefixed protobuf message
    """
    buffer = BytesIO(b"")
    bz = message.SerializeToString()
    buffer.write(encode_uvarint(len(bz) << 1))
    buffer.write(bz)
    return buffer.getvalue()


def read_messages(reader: BytesIO, message: Message) -> Message:
    """
    Return an interator over the messages found in the byte stream
    """
    while True:
        try:
            length = decode_uvarint(reader) >> 1
        except EOFError:
            return
        data = reader.read(length)
        if len(data) < length:
            return
        m = message()
        m.ParseFromString(data)

        yield m
