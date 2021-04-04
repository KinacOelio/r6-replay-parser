import sys

import zstandard
import argparse
import io

from Parser import zst_utils
from Parser.binary_utils import bytes_to_hex_string
from Parser.zst_utils import find_last_zst_header

last_bytes = b'\x00\x00\x00\x00\x49\xcc\xd5\x76\xf4\x05\x5a\x22'


def display_warning(args, warning_text):
    print(warning_text)
    fail_if_not_forced(args)


def fail_if_not_forced(args):
    if args.force:
        return
    else:
        print("\n\nParsing stopped. No output written.\n(You can override this behavior using the -f flag)")
        sys.exit(9)


def decompress_stream_to_output_file(args, input_stream, bytes_to_read=-1):
    with open(args.out_file, 'wb') as of:
        decompressor = zstandard.ZstdDecompressor()
        decompressor.copy_stream(input_stream, of)


def main(args):
    with open(args.input_file, 'rb') as f:
        if args.is_zst:
            # The footer has been pre-stripped for us,
            # so we only need to decompress using the standard ZST library function
            decompress_stream_to_output_file(args, f)
        else:
            # We need to strip the footer from the rec file
            # before feeding it to the ZST library function
            in_memory_copy = io.BytesIO(f.read())
            buffer = in_memory_copy.getbuffer()

            actual_last_bytes = buffer[-len(last_bytes):]
            if actual_last_bytes != last_bytes:
                display_warning(args, f"WARNING: This doesn't look like a .rec file. "
                                      f"The last {len(last_bytes)} bytes didn't match the expected value.\n"
                                      f"Expected Value:\t\t{bytes_to_hex_string(actual_last_bytes)}\n"
                                      f"Actual Value:\t\t{bytes_to_hex_string(last_bytes)}")

            # Find the last frame in the ZST file
            last_zst_header_addr = find_last_zst_header(buffer)

            if last_zst_header_addr is None:
                display_warning(args, f"WARNING: This doesn't look like a .rec file. Couldn't find any ZST"
                                      f" magic number bytes")
            last_zst_header_bytes = bytes(buffer[last_zst_header_addr:last_zst_header_addr+25])
            frame_header_size = zstandard.frame_header_size(last_zst_header_bytes)

            # Read through each block in this last frame to find the location of the end of the file
            block_params = zst_utils.parse_block_header(last_zst_header_bytes[frame_header_size:frame_header_size+3])
            next_block_addr = last_zst_header_addr + frame_header_size + 3 + block_params.block_size

            while not block_params.last_block:
                block_params = zst_utils.parse_block_header(bytes(buffer[next_block_addr:next_block_addr+3]))
                next_block_addr += 3 + block_params.block_size

            # The next byte after the last block in the last frame is outside of the ZST file, giving us the length
            size_of_zst_file = next_block_addr

            # Only grab the first portion of the file (which is simply a ZST file)
            in_memory_copy.seek(0)
            zst_file_in_memory = io.BytesIO(in_memory_copy.read(size_of_zst_file))

            # Decompress and write to output file
            decompress_stream_to_output_file(args, zst_file_in_memory)







if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decompresses an entire .rec file")
    parser.add_argument('input_file', metavar='input_file', type=str, help="The file to decompress")
    parser.add_argument('out_file', metavar='output_file', type=str, help="The file path to write to")
    parser.add_argument('-z', '--is-zst', action='store_true', help="Indicate that the input file is already in ZST "
                                                                    "format (no need to strip the footer)")
    parser.add_argument('-f', '--force', action='store_true', help="Force the parser to continue despite warnings")

    main(parser.parse_args())