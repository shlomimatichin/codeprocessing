import collections
import codeprocessingnative

KIND_SPECIAL = 0
KIND_IDENTIFIER = 1
KIND_SINGLE_QUOTE = 2
KIND_DOUBLE_QUOTE = 3
KIND_C_COMMENT = 4
KIND_DIRECTIVE = 5
KIND_WHITESPACE = 6
_KNOWN_KINDS = set([
    KIND_SPECIAL, KIND_IDENTIFIER, KIND_SINGLE_QUOTE,
    KIND_DOUBLE_QUOTE, KIND_C_COMMENT, KIND_DIRECTIVE,
    KIND_WHITESPACE,
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
        #for loop implemented as while to consider list edited inside loop
        index = 0
        while index < len(self):
            if self[index].spelling == spelling:
                yield self[index]
            index += 1

    def findAllSpellings(self, spellings, returnWhitespaces=False):
        for token in self.findAllSpelling(spellings[0]):
            index = token.index
            result = self.matchIgnoreWhitespaces(index, spellings)
            if result is not None:
                if returnWhitespaces:
                    yield result
                else:
                    yield [t for t in result if t.kind != KIND_WHITESPACE]

    def matchIgnoreWhitespaces(self, startIndex, spellings):
        assert self[startIndex].spelling == spellings[0]
        notFound = spellings[1:]
        last = startIndex
        while len(notFound) > 0:
            last += 1
            candidate = self[last]
            if candidate.kind != KIND_WHITESPACE:
                if candidate.spelling == notFound[0]:
                    notFound.pop(0)
                else:
                    return None
        return self[startIndex: last + 1]

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

    def joinSpellings(self, seperator=""):
        return seperator.join([t.spelling for t in self])

    def saveToFile(self, filename):
        with open(filename, "w") as f:
            f.write(self.joinSpellings())

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

    def insertBeforeToken(self, token, what):
        if isinstance(token, int):
            assert token < len(self)
            token = self[token]
        assert self[token.index] is token
        what = self._toTokens(what, followingToken=token,
                              preceedingToken=self[token.index - 1] if token.index > 0 else None)
        for t in reversed(what):
            self.insert(token.index, t)
        self._fix(token.index)

    def replaceBetweenTokens(self, first, last, what):
        if isinstance(first, int):
            assert first < len(self)
            first = self[first]
        assert self[first.index] is first
        if isinstance(last, int):
            assert last < len(self)
            last = self[last]
        assert self[last.index] is last
        assert first.index <= last.index
        del self[first.index: last.index + 1]
        self[first.index].index = first.index
        self.insertBeforeToken(first.index, what)

    def _toTokens(self, what, preceedingToken, followingToken):
        if isinstance(what, str):
            what = self.fromContents(what)
        assert isinstance(what, list)
        for i, t in enumerate(what):
            assert isinstance(t, Token)
        if preceedingToken is not None and preceedingToken.kind == KIND_IDENTIFIER and \
                what[0].kind == KIND_IDENTIFIER:
            what = [self._whitespace()] + what
        if followingToken is not None and followingToken.kind == KIND_IDENTIFIER and \
                what[-1].kind == KIND_IDENTIFIER:
            what = what + [self._whitespace()]
        return what

    def _fix(self, startAt):
        if startAt == 0:
            line = 1
            offset = 0
        else:
            lastToken = self[startAt - 1]
            line = lastToken.line + lastToken.spelling.count('\n')
            offset = lastToken.offset + len(lastToken.spelling)
        for i in xrange(startAt, len(self)):
            token = self[i]
            token.line = line
            token.offset = offset
            token.index = i
            line += token.spelling.count('\n')
            offset += len(token.spelling)

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

    @classmethod
    def _whitespace(cls, spelling=" "):
        result = Token()
        result.spelling = spelling
        result.kind = KIND_WHITESPACE
        result.offset = -1
        result.line = 0
        result.index = -1
        return result
