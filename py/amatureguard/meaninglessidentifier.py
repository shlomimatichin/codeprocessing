import string

CHARACTERS = string.ascii_lowercase + string.ascii_uppercase + string.digits + '_'


def meaninglessIdentifier(id):
    assert id < len(CHARACTERS) ** 3
    first = (id / (len(CHARACTERS) ** 2)) % len(CHARACTERS)
    second = (id / len(CHARACTERS)) % len(CHARACTERS)
    third = id % len(CHARACTERS)
    return 'Z' + CHARACTERS[first] + CHARACTERS[second] + CHARACTERS[third]
