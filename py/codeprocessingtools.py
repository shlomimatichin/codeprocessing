def stripComment(text):
    if text.startswith("//"):
        assert text.endswith("\n")
        return text[len("//"): -len("\n")]
    elif text.startswith("/*"):
        assert text.endswith("*/")
        return text[len("/*"): -len("*/")]
    elif text.startswith("#"):
        assert text.endswith("\n")
        return text[len("#"): -len("\n")]
    else:
        raise AssertionError("Uknown comment to strip: %s" % text)
