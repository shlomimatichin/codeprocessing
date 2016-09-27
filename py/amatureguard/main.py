#!/usr/bin/python
import argparse
import logging
from amatureguard import walk
import codeprocessingtokens
import codeprocessingtools
from amatureguard import replacableidentifiers
from amatureguard import datafile
from amatureguard import meaninglessidentifier
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
parser = argparse.ArgumentParser()
parser.add_argument("--configurationFile", default="amatureguard.conf")
parser.add_argument("--dataFile", default="amatureguard.dat")
cmdSubparsers = parser.add_subparsers(dest='cmd')
scanCmd = cmdSubparsers.add_parser('scan')
scanCmd.add_argument("dirs", nargs="+", default=["."])
obfuscateCmd = cmdSubparsers.add_parser('obfuscate')
obfuscateCmd.add_argument("dirs", nargs="+", default=["."])
obfuscateCmd.add_argument("--comment")
obfuscateCmd.add_argument("--fixedMacroComment", action='store_true')
args = parser.parse_args()


def annotateWithComments(afterObfuscation, filename, comment):
    if not comment:
        return afterObfuscation
    newContents = afterObfuscation.split("\n")
    with open(filename) as f:
        oldContents = f.read().split("\n")
    assert len(newContents) == len(oldContents), "new %d old %d %s" % (len(newContents), len(oldContents), filename)
    for i in xrange(len(newContents)):
        if newContents[i] != oldContents[i]:
            newContents[i] = newContents[i] + " " + comment + oldContents[i].strip()
    return "\n".join(newContents)


def fixPreprocessorMacros(afterObfuscation, replaces):
    tokens = codeprocessingtokens.Tokens.fromContents(afterObfuscation)
    for token in tokens:
        if token.kind != codeprocessingtokens.KIND_DIRECTIVE:
            continue
        if not token.spelling.startswith("#define"):
            continue
        directiveTokens = codeprocessingtokens.Tokens.fromContents(token.spelling, hashMode="special")
        for directiveToken in replacableidentifiers.replacableIdentifiers(directiveTokens):
            if directiveToken.kind != codeprocessingtokens.KIND_IDENTIFIER:
                continue
            if directiveToken.spelling in replaces:
                directiveToken.spelling = meaninglessidentifier.meaninglessIdentifier(
                    replaces[directiveToken.spelling])
        spellingBefore = token.spelling
        token.spelling = directiveTokens.joinSpellings()
        if args.fixedMacroComment and spellingBefore != token.spelling:
            token.spelling = token.spelling + '\n//' + '//'.join(spellingBefore.split('\n'))
    return tokens.joinSpellings()


dataFile = datafile.DataFile(args.dataFile, dict(replaces={}))
data = dataFile.data()
if args.cmd == 'scan':
    replaces = data['replaces']
    nextAvailable = max([0] + list(replaces.values())) + 1
    for filename in walk.allSourceCodeFiles(args.dirs):
        tokens = codeprocessingtokens.Tokens.fromFile(filename)
        for token in replacableidentifiers.replacableIdentifiers(tokens):
            if token.spelling not in replaces:
                replaces[token.spelling] = nextAvailable
                logging.info("New identifier found '%(identifier)s':%(id)s", dict(
                    identifier=token.spelling, id=nextAvailable))
                nextAvailable += 1
    data['replaces'] = replaces
elif args.cmd == 'obfuscate':
    found = {}
    replaces = data['replaces']
    nextAvailable = max([0] + list(replaces.values())) + 1
    for filename in walk.allSourceCodeFiles(args.dirs):
        tokens = codeprocessingtokens.Tokens.fromFile(filename)
        for token in replacableidentifiers.replacableIdentifiers(tokens):
            if token.spelling not in replaces:
                raise Exception("Token '%s' missing from scan! %s:%d" % (
                    token.spelling, token.filename, token.line))
            token.spelling = meaninglessidentifier.meaninglessIdentifier(replaces[token.spelling])
        newContents = tokens.joinSpellings()
        newContents = annotateWithComments(newContents, filename, args.comment)
        newContents = fixPreprocessorMacros(newContents, replaces)
        with open(filename, "w") as f:
            f.write(newContents)
else:
    raise Exception("Unknown command %s" % args.cmd)
dataFile.saveIfChanged(data)


