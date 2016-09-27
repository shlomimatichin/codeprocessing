#define ASSERT(x) do{}while(0)

#include <Python.h>
#include "CodeProcessing/Tokenizer.h"

static PyObject *
codeprocessingnative_tokenizer(PyObject *self, PyObject *args)
{
    const char *contentCString;
    int contentSize;
    const char *hashModeCString;
    int hashModeSize;

    if (!PyArg_ParseTuple(args, "s#s#", &contentCString, &contentSize, &hashModeCString, &hashModeSize))
        return NULL;
    std::string content = std::string(contentCString, contentSize);
    std::string hashModeString = std::string(hashModeCString, hashModeSize);
    enum CodeProcessing::Tokenizer::HashMode hashMode;
    if (hashModeString == "directive")
        hashMode = CodeProcessing::Tokenizer::HASH_IS_DIRECTIVE;
    else if (hashModeString == "comment")
        hashMode = CodeProcessing::Tokenizer::HASH_IS_COMMENT;
    else if (hashModeString == "special")
        hashMode = CodeProcessing::Tokenizer::HASH_IS_SPECIAL;
    else {
        PyErr_SetString(PyExc_ValueError, "hash mode must be one of 'directive', 'comment' or 'special'");
        return nullptr;
    }

    CodeProcessing::Tokenizer tokenizer(std::move(content), hashMode);
    std::list<CodeProcessing::Tokenizer::Token> result;
    while (true)
        try {
            auto token = tokenizer.next();
            result.emplace_back(std::move(token));
        } catch (CodeProcessing::Tokenizer::Done) {
            break;
        }

    PyObject * returned = PyList_New(result.size());
    if (returned == nullptr)
        return nullptr;
    unsigned i = 0;
    for (auto & token: result) {
        PyObject * one = Py_BuildValue("(s#iii)",
                token.spelling.c_str(), token.spelling.size(),
                static_cast<unsigned>(token.type),
                token.beginsOffset,
                tokenizer.offsetToLine(token.beginsOffset));
        if (one == nullptr) {
            Py_DECREF(returned);
            return nullptr;
        }
        PyList_SetItem(returned, i, one);
        ++ i;
    }
    return returned;
}

static PyMethodDef codeprocessingnativeMethods[] = {
    {"tokenizer", codeprocessingnative_tokenizer, METH_VARARGS, NULL},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC
initcodeprocessingnative(void)
{
    PyObject *m;

    m = Py_InitModule("codeprocessingnative", codeprocessingnativeMethods);
    if (m == NULL)
        return;
}
