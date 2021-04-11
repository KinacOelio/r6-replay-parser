import io
from typing import BinaryIO

from Parser.binary_utils import bytes_to_hex_string, decode_integer
import config


class RecBlock:
    """Base class representing a .REC 'block' - a sequence of bytes representing an atomic unit of data in
    a .REC file

    Stores the source bytes, and can be overridden to implement the extraction of useful information in dictionary
    form (see value())
    """
    @staticmethod
    def from_bytestream(bytestream: BinaryIO, length: int):
        try:
            int(length)
        except TypeError:
            raise ValueError("Cannot parse a block using RecBlock unless a length is provided")

        content_bytes = bytestream.read(length)
        return RecBlock(content_bytes)

    def __init__(self, src_bytes: bytes):
        self.src_bytes = src_bytes

    def __repr__(self):
        return f"RecBlock('{bytes_to_hex_string(self.src_bytes)}')"

    def __str__(self, explanation="Unknown block"):
        hex_string = bytes_to_hex_string(self.src_bytes)
        if len(hex_string) > (config.column_width - 10):
            hex_string = hex_string[:config.column_width - 13] + "..."

        out_str = hex_string
        out_str += ' ' * (config.column_width - len(hex_string))

        out_str += explanation
        return out_str

    @property
    def value(self):
        """Returns a dict with key-value pairs representing the data stored in this block"""
        raise NotImplementedError("Base class RecBlock cannot interpret the bytes in a REC block. "
                                  "Override value() and implement parsing logic for the byte sequence.")


class ExpectedBytesBlock(RecBlock):
    """A block that always contains the same bytes. Verifies that the bytes are read in as expected. Can be
    used to detect corruption"""

    @staticmethod
    def from_bytestream(bytestream: BinaryIO, expected_bytes: bytes):
        read_bytes = bytestream.read(len(expected_bytes))

        if read_bytes != expected_bytes:
            raise ValueError(f"Received bytes ({bytes_to_hex_string(read_bytes)}) did not "
                             f"match expected bytes ({bytes_to_hex_string(expected_bytes)})")

        return ExpectedBytesBlock(read_bytes)

    def __init__(self, src_bytes: bytes, expected_bytes=None):
        if expected_bytes is None:
            # TODO: Issue warning that no assertion is being performed?
            expected_bytes = src_bytes

        if src_bytes != expected_bytes:
            raise ValueError(f"Received bytes ({bytes_to_hex_string(src_bytes)}) did not "
                             f"match expected bytes ({bytes_to_hex_string(expected_bytes)})")
        super().__init__(src_bytes)

    def __repr__(self):
        return f"ExpectedBytesBlock('{bytes_to_hex_string(self.src_bytes)}')"

    def __str__(self, explanation=f'As expected'):
        return super().__str__(explanation)

    @property
    def value(self):
        return dict({})


class MagicNumberBlock(ExpectedBytesBlock):
    """A block containing the .REC file magic number"""
    @staticmethod
    def from_bytestream(bytestream: BinaryIO):
        expected_bytes = b'dissect\x00\x04\x00\x00\x00'
        return MagicNumberBlock(bytestream.read(len(expected_bytes)), expected_bytes)

    def __repr__(self):
        return f"MagicNumberBlock('{bytes_to_hex_string(self.src_bytes)}')"

    def __str__(self, explanation=f'.REC file magic number'):
        return super().__str__(explanation)


class StringBlock(RecBlock):
    """A .REC block containing a single string (prepended by the length of the string)"""
    @staticmethod
    def from_bytestream(bytestream: BinaryIO, num_length_bytes=8):
        string_length_bytes = bytestream.read(num_length_bytes)
        string_length = decode_integer(string_length_bytes)
        string_content_bytes = bytestream.read(string_length)
        string_content = string_content_bytes.decode('UTF-8')

        return StringBlock(string_length_bytes + string_content_bytes, string_length, string_content)

    def __init__(self, src_bytes: bytes, length: int, content: str):
        super().__init__(src_bytes)
        self.length = length
        self.content = content

    def __repr__(self):
        return f"StringBlock('{self.content}')"

    def __str__(self, explanation=None):
        if explanation is None:
            explanation = f'"{self.content}"'
        return super().__str__(explanation)

    @property
    def value(self):
        return {
            'length': self.length,
            'content': self.content
        }


class StringKeyValueBlock(RecBlock):
    """A .REC block composed of two StringBlocks, where the first represents the key, and the
    second represents the value"""

    @staticmethod
    def from_bytestream(bytestream: BinaryIO):
        key_block = StringBlock.from_bytestream(bytestream)
        value_block = StringBlock.from_bytestream(bytestream)

        return StringKeyValueBlock(key_block, value_block)

    def __init__(self, key_block: StringBlock, value_block: StringBlock):
        super().__init__(key_block.src_bytes + value_block.src_bytes)
        self.key_block = key_block
        self.value_block = value_block

    def __repr__(self):
        return f"KeyValueBlock('{self.key_block.value['content']}': '{self.value_block.value['content']}')"

    def __str__(self, explanation=None):
        if explanation is None:
            explanation = f"'{self.key_block.value['content']}': '{self.value_block.value['content']}'"
        return super().__str__(explanation)

    @property
    def value(self):
        return {
            'key': self.key_block.value['content'],
            'value': self.value_block.value['content']
        }
