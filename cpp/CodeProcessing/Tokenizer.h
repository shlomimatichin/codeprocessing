#ifndef __CODE_PROCESSING_TOKENIZER_H__
#define __CODE_PROCESSING_TOKENIZER_H__

#include <list>
#include <string>
#include <stdexcept>
#include <map>

namespace CodeProcessing
{

class Tokenizer
{
public:
    Tokenizer(std::string data) :
        _data(std::move(data)),
        _index(0)
    {
        unsigned line = 1;
        _offsetToLine[0] = line;
        for (unsigned i=0; i < _data.size(); ++ i)
            if (_data[i] == '\n') {
                ++ line;
                _offsetToLine[i+1] = line;
            }
    }

    unsigned offsetToLine(unsigned offset)
    {
        auto after = _offsetToLine.upper_bound(offset);
        if (after == _offsetToLine.end())
            return _offsetToLine.rbegin()->second;
        else
            return after->second - 1;
    }

    enum class Type {
        SPECIAL,
        IDENTIFIER,
        SINGLE_QUOTE,
        DOUBLE_QUOTE,
        C_COMMENT,
        DIRECTIVE,
        WHITESPACE,
    };

    struct Token
    {
        Type        type;
        unsigned    beginsOffset;
        std::string spelling;
    };

    class Done {};

    struct Token next()
    {
        while (true) {
            unsigned beginsOffset = _index;
            if (beginsOffset >= _data.size())
                throw Done();

            char c = _data[_index];
            char next = '\0';
            if (_index < _data.size() - 1)
                next = _data[_index + 1];
            if (wordCharacter(c))
                return Token({Type::IDENTIFIER, beginsOffset, eatIdentifier()});
            else if (c == '\'')
                return Token({Type::SINGLE_QUOTE, beginsOffset, eatQuotes()});
            else if (c == '"')
                return Token({Type::DOUBLE_QUOTE, beginsOffset, eatQuotes()});
            else if (c == '/' and next == '/')
                return Token({Type::C_COMMENT, beginsOffset, eatUntil("\n", true)});
            else if (c == '/' and next == '*')
                return Token({Type::C_COMMENT, beginsOffset, eatUntilAfter("*/")});
            else if (c == '#')
                return Token({Type::DIRECTIVE, beginsOffset, eatUntil("\n", true)});
            else if (c == '<' and next == '<') {
                _index += 2;
                return Token({Type::SPECIAL, beginsOffset, "<<"});
            } else if (c == ':' and next == ':') {
                _index += 2;
                return Token({Type::SPECIAL, beginsOffset, "::"});
            } else if (whitespace(c))
                return Token({Type::WHITESPACE, beginsOffset, eatWhitespace()});
            else {
                ++ _index;
                return Token({Type::SPECIAL, beginsOffset, _data.substr(beginsOffset, 1)});
            }
        }
    }

private:
    std::string                   _data;
    unsigned                      _index;
    std::map<unsigned, unsigned>  _offsetToLine;

    static inline bool digitCharacter(char c)
    {
        return c >= '0' and c <= '9';
    }

    static inline bool alphabeticCharacter(char c)
    {
        return (c >= 'A' and c <= 'Z') or (c >= 'a' and c <= 'z');
    }

    static inline bool wordCharacter(char c)
    {
        return
            alphabeticCharacter(c) or
            digitCharacter(c) or
            c == '_';
    }

    static inline bool whitespace(char c)
    {
        return c == ' ' or c == '\n' or c == '\t';
    }

    std::string eatWhitespace()
    {
        unsigned before = _index;
        while (_index < _data.size() and whitespace(_data[_index]))
            ++ _index;
        return _data.substr(before, _index - before);
    }

    std::string eatUntilAfter(std::string lookFor)
    {
        unsigned before = _index;
        size_t pos = _data.find(lookFor, _index);
        if (pos == std::string::npos) {
            _index = _data.size();
            return "";
        }
        _index = pos + lookFor.size();
        return _data.substr(before, _index - before);
    }

    std::string eatUntil(std::string lookFor, bool backslashEscape)
    {
        unsigned before = _index;
        unsigned nextSearch = before;
        do {
            size_t pos = _data.find(lookFor, nextSearch);
            if (pos == std::string::npos)
                _index = _data.size();
            else {
                _index = pos;
                nextSearch = _index + 1;
            }
        } while (backslashEscape and _index < _data.size() and _index > before and _data[_index - 1] == '\\');
        return _data.substr(before, _index - before);
    }

    std::string eatQuotes()
    {
        char open = _data[_index];
        ASSERT(open == '\'' or open == '"');
        unsigned before = _index;
        ++ _index;
        while (_index < _data.size()) {
            if (_data[_index] == '\\' and _index < _data.size() - 1)
                _index += 2;
            else if (_data[_index] == open) {
                ++ _index;
                return std::string(_data.data() + before, _index - before);
            } else
                ++ _index;
        }
        return _data.substr(before);
    }

    std::string eatIdentifier()
    {
        unsigned before = _index;
        while (_index < _data.size()) {
            if (wordCharacter(_data[_index]))
                ++ _index;
            else
                return std::string(_data.data() + before, _index - before);
        }
        return _data.substr(before);
    }
};

} // namespace CodeProcessing

#endif // __CODE_PROCESSING_TOKENIZER_H__
