"""
parse.py: generate Hugo friendly annotated markdown files
"""
import argparse
from parser import Metadata

parser = argparse.ArgumentParser()
parser.add_argument("input", help='input markdown folder / file')
parser.add_argument("root", help='root markdown folder / file')
parser.add_argument("output", help='output markdown folder / file')

if __name__ == "__main__":
    # argument parser
    args = parser.parse_args()
    input_path, root_path, output_path = args.input, args.root, args.output
    Metadata.generate(input_path, root_path, output_path)