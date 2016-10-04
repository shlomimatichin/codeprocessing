import re
import codeprocessingtokens


KEYWORDS = [
    'void', 'int', 'signed', 'unsigned', 'char', 'double', 'float', 'long', 'bool', 'typedef', 'register',
    'uint', 'uint8_t', 'int8_t', 'uint16_t', 'int16_t', 'uint32_t', 'int32_t', 'uint64_t', 'int64_t',
    'u_int', 'u_int8_t', 'u_int16_t', 'u_int32_t', 'u_int64_t',
    'char_t', 'wchar_t',
    'time_t', 'size_t', 'ssize_t', 'off_t',
    'public', 'private', 'protected', 'class', 'template', 'typename', 'namespace', 'using', 'friend',
    'override', 'explicit', 'virtual', 'static', 'inline', 'volatile', 'const', 'mutable', 'extern',
    'static_cast', 'reinterpret_cast', 'const_cast', 'operator',
    'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'return', 'break', 'continue',
    'nil', 'null', 'nullptr', 'this', 'sizeof', 'new', 'delete', 'enum', 'union', 'struct', 'class', 'auto',
    'not', 'and', 'or', 'true', 'false',
    'try', 'catch', 'throw', 'goto',
]
CPP_KEEP = [
    'c_str', 'size', 'count', 'gcount', 'length', 'substr', 'rdbuf', 'str', 'append', 'emplace_back',
    'find', 'rfind', 'find_first_of', 'find_last_of',
    'pop_front', 'front', 'push_front', 'data', 'clear', 'erase', 'resize', 'back', 'pop_back', 'push_back', 'insert',
    'reset', 'release', 'pointer', 'reference', 'difference_type',
    'seekg', 'tellg', 'eof', 'tellp',
    'begin', 'end', 'rbegin', 'rend', 'beg',
    'native_handle', 'join',
    'wait_for', 'notify_one',
    'first', 'second',
    'lock', 'unlock',
]
C_KEEP = [
    'timeval', 'tv_sec', 'tv_usec', 'gettimeofday', 'timezone',
    'malloc', 'free', 'main', 'errno', 'calloc', 'realloc',
    'st_birthtimespec', 'st_mode', 'st_size',
    'memcpy', 'memmove', 'memcmp', 'memset', 'bzero', 'memchr',
    'close', 'open', 'write', 'read', 'lseek', 'fseek', 'stat', 'fstat', 'unlink', 'rename',
    'rmdir', 'mkdir', 'dirent', 'd_name', 'opendir', 'readdir', 'closedir',
    'O_APPEND', 'O_CREAT', 'O_RDONLY', 'NULL',
    'isalnum',
    'printf', 'scanf', 'sscanf', 'vsprintf', 'vsnprintf', 'snprintf',
    'getpid', 'getppid', 'pthread_mutex_t', 'pthread_self',
    'sigaction', 'siginfo_t', 'sa_sigaction', 'sa_flags', 'sa_handler',
    'va_list', 'va_start', 'va_end',
    'strcmp', 'strcat', 'strlen', 'strcpy', 'strncpy',
    'fopen', 'fclose', 'ftell', 'fseek', 'fread', 'fwrite', 'ferror',
    'rand', 'srand', 'rand_r',
]
OBJECTIVE_C_KEEP = [
    'self', 'selector', 'YES', 'NO', 'BOOL', 'UTF8String', 'Byte', 'Bool', 'SEL',
    'interface', 'implementation', 'IBOutlet', 'property', 'nullable', 'instancetype',
    'synthesize', 'dynamic', 'atomic', 'synchronized', 'autoreleasepool',
    'Class', 'readonly', 'copy', 'strong', 'finally',
]
CUSTOM_KEEP = [
    "_Ti", "_Tn", 'e',
    'TRACE_INFO', 'TRACE_WARNING', 'TRACE_ERROR', 'TRACE_DEBUG',
    'next_in', 'next_out', 'avail_in', 'avail_out',

    'JavaVM', 'JNIEnv', 'JNI_VERSION_1_2', 'GetJavaVM',
    'jobject', 'jboolean', 'jbyte', 'jclass', 'jint', 'jmethodID', 'jfieldID', 'jthrowable', 'jbyteArray',
    'jstring', 'jsize',
    'GetEnv', 'DestroyJavaVM', 'AttachCurrentThread', 'DetachCurrentThread', 'DeleteLocalRef',
    'DeleteGlobalRef', 'NewGlobalRef', 'NewObjectV', 'NewByteArray', 'NewStringUTF',
    'ExceptionOccurred', 'ExceptionClear', 'ThrowNew', 'FatalError',
    'CallBooleanMethod', 'CallIntMethod', 'CallObjectMethod', 'CallReturns', 'CallStaticMethod',
    'CallStaticObjectMethod', 'CallStaticVoidMethod', 'CallStaticVoidMethodV', 'CallVoidMethod',
    'CallVoidMethodV', 'FindClass',
    'GetStaticFieldID', 'GetStaticLongField', 'GetStaticMethodID', 'GetStaticObjectField',
    'GetObjectClass', 'GetMethodID', 'GetByteArrayElements', 'GetStringUTFChars',
    'GetArrayLength', 'GetStringUTFLength', 'GetByteArrayRegion',
    'IsSameObject',
    'SetByteArrayRegion', 'ReleaseByteArrayElements', 'ReleaseStringUTFChars',
]
KEEP = set(KEYWORDS + CPP_KEEP + C_KEEP + OBJECTIVE_C_KEEP + CUSTOM_KEEP)

OBJECTIVE_C_EXP = ["UI[A-Z]", "NS[A-Z]", "C(M|L|G|F|A)[A-Z]", "A(V|L)[A-Z]", "SCNetwork", 'MFMail', 'MFMessage']
CUSTOM_EXP = [
    "^[A-Z_][A-Z_0-9]*$",
    'Java_',
    'lzma_', 'LZMA_',
    'openssl_', 'RSA_', 'RAND_', 'FIPS_', 'NID_', 'SHA1_', 'SHA512_', 'BN_',
    'ASensor', 'ALooper',
]
EXP = [re.compile(e) for e in OBJECTIVE_C_EXP + CUSTOM_EXP]

MULTI_TOKEN_IGNORE_CPP = [
    ['std', '::', None, '::', None, '::', None],
    ['std', '::', None, '<', None, '>', '::', None],
    ['std', '::', None, '::', None],
    ['std', '::', None],
    ['boost', '::', None, '::', None, '::', None],
    ['boost', '::', None, '::', None],
    ['boost', '::', None],
    ['__attribute__', '(', '(', None, ')', ')'],
    ['__attribute__', '(', '(', None, '(', None, ')', ')', ')'],
]
MULTI_TOKEN_IGNORE_CUSTOM = [
    ['RAPIDJSON_DIAG_OFF', '(', None, None, None, ')'],
    ['RAPIDJSON_DIAG_OFF', '(', None, ')'],
]
MULTI_TOKEN_IGNORE = MULTI_TOKEN_IGNORE_CPP + MULTI_TOKEN_IGNORE_CUSTOM


def _matchMultiToken(tokens, index):
    for multiToken in MULTI_TOKEN_IGNORE:
        match = tokens.matchIgnoreWhitespaces(index, multiToken)
        if match is not None:
            return match
    return None


def _matchesExpression(spelling):
    for exp in EXP:
        if exp.match(spelling) is not None:
            return True
    return False


def replacableIdentifiers(tokens):
    i = 0
    while i < len(tokens):
        multiTokenMatched = _matchMultiToken(tokens, i)
        if multiTokenMatched is not None:
            i += len(multiTokenMatched)
            continue
        token = tokens[i]
        i += 1
        if token.kind != codeprocessingtokens.KIND_IDENTIFIER:
            continue
        spelling = token.spelling
        if len(spelling) == 1:
            continue
        if spelling in KEEP:
            continue
        if spelling.startswith("__"):
            continue
        if spelling[0].isdigit():
            continue
        if _matchesExpression(spelling):
            continue
        yield token
