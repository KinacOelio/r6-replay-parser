import struct


def decode_integer(hex_bytes):
    """
    Decode a bytes object in little endian notation into its integer form
    :param hex_bytes: a bytes object with a length of either 2, 4, or 8
    :return: the integer represented in the given bytes
    """
    if len(hex_bytes) == 2:
        return struct.unpack("<H", hex_bytes)[0]
    elif len(hex_bytes) == 4:
        return struct.unpack("<I", hex_bytes)[0]
    elif len(hex_bytes) == 8:
        return struct.unpack("<Q", hex_bytes)[0]
    else:
        raise ValueError(f"ByteString: {bytes_to_hex_string(hex_bytes)} is of incorrect length")


def bytes_to_hex_string(hex_bytes):
    hex_str = hex_bytes.hex().upper()
    return ' '.join([hex_str[i:i + 4] for i in range(0, len(hex_str), 4)])


def print_block(hex_bytes, explanation, args, segment):
    if segment == 0:
        print("--------------------------" * 5)
        if not args.hide_source_bytes:
            hex_string = bytes_to_hex_string(hex_bytes)
            if len(hex_string) > (args.column_width - 10):
                hex_string = hex_string[:args.column_width - 13] + "..."

            print(hex_string, end='')
            print(' ' * (args.column_width - len(hex_string)), end='')

        print(explanation)
    elif segment == 1:
        print("--------------------------" * 5)
        print(bytes_to_hex_string(hex_bytes))