import collections
import codeprocessingnative

KIND_SPECIAL = 0
KIND_IDENTIFIER = 1
KIND_SINGLE_QUOTE = 2
KIND_DOUBLE_QUOTE = 3
KIND_C_COMMENT = 4
KIND_DIRECTIVE = 5
_KNOWN_KINDS = set([
    KIND_SPECIAL, KIND_IDENTIFIER, KIND_SINGLE_QUOTE,
    KIND_DOUBLE_QUOTE, KIND_C_COMMENT, KIND_DIRECTIVE,
])
_OPENS = {"{": "}", "(": ")", "[": "]"}
_CLOSES = {y: x for x, y in _OPENS.iteritems()}


class Token: pass


class Tokens(list):
    @classmethod
    def fromFile(cls, filename):
        content = open(filename).read()
        tokens = codeprocessingnative.tokenizer(content)
        result = cls(cls._convertNativeTokens(tokens, filename))
        result.filename = filename
        return result

    def findAllSpelling(self, spelling):
        for token in self:
            if token.spelling == spelling:
                yield token

    def closingParen(self, token):
        assert self[token.index] is token
        assert token.spelling in ["[", "(", "{"]
        stack = [token]
        for another in self[token.index + 1:]:
            if another.spelling in _OPENS:
                stack.append(another.spelling)
            elif another.spelling in _CLOSES:
                popped = stack.pop()
                if popped.spelling != _CLOSES[another.spelling]:
                    raise Exception("Incoherent parnethesis: opens %s closes %s" % (popped, another))
                if len(stack) == 0:
                    return another

    @classmethod
    def _convertNativeTokens(cls, tokens, filename):
        return [cls._convertNativeToken(native, index, filename) for index, native in enumerate(tokens)]

    @classmethod
    def _convertNativeToken(cls, token, index, filename):
        result = Token()
        result.filename = filename
        result.spelling = token[0]
        result.kind = token[1]
        assert result.kind in _KNOWN_KINDS
        result.offset = token[2]
        result.line = token[3]
        result.index = index
        return result
