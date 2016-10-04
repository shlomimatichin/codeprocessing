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
import tarfile
import pprint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
parser = argparse.ArgumentParser()
parser.add_argument("--configurationFile", nargs="+", default=[])
parser.add_argument("--dataFile", default="amatureguard.dat")
cmdSubparsers = parser.add_subparsers(dest='cmd')
scanCmd = cmdSubparsers.add_parser('scan')
scanCmd.add_argument("dirs", nargs="+", default=["."])
scanCmd.add_argument("--assumeObjectiveCsetPrefix", action='store_true')
obfuscateCmd = cmdSubparsers.add_parser('obfuscate')
obfuscateCmd.add_argument("dirs", nargs="+", default=["."])
obfuscateCmd.add_argument("--comment")
obfuscateCmd.add_argument("--fixedMacroComment", action='store_true')
obfuscateCmd.add_argument("--restoreTar")
obfuscateCmd.add_argument("--keepObjectiveCinitPrefix", action='store_true')
obfuscateCmd.add_argument("--keepObjectiveCsetPrefix", action='store_true')
createConfigCmd = cmdSubparsers.add_parser('createConfig')
createConfigCmd.add_argument("dirs", nargs="+")
createConfigCmd.add_argument("--match", nargs="+", default=[".."])
createConfigCmd.add_argument("--mustNotMatch", nargs="+", default=[])
createConfigCmd.add_argument("--output", required=True)
createConfigCmd.add_argument("--guessObjectiveCSetters", action="store_true")
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
            old = oldContents[i].strip().split('/*')[0]
            newContents[i] = newContents[i] + " " + comment + old
    return "\n".join(newContents)


def fixPreprocessorMacros(afterObfuscation, replaces):
    relevantPragma = re.compile(r"#\s*(define|undef|if|pragma\s+mark)")
    tokens = codeprocessingtokens.Tokens.fromContents(afterObfuscation)
    for token in tokens:
        if token.kind != codeprocessingtokens.KIND_DIRECTIVE:
            continue
        if relevantPragma.match(token.spelling) is None:
            continue
        directiveTokens = codeprocessingtokens.Tokens.fromContents(token.spelling, hashMode="special")
        for directiveToken in replacableidentifiers.replacableIdentifiers(directiveTokens):
            if directiveToken.kind != codeprocessingtokens.KIND_IDENTIFIER:
                continue
            if directiveToken.spelling in replaces:
                directiveToken.spelling = meaninglessidentifier.meaninglessIdentifier(
                    directiveToken.spelling, replaces[directiveToken.spelling])
        spellingBefore = token.spelling
        token.spelling = directiveTokens.joinSpellings()
        if args.fixedMacroComment and spellingBefore != token.spelling:
            token.spelling = token.spelling + '\n//' + '\n//'.join([t.rstrip('\\') for t in spellingBefore.split('\n')])
    return tokens.joinSpellings()


def tokenMatches(token, matchers, mustNotMatchers):
    for matcher in matchers:
        if matcher.match(token):
            for mustNotMatcher in mustNotMatchers:
                if mustNotMatcher.match(token):
                    return False
            return True
    return False


def allProperties(tokens):
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


SETTER = re.compile("set[A-Z]")


def setterToProperty(spelling):
    assert SETTER.match(spelling) is not None
    return spelling[3].lower() + spelling[4:]


if hasattr(args, 'keepObjectiveCinitPrefix') and args.keepObjectiveCinitPrefix:
    meaninglessidentifier.OBJECTIVE_C_KEEP_INIT_PREFIX = True
for filename in args.configurationFile:
    with open(filename) as f:
        exec(f.read())
dataFile = datafile.DataFile(args.dataFile, dict(replaces={}))
data = dataFile.data()
if args.cmd == 'scan':
    replaces = data['replaces']
    nextAvailable = max([0] + list(replaces.values())) + 1
    for filename in walk.allSourceCodeFiles(args.dirs):
        tokens = codeprocessingtokens.Tokens.fromFile(filename)
        for token in replacableidentifiers.replacableIdentifiers(tokens):
            spelling = token.spelling
            if args.assumeObjectiveCsetPrefix:
                if SETTER.match(spelling) is not None:
                    spelling = setterToProperty(spelling)
            if spelling not in replaces:
                replaces[spelling] = nextAvailable
                logging.info("New identifier found '%(identifier)s':%(id)s", dict(
                    identifier=spelling, id=nextAvailable))
                nextAvailable += 1
    data['replaces'] = replaces
elif args.cmd == 'obfuscate':
    found = {}
    replaces = data['replaces']
    nextAvailable = max([0] + list(replaces.values())) + 1
    tar = None
    if args.restoreTar:
        tar = tarfile.open(args.restoreTar, "w")
    for filename in walk.allSourceCodeFiles(args.dirs):
        tokens = codeprocessingtokens.Tokens.fromFile(filename)
        for token in replacableidentifiers.replacableIdentifiers(tokens):
            spelling = token.spelling
            if args.keepObjectiveCsetPrefix and SETTER.match(spelling) is not None:
                property = setterToProperty(spelling)
                if property not in replaces:
                    raise Exception("Token '%s' (property '%s') missing from scan! %s:%d" % (
                        spelling, property, token.filename, token.line))
                identifier = meaninglessidentifier.meaninglessIdentifier(property, replaces[property])
                token.spelling = "set" + identifier[0].upper() + identifier[1:]
            else:
                if spelling not in replaces:
                    raise Exception("Token '%s' missing from scan! %s:%d" % (
                        spelling, token.filename, token.line))
                token.spelling = meaninglessidentifier.meaninglessIdentifier(spelling, replaces[spelling])
        newContents = tokens.joinSpellings()
        newContents = annotateWithComments(newContents, filename, args.comment)
        newContents = fixPreprocessorMacros(newContents, replaces)
        if tar is not None:
            tar.add(filename)
        with open(filename, "w") as f:
            f.write(newContents)
    if tar is not None:
        tar.close()
elif args.cmd == 'createConfig':
    matchers = [re.compile(m) for m in args.match]
    mustNotMatchers = [re.compile(m) for m in args.mustNotMatch]
    found = set()
    for filename in walk.allSourceCodeFiles(args.dirs):
        logging.info("Processing %(filename)s", dict(filename=filename))
        tokens = codeprocessingtokens.Tokens.fromFile(filename)
        for token in replacableidentifiers.replacableIdentifiers(tokens):
            if tokenMatches(token.spelling, matchers, mustNotMatchers):
                found.add(token.spelling)
        if args.guessObjectiveCSetters:
            for property in allProperties(tokens):
                found.add("set" + property[0].upper() + property[1:])
    with open(args.output, "w") as f:
        f.write('replacableidentifiers.KEEP = replacableidentifiers.KEEP.union(\n')
        f.write(pprint.pformat(sorted(found)))
        f.write(')\n')
else:
    raise Exception("Unknown command %s" % args.cmd)
dataFile.saveIfChanged(data)
