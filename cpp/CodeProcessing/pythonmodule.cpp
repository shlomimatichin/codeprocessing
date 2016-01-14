#define ASSERT(x) do{}while(0)

#include <Python.h>
#include "CodeProcessing/Tokenizer.h"

static PyObject *
codeprocessingnative_tokenizer(PyObject *self, PyObject *args)
{
    const char *contentCString;
    int contentSize;

    if (!PyArg_ParseTuple(args, "s#", &contentCString, &contentSize))
        return NULL;
    std::string content = std::string(contentCString, contentSize);
    CodeProcessing::Tokenizer tokenizer(std::move(content));
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
