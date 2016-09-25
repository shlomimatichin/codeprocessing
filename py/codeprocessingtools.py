import codeprocessingtokens


def stripComment(text):
    if text.startswith("//"):
        return _stripOneNewLine(text[len("//"):])
    elif text.startswith("/*"):
        assert text.endswith("*/")
        return text[len("/*"): -len("*/")]
    elif text.startswith("#"):
        return _stripOneNewLine(text[len("#"):])
    else:
        raise AssertionError("Uknown comment to strip: %s" % text)


def _stripOneNewLine(text):
    if text.endswith("\n"):
        return text[:-len("\n")]
    else:
        return text


def findMacro(macrospellings, tokens, semicolon=False):
    if isinstance(macrospellings, str):
        macrospellings = [macrospellings]
    macroname = "".join(macrospellings)
    for match in tokens.findAllSpellings(macrospellings + ["("]):
        closingParen = tokens.closingParen(match[1])
        result = dict(
            name=macroname,
            firstToken=match[0],
            openingParen=match[1],
            closingParen=closingParen,
            insideParen=tokens.subList(match[1].index + 1, closingParen.index))
        if semicolon:
            if closingParen.index + 1 < len(tokens) and tokens[closingParen.index + 1].spelling == ';':
                result['semicolon'] = tokens[closingParen.index + 1]
            elif closingParen.index + 2 < len(tokens) and \
                    tokens[closingParen.index + 1].kind == codeprocessingtokens.KIND_WHITESPACE and \
                    tokens[closingParen.index + 2].spelling == ";":
                result['semicolon'] = tokens[closingParen.index + 2]
            else:
                raise Exception("Missing semicolon after macro invocation", result)
        yield result
