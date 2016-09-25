import argparse
import codeprocessingtokens
import codeprocessingtools

parser = argparse.ArgumentParser()
parser.add_argument("--functionName", nargs="+", default=["NSLog"])
parser.add_argument("--replaceWith", default="")
parser.add_argument("--replaceInline", action="store_true")
parser.add_argument("filename", nargs="+")
args = parser.parse_args()

for filename in args.filename:
    with open(filename) as f:
        content = f.read()
    tokens = codeprocessingtokens.Tokens.fromFile(filename)
    for functionName in args.functionName:
        for macro in codeprocessingtools.findMacro(functionName, tokens, semicolon=True):
            tokens.replaceBetweenTokens(macro['firstToken'], macro['semicolon'], args.replaceWith)
    if args.replaceInline:
        with open(filename, "w") as f:
            f.write(tokens.joinSpellings())
    else:
        print tokens.joinSpellings()
