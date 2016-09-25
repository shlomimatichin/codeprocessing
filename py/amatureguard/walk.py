import os


def allSourceCodeFiles(directory, ignoreDirs=[], ignoreBasenames=[]):
    CODE_EXTENSIONS = set([".h", ".H", ".hpp", ".HPP", ".hxx", ".HXX", ".cpp", ".CPP", ".cxx", ".CXX", ".m", ".mm"])
    result = []
    for root, dirs, files in os.walk(directory):
        for dirName in ignoreDirs:
            if dirName in dirs:
                dirs.remove(dirName)
        for basename in files:
            if not os.path.splitext(basename)[1] in CODE_EXTENSIONS:
                continue
            if basename in ignoreBasenames:
                continue
            result.append(os.path.join(root, basename))
    result.sort()
    return result
