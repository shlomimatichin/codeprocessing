import contextlib
from amatureguard import replacableidentifiers
import codeprocessingtokens
import codeprocessingtools
import logging


@contextlib.contextmanager
def fileDirectives(tokens):
    previousKeep = replacableidentifiers.KEEP
    replacableidentifiers.KEEP = set(previousKeep)
    for token in tokens:
        if token.kind != codeprocessingtokens.KIND_C_COMMENT:
            continue
        contents = codeprocessingtools.stripComment(token.spelling).strip()
        if not contents.startswith("AMATURE GUARD:"):
            continue
        directiveTokens = codeprocessingtokens.Tokens.fromContents(contents[len("AMATURE GUARD:"):])
        while len(directiveTokens) > 0:
            matchKeep = directiveTokens.matchIgnoreWhitespaces(0, ["keep", ":"])
            if matchKeep:
                directiveTokens = directiveTokens[len(matchKeep):]
                identifier = None
                keeping = []
                while len(directiveTokens) > 0:
                    identifier = directiveTokens.pop(0)
                    if identifier.kind == codeprocessingtokens.KIND_WHITESPACE:
                        continue
                    if identifier.spelling == ';':
                        break
                    replacableidentifiers.KEEP.add(identifier.spelling)
                    keeping.append(identifier.spelling)
                if identifier.spelling != ';':
                    raise Exception("amature guard 'keep' directive not terminated at %s:%d" % (
                        token.filename, token.line))
                logging.info("amature guard directive keep at %(filename)s/%(line)d. will keep %(keep)s", dict(
                    filename=token.filename, line=token.line, keep=keeping))
            else:
                raise Exception("Unknown amature guard directive '%s' in %s:%d" % (
                    directiveTokens[0].spelling, token.filename, token.line))
    yield
    replacableidentifiers.KEEP = previousKeep
