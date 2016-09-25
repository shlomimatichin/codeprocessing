#!/usr/bin/python
import argparse
import logging
from amatureguard import walk
import codeprocessingtokens

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
parser = argparse.ArgumentParser()
parser.add_argument("--configurationFile", default="amatureguard.conf")
args = parser.parse_args()

KEYWORDS = [
    'void', 'int', 'unsigned', 'char', 'double', 'float', 'long', 'bool', 'typedef',
    'uint', 'uint8_t', 'int8_t', 'uint16_t', 'int16_t', 'uint32_t', 'int32_t', 'uint64_t', 'int64_t',
    'time_t', 'size_t', 'ssize_t', 'offset_t',
    'public', 'private', 'protected', 'class', 'template', 'typename', 'namespace', 'operator',
    'override', 'virtual', 'static', 'inline', 'volatile', 'static_case', 'reinterpret_case', 'const_cast',
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'return', 'break',
    'nil', 'nullptr', 'this', 'sizeof', 'new', 'delete', 'enum', 'struct', 'class', 'auto',
    'not', 'and', 'or', 'true', 'false',
    'try', 'catch', 'throw',
]
CPP_KEEP = [
    'std::unique_ptr', 'std::string',
]
C_KEEP = [
    'tv_sec', 'tv_usec', 'malloc', 'free', 'main', 'errno',
    'O_APPEND', 'O_CREAT', 'O_RDONLY', 'NULL',
]
OBJECTIVE_C_KEEP = [
    'self', 'selector', 'YES', 'NO', 'BOOL', 'UTF8String', 'Byte', 'Bool',
]
OBJECTIVE_C_EXP = [r"UI[A-Z]", r"NS[A-Z]"]
CUSTOM_KEEP = ["_Ti", "_Tn", ]
KEEP = set(KEYWORDS + CPP_KEEP + C_KEEP + OBJECTIVE_C_KEEP + CUSTOM_KEEP)

found = set()
for filename in walk.allSourceCodeFiles("."):
    tokens = codeprocessingtokens.Tokens.fromFile(filename)
    for token in tokens:
        if token.kind != codeprocessingtokens.KIND_IDENTIFIER:
            continue
        spelling = token.spelling
        if spelling in KEEP:
            continue
        if spelling.startswith("__"):
            continue
        if spelling.startswith('0') or spelling.isdigit():
            continue
        if len(spelling) > 1 and spelling[:-1].isdigit and spelling[-1] in ['u', 'f']:
            continue
        found.add(spelling)

import pprint
pprint.pprint(found)
print len(found)
