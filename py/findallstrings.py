import argparse
import codeprocessingtokens
import codeprocessingtools

parser = argparse.ArgumentParser()
parser.add_argument("filename", nargs="+")
args = parser.parse_args()

for filename in args.filename:
    with open(filename) as f:
        content = f.read()
    tokens = codeprocessingtokens.Tokens.fromFile(filename)
    for token in tokens:
        if token.kind == codeprocessingtokens.KIND_DOUBLE_QUOTE:
            print(token.spelling)
