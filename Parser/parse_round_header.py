import argparse
import config

from Parser.rec_segment import HeaderSegment, MultiKeyValueSegment, MultiBlockSegment


def main(args):
    config.column_width = args.column_width

    with open(args.file_path, 'rb') as f:
        header_segment = HeaderSegment.from_bytestream(f)
        print(header_segment.peek_first_few_blocks())

        key_value_segment = MultiKeyValueSegment.from_bytestream(f)
        print(key_value_segment.peek_first_few_blocks())

        fixed_width_segment = MultiBlockSegment.from_bytestream(f, block_size=12, num_padding_bytes=8)
        print(fixed_width_segment.peek_first_few_blocks())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parses the first frame of a R6 .rec file")
    parser.add_argument('file_path', metavar='path', type=str, help="The file to parse")
    parser.add_argument('-c', '--column-width', default=70, type=int)

    main(parser.parse_args())


