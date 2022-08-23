import argparse
import os


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="back up a directory into an Elastic Block Storage (EBS) volume"
    )

    parser.add_argument(
        '-k',
        '--keyname',
        metavar='keyname',
        type=str,
        default='ebs-backup',
        help='the name of the keypair to use'
    )

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='enable verbose logging'
    )

    parser.add_argument(
        'path',
        type=str,
        help='the file/directory to be backed up'
    )

    return parser.parse_args()


def get_size(path):
    if os.path.isfile(path):
        return get_file_size(path)
    elif os.path.isdir(path):
        return get_dir_size(path)


def get_file_size(file):
    return os.path.getsize(file)


def get_dir_size(dir):
    size = 0

    for dir_path, dir_name, file_names in os.walk(dir):
        for file_name in file_names:
            file_path = os.path.join(dir_path, file_name)
            if os.path.islink(file_path):
                size += os.lstat(file_path).st_size
            else:
                size += os.path.getsize(file_path)

    return size
