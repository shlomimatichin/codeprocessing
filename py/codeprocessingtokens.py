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
_OPENS_TEMPLATE = dict(_OPENS)
_OPENS_TEMPLATE["<"] = ">"
_CLOSES = {y: x for x, y in _OPENS.items()}
_CLOSES_TEMPLATE = {y: x for x, y in _OPENS_TEMPLATE.items()}


class Token:
    def __repr__(self):
        return '"%s"(%d)' % (self.spelling, self.line)

    def isComment(self):
        return self.kind == KIND_C_COMMENT or self.kind == KIND_DIRECTIVE


class Tokens(list):
    @classmethod
    def fromFile(cls, filename, hashMode="directive"):
        contents = open(filename).read()
        result = cls.fromContents(contents, hashMode=hashMode)
        result.filename = filename
        for token in result:
            token.filename = filename
        return result

    @classmethod
    def fromContents(cls, contents, hashMode="directive"):
        assert hashMode in ['directive', 'comment', 'special']
        tokens = codeprocessingnative.tokenizer(contents, hashMode)
        return cls(cls._convertNativeTokens(tokens))

    def findAllSpelling(self, spelling):
        #for loop implemented as while to consider list edited inside loop
        index = 0
        while index < len(self):
            if self[index].spelling == spelling:
                yield self[index]
            index += 1

    def findAllSpellings(self, spellings):
        for token in self.findAllSpelling(spellings[0]):
            index = self.index(token)
            result = self.matchIgnoreWhitespaces(index, spellings)
            if result is not None:
                yield result

    def matchIgnoreWhitespaces(self, startIndex, spellings):
        notFound = list(spellings)
        last = startIndex
        while last < len(self) and len(notFound) > 0:
            candidate = self[last]
            if candidate.kind != KIND_WHITESPACE:
                if notFound[0] is None:
                    notFound.pop(0)
                elif candidate.spelling == notFound[0]:
                    notFound.pop(0)
                else:
                    return None
            last += 1
        if len(notFound) > 0:
            return None
        return self.subList(startIndex, last)

    def firstTokenOnLine(self, number):
        for token in self:
            if token.line == number:
                return token
        raise Exception("Line %d not found in %s" % (
            number, getattr(self[0], 'filename', 'unknown filename')))

    def closingParen(self, token, template=False):
        stack = [token]
        opens = _OPENS_TEMPLATE if template else _OPENS
        closes = _CLOSES_TEMPLATE if template else _CLOSES
        assert token.spelling in opens
        for another in self[self.index(token) + 1:]:
            if another.spelling in opens:
                stack.append(another)
            elif another.spelling in closes:
                popped = stack.pop()
                if popped.spelling != closes[another.spelling]:
                    raise Exception("Incoherent parnethesis: opens %s closes %s" % (popped, another))
                if len(stack) == 0:
                    return another
        raise Exception("Incoherent parenthesis: no close for %s" % (token,))

    def findSemicolon(self, first, semicolon=';'):
        if isinstance(first, Token):
            assert self[first.index] is first
        else:
            first = self[first]
        candidate = self.index(first)
        while candidate < len(self) and self[candidate].spelling != semicolon:
            token = self[candidate]
            if token.spelling in ["[", "(", "{"]:
                candidate = self.index(self.closingParen(token))
            candidate += 1
        if candidate == len(self):
            raise Exception("Semicolon (%s) was not found, when looking from %s:%d" % (
                semicolon, first.filename, first.line))
        assert self[candidate].spelling == ';'
        return self[candidate]

    def dropWhitespaces(self):
        result = Tokens([t for t in self if t.kind != KIND_WHITESPACE])
        if hasattr(self, 'filename'):
            result.filename = self.filename
        return result

    def subList(self, first, lastOrCiel):
        if isinstance(lastOrCiel, Token):
            ceil = self.index(lastOrCiel) + 1
        else:
            assert isinstance(lastOrCiel, int)
            ceil = lastOrCiel
        if isinstance(first, Token):
            firstIndex = self.index(first)
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
        tokenIndex = self.index(token)
        what = self._toTokens(what, followingToken=token,
                              preceedingToken=self[tokenIndex - 1] if tokenIndex > 0 else None)
        for t in reversed(what):
            self.insert(tokenIndex, t)
        self._fix(tokenIndex)

    def replaceBetweenTokens(self, first, last, what):
        if isinstance(first, int):
            assert first < len(self)
            first = self[first]
        if isinstance(last, int):
            assert last < len(self)
            last = self[last]
        firstIndex = self.index(first)
        lastIndex = self.index(last)
        assert firstIndex <= lastIndex
        del self[firstIndex: lastIndex + 1]
        self[firstIndex].index = firstIndex
        self.insertBeforeToken(firstIndex, what)

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
