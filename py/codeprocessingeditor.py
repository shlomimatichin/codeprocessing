import codeprocessingtokens


class Editor:
    def __init__(self, filename):
        self._filename = filename
        self.tokens = codeprocessingtokens.Token.fromFile(filename)
        self._changed = False

    def filename(self):
        return self._filename

    def saveIfChanged(self):
        if not self._changed:
            return
        self._changed = False
        self.tokens.saveToFile(self._filename)

    def insert(self, location, what):
        self.replace(location, location, what)

    def replace(self, starting, ceil, what, assumeReplaced=None):
        with open(self._filename) as f:
            content = f.read()
        if assumeReplaced is not None:
            replacedTokens = codeprocessingtokens.Tokens.fromContents(content[starting: ceil])
            if isinstance(assumeReplaced, str):
                assumeReplaced = codeprocessingtokens.Tokens.fromContents(assumeReplaced)
            replacedText = replacedTokens.joinSpellings(" ")
            assumeReplacedText = " ".join([t.spelling for t in assumeReplaced])
            if replacedText != assumeReplacedText:
                raise Exception("Expected to replace '%s' but found '%s' at '%s'" % (
                    assumeReplacedText, replacedText, self._filename))
        content = content[:starting] + what + content[ceil:]
        with open(self._filename, "w") as f:
            f.write(content)

    def replaceTokens(self, tokens, what):
        if isinstance(tokens, codeprocessingtokens.Token):
            tokens = [tokens]
        self.replace(tokens[0].offset, tokens[-1].offset + len(tokens[-1].spelling), what,
                     assumeReplaced=tokens)
