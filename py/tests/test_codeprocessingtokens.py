import unittest
import codeprocessingtokens
import tempfile
import pprint


class Test(unittest.TestCase):
    def createTested(self, content):
        t = tempfile.NamedTemporaryFile()
        t.write(content)
        t.flush()
        tested = codeprocessingtokens.Tokens.fromFile(t.name)
        t.close()
        return tested

    def serialize(self, tokens):
        return pprint.pformat([(t.spelling, t.index, t.kind, t.line, t.offset) for t in tokens])

    def test_SimpleTestCase(self):
        tested = self.createTested(
            "//hello\n"
            "void a(int b, bool c) { int i; code; }\n")
        self.assertEquals(tested[4].spelling, "a")
        self.assertTrue(tested.closingParen(tested[5]) is tested[14])
        for i, token in enumerate(tested.findAllSpelling("int")):
            if i == 0:
                self.assertTrue(token is tested[6])
            elif i == 1:
                self.assertTrue(token is tested[18])
            else:
                self.assertTrue(False)
        self.assertTrue(tested.firstTokenOnLine(1) is tested[0])
        self.assertTrue(tested.firstTokenOnLine(2) is tested[2])
        self.assertEquals(tested.firstTokenOnLine(2).spelling, "void")

    def test_FindAllSpellings(self):
        tested = codeprocessingtokens.Tokens.fromContents("""a b c d e f a b c d z z a b c""")
        for i, result in enumerate(tested.findAllSpellings(["a", "b", "c"])):
            if i == 0:
                self.assertEquals(len(result), 3)
                self.assertTrue(result[0] is tested[0])
                self.assertTrue(result[1] is tested[2])
                self.assertTrue(result[2] is tested[4])
            elif i == 1:
                self.assertEquals(len(result), 3)
                self.assertTrue(result[0] is tested[12])
                self.assertTrue(result[1] is tested[14])
                self.assertTrue(result[2] is tested[16])
            elif i == 2:
                self.assertEquals(len(result), 3)
                self.assertTrue(result[0] is tested[24])
                self.assertTrue(result[1] is tested[26])
                self.assertTrue(result[2] is tested[28])
            else:
                self.assertTrue(False)

    def test_FindAllSpellingsWithWhitespaces(self):
        tested = codeprocessingtokens.Tokens.fromContents("""a b c d e f a b c d z z a b c""")
        for i, result in enumerate(tested.findAllSpellings(["a", "b", "c"], returnWhitespaces=True)):
            if i == 0:
                self.assertEquals(len(result), 5)
                self.assertTrue(result[0] is tested[0])
                self.assertTrue(result[2] is tested[2])
                self.assertTrue(result[4] is tested[4])
            elif i == 1:
                self.assertEquals(len(result), 5)
                self.assertTrue(result[0] is tested[12])
                self.assertTrue(result[2] is tested[14])
                self.assertTrue(result[4] is tested[16])
            elif i == 2:
                self.assertEquals(len(result), 5)
                self.assertTrue(result[0] is tested[24])
                self.assertTrue(result[2] is tested[26])
                self.assertTrue(result[4] is tested[28])
            else:
                self.assertTrue(False)

    def test_Fix(self):
        tested = self.createTested(
            "//hello\n"
            "void a(int b, bool c) { int i; code; }\n")
        beforeFix = self.serialize(tested)
        tested._fix(0)
        afterFix = self.serialize(tested)
        self.assertEquals(beforeFix, afterFix)

        self.assertEquals(tested[2].spelling, "void")
        tested.insertBeforeToken(tested[2], "static inline")
        self.assertEquals(self.serialize(tested), self.serialize(codeprocessingtokens.Tokens.fromContents(
            "//hello\nstatic inline void a(int b, bool c) { int i; code; }\n")))

        self.assertEquals(tested[10].spelling, "int")
        self.assertEquals(tested[12].spelling, "b")
        tested.replaceBetweenTokens(tested[10], tested[12], "float B")
        self.assertEquals(self.serialize(tested), self.serialize(codeprocessingtokens.Tokens.fromContents(
            "//hello\nstatic inline void a(float B, bool c) { int i; code; }\n")))

        self.assertEquals(tested.joinSpellings(),
                          "//hello\nstatic inline void a(float B, bool c) { int i; code; }\n")


if __name__ == '__main__':
    unittest.main()
