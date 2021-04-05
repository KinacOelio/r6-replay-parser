import argparse

from Parser.binary_utils import decode_integer, print_block

header_properties = []

packet_ids = []
packet_timestamps = []


def read_string(bytestream):
    string_length_bytes = bytestream.read(8)
    string_length = decode_integer(string_length_bytes)

    string_bytes = bytestream.read(string_length)
    string_val = string_bytes.decode('UTF-8')

    return string_length_bytes + string_bytes, string_val


def read_packet(bytestream, i):
    packet_id_bytes = bytestream.read(4)
    packet_id_num = decode_integer(packet_id_bytes)

    unknown_content_bytes = bytestream.read(4)

    timestamp_bytes = bytestream.read(4)

    timestamp_val = decode_integer(timestamp_bytes)

    packet_ids.append(packet_id_num)
    packet_timestamps.append(timestamp_val)

    return (
        packet_id_bytes + unknown_content_bytes + timestamp_bytes,
        f"Packet #{packet_id_num}, UNKNOWN CONTENT, {timestamp_val}"
    )


def main(args):
    with open(args.file_path, 'rb') as f:
        magic_number = f.read(12)

        if args.show_header:
            print_block(magic_number, ".REC File Magic Number", args, 0)
        str_bytes, str_val = read_string(f)
        if args.show_header:
            print_block(str_bytes, f'"{str_val}"', args, 0)

        unknown_header_bytes = f.read(8)

        if args.show_header:
            print_block(unknown_header_bytes, "????? (Purpose unknown)", args, 0)

        number_of_header_properties_bytes = f.read(8)

        number_of_header_properties = decode_integer(number_of_header_properties_bytes)

        if args.show_header:
            print_block(
                number_of_header_properties_bytes,
                f"{number_of_header_properties} key-value string pairs follow...",
                args, 0
            )

        for i in range(number_of_header_properties):
            key_bytes, key_str = read_string(f)
            val_bytes, val_str = read_string(f)

            header_properties.append((key_str, val_str))

            if args.show_header:
                print_block(key_bytes + val_bytes, f'"{key_str}": "{val_str}"', args, 0)

        for segment in range(args.show_body):
            print("--------------------------" * 5)
            print("--------------------------" * 5)
            print("FILE SEGMENT FOLLOWS")
            print("--------------------------" * 5)

            number_of_packets_bytes = f.read(4)
            number_of_packets = decode_integer(number_of_packets_bytes)
            if args.show_body:
                print_block(number_of_packets_bytes, f"{number_of_packets} packets follow...", args, 0)


            if segment == 0:
                zeros = f.read(12)
                if args.show_body:
                    print_block(zeros, "Zeros to space between header and body?", args, 0)

            for i in range(number_of_packets - 1):
                if segment == 0:
                    packet_bytes, packet_desc = read_packet(f, i)
                if segment == 1:
                    packet_bytes = f.read(29)
                if i > args.max_packets:
                    continue
                if args.show_body:
                    print_block(packet_bytes, packet_desc, args, segment)

                if i > args.max_packets:
                    return

            zeros = f.read(8)
            if args.show_body:
                print_block(zeros, "Zeros to space between segments", args, 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parses the first frame of a R6 .rec file")
    parser.add_argument('file_path', metavar='path', type=str, help="The file to parse")
    parser.add_argument('-m', '--max-packets', default=200, type=int)
    parser.add_argument('-H', '--show-header', action='store_true')
    parser.add_argument('-B', '--show-body', action='store', default=0, type=int, help="the number of body segments to display (default=0)")
    parser.add_argument('-S', '--hide-source-bytes', action='store_true')
    parser.add_argument('-c', '--column-width', default=70, type=int)

    main(parser.parse_args())


