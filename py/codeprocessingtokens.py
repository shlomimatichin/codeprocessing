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


class Token:
    def __repr__(self):
        return '"%s"(%d)' % (self.spelling, self.line)

    def isComment(self):
        return self.kind == KIND_C_COMMENT or self.kind == KIND_DIRECTIVE


class Tokens(list):
    @classmethod
    def fromFile(cls, filename):
        contents = open(filename).read()
        result = cls.fromContents(contents)
        result.filename = filename
        for token in result:
            token.filename = filename
        return result

    @classmethod
    def fromContents(cls, contents):
        tokens = codeprocessingnative.tokenizer(contents)
        return cls(cls._convertNativeTokens(tokens))

    def findAllSpelling(self, spelling):
        for token in self:
            if token.spelling == spelling:
                yield token

    def findAllSpellings(self, *spellings):
        for index in xrange(len(self)):
            found = True
            for j in xrange(len(spellings)):
                if self[index + j].spelling != spellings[j]:
                    found = False
                    break
            if found:
                yield self[index: index + len(spellings)]

    def firstTokenOnLine(self, number):
        for token in self:
            if token.line == number:
                return token
        raise Exception("Line %d not found in %s" % (
            number, getattr(self[0], 'filename', 'unknown filename')))

    def closingParen(self, token):
        offset = self[0].index
        assert self[token.index - offset] is token
        assert token.spelling in ["[", "(", "{"]
        stack = [token]
        for another in self[token.index + 1:]:
            if another.spelling in _OPENS:
                stack.append(another)
            elif another.spelling in _CLOSES:
                popped = stack.pop()
                if popped.spelling != _CLOSES[another.spelling]:
                    raise Exception("Incoherent parnethesis: opens %s closes %s" % (popped, another))
                if len(stack) == 0:
                    return another

    def subList(self, first, lastOrCiel):
        offset = self[0].index
        if isinstance(lastOrCiel, Token):
            assert self[lastOrCiel.index - offset] is lastOrCiel
            ceil = lastOrCiel.index - offset + 1
        else:
            assert isinstance(lastOrCiel, int)
            ceil = lastOrCiel
        if isinstance(first, Token):
            assert self[first.index - offset] is first
            firstIndex = first.index - offset
        else:
            assert isinstance(first, int)
            firstIndex = first
        result = Tokens(self[firstIndex: ceil])
        if hasattr(self, 'filename'):
            result.filename = self.filename
        return result

    def joinSpellings(self, seperator=" "):
        return seperator.join([t.spelling for t in self])

    def split(self, seperator=","):
        if len(self) == 0:
            return []
        parts = [[]]
        for token in self:
            if token.spelling == seperator:
                parts.append([])
            else:
                parts[-1].append(token)
        return [self.subList(p[0], p[-1]) for p in parts]

    @classmethod
    def _convertNativeTokens(cls, tokens):
        return [cls._convertNativeToken(native, index) for index, native in enumerate(tokens)]

    @classmethod
    def _convertNativeToken(cls, token, index):
        result = Token()
        result.spelling = token[0]
        result.kind = token[1]
        assert result.kind in _KNOWN_KINDS
        result.offset = token[2]
        result.line = token[3]
        result.index = index
        return result
