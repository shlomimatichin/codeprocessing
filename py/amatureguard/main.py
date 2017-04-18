#!/usr/bin/python
import argparse
import logging
from amatureguard import walk
import codeprocessingtokens
import codeprocessingtools
from amatureguard import replacableidentifiers
from amatureguard import datafile
from amatureguard import meaninglessidentifier
from amatureguard import directives
from amatureguard import objectivec
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
obfuscateCmd = cmdSubparsers.add_parser('obfuscateRegex')
obfuscateCmd.add_argument("dirs", nargs="+", default=["."])
obfuscateCmd.add_argument("--regex", nargs="+", required=True)
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


def replaceASingleRegex(contents, replaces, regexes):
    for regex in regexes:
        for match in re.finditer(regex, contents):
            candidate = match.group(0)
            if candidate in replaces:
                identifier = meaninglessidentifier.meaninglessIdentifier(candidate, replaces[candidate])
                return contents[:match.start()] + identifier + contents[match.end():]
    return contents


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
        with directives.fileDirectives(tokens):
            for token in replacableidentifiers.replacableIdentifiers(tokens):
                spelling = token.spelling
                if args.assumeObjectiveCsetPrefix:
                    if objectivec.SETTER.match(spelling) is not None:
                        spelling = objectivec.ObjectiveC.setterToProperty(spelling)
                if spelling not in replaces:
                    replaces[spelling] = nextAvailable
                    logging.info("New identifier found '%(identifier)s':%(id)s", dict(
                        identifier=spelling, id=nextAvailable))
                    nextAvailable += 1
    data['replaces'] = replaces
elif args.cmd == 'obfuscate':
    replaces = data['replaces']
    tar = None
    if args.restoreTar:
        tar = tarfile.open(args.restoreTar, "w")

    def obfuscateNormally(token):
        spelling = token.spelling
        if spelling not in replaces:
            raise Exception("Token '%s' missing from scan! %s:%d" % (
                spelling, token.filename, token.line))
        token.spelling = meaninglessidentifier.meaninglessIdentifier(spelling, replaces[spelling])
        return True

    obfuscators = [obfuscateNormally]
    scanners = []
    if args.keepObjectiveCinitPrefix:
        objectiveC = objectivec.ObjectiveC(replaces)
        obfuscators = [objectiveC.obfuscate] + obfuscators
        scanners.append(objectiveC.scan)
    if len(scanners) > 0:
        for filename in walk.allSourceCodeFiles(args.dirs):
            tokens = codeprocessingtokens.Tokens.fromFile(filename)
            with directives.fileDirectives(tokens):
                for scanner in scanners:
                    scanner(tokens)
    for filename in walk.allSourceCodeFiles(args.dirs):
        tokens = codeprocessingtokens.Tokens.fromFile(filename)
        with directives.fileDirectives(tokens):
            for token in replacableidentifiers.replacableIdentifiers(tokens):
                for obfuscator in obfuscators:
                    if obfuscator(token):
                        break
        newContents = tokens.joinSpellings()
        newContents = annotateWithComments(newContents, filename, args.comment)
        newContents = fixPreprocessorMacros(newContents, replaces)
        if tar is not None:
            tar.add(filename)
        with open(filename, "w") as f:
            f.write(newContents)
    if tar is not None:
        tar.close()
elif args.cmd == 'obfuscateRegex':
    replaces = data['replaces']
    for filename in walk.allSourceCodeFiles(args.dirs):
        with open(filename) as f:
            contents = f.read()
        contentsBefore = ""
        while contents != contentsBefore:
            contentsBefore = contents
            contents = replaceASingleRegex(contentsBefore, replaces, args.regex)
        with open(filename, "w") as f:
            f.write(contents)
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
            for property in objectivec.ObjectiveC.allProperties(tokens):
                found.add("set" + property[0].upper() + property[1:])
    with open(args.output, "w") as f:
        f.write('replacableidentifiers.KEEP = replacableidentifiers.KEEP.union(\n')
        f.write(pprint.pformat(sorted(found)))
        f.write(')\n')
else:
    raise Exception("Unknown command %s" % args.cmd)
dataFile.saveIfChanged(data)
