import string

CHARACTERS = string.ascii_lowercase + string.ascii_uppercase + string.digits + '_'
OBJECTIVE_C_KEEP_INIT_PREFIX = False


def meaninglessIdentifier(spelling, id):
    assert id < len(CHARACTERS) ** 3
    first = (id / (len(CHARACTERS) ** 2)) % len(CHARACTERS)
    second = (id / len(CHARACTERS)) % len(CHARACTERS)
    third = id % len(CHARACTERS)
    result = 'Z' + CHARACTERS[first] + CHARACTERS[second] + CHARACTERS[third]
    if OBJECTIVE_C_KEEP_INIT_PREFIX and spelling.startswith("init"):
        return "init" + result
    return result
