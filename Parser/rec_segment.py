from typing import List

from typing.io import BinaryIO

from Parser.binary_utils import decode_integer
from Parser.rec_block import MagicNumberBlock, StringBlock, RecBlock, StringKeyValueBlock


class RecSegment:
    """Abstract base class representing a .REC 'segment' - an ordered collection of .REC blocks"""
    @staticmethod
    def from_bytestream(bytestream: BinaryIO):
        raise NotImplementedError("Abstract base class RecSegment cannot parse segment from bytestream. Override"
                                  "from_bytestream() in a child class and implement parsing logic")

    def __init__(self, content_blocks: List[RecBlock]):
        self.content_blocks = content_blocks

    def __repr__(self):
        return f'RecSegment({self.content_blocks})'

    def __str__(self):
        out_str = ""
        for block in self.content_blocks:
            out_str += "--------------------------" * 5 + '\n'
            out_str += str(block) + '\n'
        out_str += "--------------------------" * 5 + '\n\n\n'

        return out_str

    def peek_first_few_blocks(self, num_blocks=10):
        out_str = ""
        for i in range(num_blocks):
            if i >= len(self.content_blocks):
                break
            out_str += "--------------------------" * 5 + '\n'
            out_str += str(self.content_blocks[i]) + '\n'
        out_str += "--------------------------" * 5 + '\n'

        return out_str


class HeaderSegment(RecSegment):
    @staticmethod
    def from_bytestream(bytestream: BinaryIO):
        magic_number = MagicNumberBlock.from_bytestream(bytestream)
        version_string = StringBlock.from_bytestream(bytestream)
        unknown_block = RecBlock.from_bytestream(bytestream, 8)

        return HeaderSegment([magic_number, version_string, unknown_block])

    def __repr__(self):
        return f'HeaderSegment({self.content_blocks})'

    def __str__(self):
        out_str = "--------------------------" * 5 + '\n'
        out_str += "--------------------------" * 5 + '\n'
        out_str += ' '* 55 + "Header Segment\n"
        out_str += "--------------------------" * 5 + '\n'
        out_str += super().__str__()
        return out_str

    def peek_first_few_blocks(self, num_blocks=10):
        out_str = "--------------------------" * 5 + '\n'
        out_str += "--------------------------" * 5 + '\n'
        out_str += ' ' * 55 + "Header Segment\n"
        out_str += "--------------------------" * 5 + '\n'
        out_str += super().peek_first_few_blocks(num_blocks)
        return out_str


class SegmentWithHeader(RecSegment):
    def __init__(self, header_blocks: List[RecBlock], content_blocks: List[RecBlock]):
        super().__init__(content_blocks)
        self.header_blocks = header_blocks

    def __str__(self):
        out_str = ""
        if len(self.header_blocks):
            out_str += "--------------------------" * 5 + '\n'
            for block in self.header_blocks:
                out_str += str(block) + '\n'
            out_str += "--------------------------" * 5 + '\n'

        out_str += super().__str__()
        return out_str

    def peek_first_few_blocks(self, num_blocks=10):
        out_str = ""
        if len(self.header_blocks):
            out_str += "--------------------------" * 5 + '\n'
            for block in self.header_blocks:
                out_str += str(block) + '\n'
            out_str += "--------------------------" * 5 + '\n'

        out_str += super().peek_first_few_blocks(num_blocks)
        return out_str


class MultiBlockSegment(SegmentWithHeader):
    @classmethod
    def from_bytestream(cls, bytestream: BinaryIO, num_length_bytes=8, block_size=None, num_padding_bytes=0):
        segment_length_bytes = bytestream.read(num_length_bytes)
        segment_length = decode_integer(segment_length_bytes)

        header_blocks = []
        if num_padding_bytes > 0:
            header_blocks.append(RecBlock.from_bytestream(bytestream, length=num_padding_bytes))

        content_blocks = []
        for i in range(segment_length):
            content_blocks.append(cls.parse_block(bytestream, block_size))

        return cls(header_blocks, content_blocks)

    @staticmethod
    def parse_block(bytestream: BinaryIO, block_size: int):
        return RecBlock.from_bytestream(bytestream, block_size)

    def __repr__(self):
        return f'MultiBlockSegment({self.content_blocks})'

    def __str__(self):
        out_str = "--------------------------" * 5 + '\n'
        out_str += "--------------------------" * 5 + '\n'
        out_str += ' '* 45 + f"Multi-Block Segment ({len(self.content_blocks)} blocks follow)\n"
        out_str += "--------------------------" * 5 + '\n'
        out_str += super().__str__()
        return out_str

    def peek_first_few_blocks(self, num_blocks=10):
        out_str = "--------------------------" * 5 + '\n'
        out_str += "--------------------------" * 5 + '\n'
        out_str += ' '* 45 + f"Multi-Block Segment ({len(self.content_blocks)} blocks follow)\n"
        out_str += "--------------------------" * 5 + '\n'
        out_str += super().peek_first_few_blocks(num_blocks)
        return out_str


class MultiKeyValueSegment(MultiBlockSegment):
    @staticmethod
    def parse_block(bytestream: BinaryIO, block_size: int):
        if block_size is not None:
            raise ValueError("block_size is not supported when using MultiKeyValueSegment")

        return StringKeyValueBlock.from_bytestream(bytestream)

    def __repr__(self):
        return f'MultiKeyValueSegment({self.content_blocks})'

    def __str__(self):
        out_str = "--------------------------" * 5 + '\n'
        out_str += "--------------------------" * 5 + '\n'
        out_str += ' '* 45 + f"Multi-Key-Value Segment ({len(self.content_blocks)} key-value pairs follow)\n"
        out_str += "--------------------------" * 5 + '\n'
        out_str += SegmentWithHeader.__str__(self)
        return out_str

    def peek_first_few_blocks(self, num_blocks=10):
        out_str = "--------------------------" * 5 + '\n'
        out_str += "--------------------------" * 5 + '\n'
        out_str += ' '* 45 + f"Multi-Key-Value Segment ({len(self.content_blocks)} key-value pairs follow)\n"
        out_str += "--------------------------" * 5 + '\n'
        out_str += SegmentWithHeader.peek_first_few_blocks(self, num_blocks)
        return out_str
