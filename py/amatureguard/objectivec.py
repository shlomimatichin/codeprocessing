import re
import codeprocessingtokens
from amatureguard import meaninglessidentifier
from amatureguard import replacableidentifiers

SETTER = re.compile("set[A-Z]")


class ObjectiveC:
    def __init__(self, replaces):
        self._replaces = replaces
        self._properties = {}

    @classmethod
    def setterToProperty(cls, spelling):
        assert SETTER.match(spelling) is not None
        return spelling[3].lower() + spelling[4:]

    @classmethod
    def setterOfProperty(cls, spelling):
        return "set" + spelling[0].upper() + spelling[1:]

    def obfuscate(self, token):
        return self._obfuscateSetterFunction(token) or self._obfuscateObjectiveCPrivateProperty(token)

    def scan(self, tokens):
        filename = tokens[0].filename
        for prop in self.allProperties(tokens):
            self._properties.setdefault(prop, []).append(filename)

    @classmethod
    def allProperties(cls, tokens):
        for match in tokens.findAllSpellings(["@", "property"]):
            semicolon = tokens.findSemicolon(match[0])
            declaration = tokens.subList(match[0], semicolon)
            spellings = [t.spelling for t in declaration]
            if 'readonly' in spellings:
                continue
            assert 'setter' not in spellings, "Not implemented"
            theRest = declaration.dropWhitespaces()
            assert theRest[0].spelling == "@"
            assert theRest[1].spelling == "property"
            del theRest[:2]
            for token in list(theRest):
                if token.kind == codeprocessingtokens.KIND_C_COMMENT:
                    theRest.remove(token)
                elif token.spelling in ["__kindof", '_Nonnull', '_Nullable']:
                    theRest.remove(token)
            for multiMatch in theRest.findAllSpellings(["__attribute__", "(", "(", None, ")", ")"]):
                del theRest[theRest.index(multiMatch[0]): theRest.index(multiMatch[-1]) + 1]
            try:
                if theRest[0].spelling == "(":
                    closing = theRest.closingParen(theRest[0])
                    del theRest[: theRest.index(closing) + 1]
                assert theRest[0].kind == codeprocessingtokens.KIND_IDENTIFIER, "%s: %s" % (declaration, theRest[0])
                theRest.pop(0)
                if theRest[0].spelling == "<":
                    closing = theRest.closingParen(theRest[0], template=True)
                    del theRest[: theRest.index(closing) + 1]
                while theRest[0].kind == codeprocessingtokens.KIND_SPECIAL:
                    theRest.pop(0)
                yield theRest[0].spelling
            except:
                print "While parsing property at %s:%d" % (match[0].filename, match[0].line)
                raise

    def _obfuscateSetterFunction(self, token):
        spelling = token.spelling
        if SETTER.match(spelling) is None:
            return False
        property = self.setterToProperty(spelling)
        if property not in self._replaces:
            raise Exception("Token '%s' (property '%s') missing from scan! %s:%d" % (
                spelling, property, token.filename, token.line))
        identifier = meaninglessidentifier.meaninglessIdentifier(property, self._replaces[property])
        token.spelling = self.setterOfProperty(identifier)
        return True

    def _obfuscateObjectiveCPrivateProperty(self, token):
        spelling = token.spelling
        if not spelling.startswith("_"):
            return False
        property = spelling[1:]
        if property not in self._properties:
            return False
        filename = token.filename
        if filename.endswith(".m"):
            headerFilename = filename[:-len(".m")] + ".h"
        else:
            return False
        if headerFilename not in self._properties[property]:
            return False
        if not replacableidentifiers.replacableSpelling(property):
            return True
        token.spelling = "_" + meaninglessidentifier.meaninglessIdentifier(property, self._replaces[property])
        return True
