import unittest
import codeprocessingtokens
import tempfile


class Test(unittest.TestCase):
    def createTested(self, content):
        t = tempfile.NamedTemporaryFile()
        t.write(content)
        t.flush()
        tested = codeprocessingtokens.Tokens.fromFile(t.name)
        t.close()
        return tested

    def test_SimpleTestCase(self):
        tested = self.createTested(
            "//hello\n"
            "void a(int b, bool c) { code; }\n")
        self.assertEquals(tested[2].spelling, "a")
        self.assertTrue(tested.closingParen(tested[3]) is tested[9])


if __name__ == '__main__':
    unittest.main()
