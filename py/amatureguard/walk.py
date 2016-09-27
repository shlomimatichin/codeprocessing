import os


def allSourceCodeFiles(directories, ignoreDirs=[], ignoreBasenames=[]):
    CODE_EXTENSIONS = set([".h", ".H", ".hpp", ".HPP", ".hxx", ".HXX", ".cpp", ".CPP", ".cxx", ".CXX", ".m", ".mm"])
    result = set()
    for directory in directories:
        if os.path.isdir(directory):
            for root, dirs, files in os.walk(directory):
                for dirName in ignoreDirs:
                    if dirName in dirs:
                        dirs.remove(dirName)
                for basename in files:
                    if not os.path.splitext(basename)[1] in CODE_EXTENSIONS:
                        continue
                    if basename in ignoreBasenames:
                        continue
                    fullPath = os.path.join(root, basename)
                    if os.path.islink(fullPath):
                        continue
                    result.add(fullPath)
        else:
            result.add(directory)
    return sorted(result)
