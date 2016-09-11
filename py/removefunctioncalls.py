import argparse
import codeprocessingtokens

parser = argparse.ArgumentParser()
parser.add_argument("--functionName", nargs="+", default=["NSLog"])
parser.add_argument("--replaceInline", action="store_true")
parser.add_argument("filename", nargs="+")
args = parser.parse_args()

for filename in args.filename:
    with open(filename) as f:
        content = f.read()
    tokens = codeprocessingtokens.Tokens.fromFile(filename)
    for functionName in args.functionName:
        for token in tokens:
            if token.spelling == functionName:
                assert tokens[token.index + 1].spelling == "("
                closingParen = tokens.closingParen(tokens[token.index + 1])
                semicolon = tokens[closingParen.index + 1]
                assert semicolon.spelling == ';'
                space = " " * (semicolon.offset + 1 - token.offset)
                content = content[:token.offset] + space + content[semicolon.offset + 1:]
    if args.replaceInline:
        with open(filename, "w") as f:
            f.write(content)
    else:
        print content
