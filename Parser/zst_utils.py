import binary_utils

zst_file_magic_number = b'\x28\xB5\x2F\xFD'

class BlockParameters(object):
    block_size: int
    block_type: int
    last_block: bool

def find_last_zst_header(buffer):
    for i in range(len(buffer)):
        if bytes(buffer[-(i+4):-i]) == zst_file_magic_number:
            return len(buffer) - (i + 4)


def parse_block_header(block_header_bytes):
    if len(block_header_bytes) != 3:
        raise ValueError(f"Invalid number of bytes for block header. Expecting 3 bytes, got: "
                         f"{binary_utils.bytes_to_hex_string(block_header_bytes)}")

    lowest_byte = block_header_bytes[0]
    output = BlockParameters()

    output.last_block = (lowest_byte & 0x01) == 0x01
    output.block_type = ((lowest_byte >> 1) & 0x03)
    output.block_size = binary_utils.decode_integer(block_header_bytes + b'\x00') >> 3

    return output
