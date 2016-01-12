#include <cxxtest/TestSuite.h>

#define ASSERT(x) TS_ASSERT(x)

#include "CodeProcessing/Tokenizer.h"

typedef CodeProcessing::Tokenizer::Token Token;
typedef CodeProcessing::Tokenizer::Type Type;
using namespace CodeProcessing;

class Test_Tokenizer : public CxxTest::TestSuite
{
public:
    struct Expected {
        Tokenizer::Token token;
        unsigned line;
    };

    void verify(Tokenizer & tested, std::string contents, std::vector<Expected> expected)
    {
        auto nextExpected = expected.begin();
        unsigned i = 0;
        while (true) {
            try {
                auto token = tested.next();
                TSM_ASSERT_DIFFERS(i, nextExpected, expected.end());
                TSM_ASSERT_EQUALS(i, token.spelling, nextExpected->token.spelling);
                TSM_ASSERT_EQUALS(i, token.type, nextExpected->token.type);
                TSM_ASSERT_EQUALS(i, contents.substr(token.beginsOffset, token.spelling.size()), token.spelling);
                TSM_ASSERT_EQUALS(i, tested.offsetToLine(token.beginsOffset), nextExpected->line);
                ++ nextExpected;
                ++ i;
            } catch (Tokenizer::Done) {
                TS_ASSERT(nextExpected == expected.end());
                break;
            }
        }
    }

    void test_SimpleSanity()
    {
        std::string original(
            "class Name {\n"
            " public:\n"
            " void it(int b) {\n"
            "  TRACE_INFO(\"Hello \" << 7);\n"
            "  //comment 1\n"
            " /* comment 2 */\n"
            "}};");
        Tokenizer tested(original);
        std::vector<Expected> expected = {
            Expected({Token({Type::IDENTIFIER, 0, "class"}), 1}),
            Expected({Token({Type::IDENTIFIER, 0, "Name"}), 1}),
            Expected({Token({Type::SPECIAL, 0, "{"}), 1}),
            Expected({Token({Type::IDENTIFIER, 0, "public"}), 2}),
            Expected({Token({Type::SPECIAL, 0, ":"}), 2}),
            Expected({Token({Type::IDENTIFIER, 0, "void"}), 3}),
            Expected({Token({Type::IDENTIFIER, 0, "it"}), 3}),
            Expected({Token({Type::SPECIAL, 0, "("}), 3}),
            Expected({Token({Type::IDENTIFIER, 0, "int"}), 3}),
            Expected({Token({Type::IDENTIFIER, 0, "b"}), 3}),
            Expected({Token({Type::SPECIAL, 0, ")"}), 3}),
            Expected({Token({Type::SPECIAL, 0, "{"}), 3}),
            Expected({Token({Type::IDENTIFIER, 0, "TRACE_INFO"}), 4}),
            Expected({Token({Type::SPECIAL, 0, "("}), 4}),
            Expected({Token({Type::DOUBLE_QUOTE, 0, "\"Hello \""}), 4}),
            Expected({Token({Type::SPECIAL, 0, "<<"}), 4}),
            Expected({Token({Type::IDENTIFIER, 0, "7"}), 4}),
            Expected({Token({Type::SPECIAL, 0, ")"}), 4}),
            Expected({Token({Type::SPECIAL, 0, ";"}), 4}),
            Expected({Token({Type::C_COMMENT, 0, "//comment 1\n"}), 5}),
            Expected({Token({Type::C_COMMENT, 0, "/* comment 2 */"}), 6}),
            Expected({Token({Type::SPECIAL, 0, "}"}), 7}),
            Expected({Token({Type::SPECIAL, 0, "}"}), 7}),
            Expected({Token({Type::SPECIAL, 0, ";"}), 7}),
        };
        verify(tested, original, expected);
    }
};
