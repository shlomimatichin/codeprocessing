import unittest
import codeprocessingtokens
import tempfile
import subprocess
import os


class Test(unittest.TestCase):
    _EXECUTABLE = os.path.join(os.path.dirname(__file__), "..", "removefunctioncalls.py")

    def doOne(self, content):
        t = tempfile.NamedTemporaryFile()
        t.write(content)
        t.flush()
        subprocess.check_call([
            "python", self._EXECUTABLE,
            "--functionName", "NSLog",
            "--replaceInline",
            "--replaceWith", "do{}while(0);",
            t.name])
        t.seek(0)
        output = t.read()
        t.close()
        return output

    def test_SimpleTestCase(self):
        output = self.doOne("""
int main()
{
    printf("Hello world!");
    NSLog("This should be replaced, ", blah, [call me], call(me));
}""")
        self.assertEquals(output,"""
int main()
{
    printf("Hello world!");
    do{}while(0);                                                 
}""")


if __name__ == '__main__':
    unittest.main()
