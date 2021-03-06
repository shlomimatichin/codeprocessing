all: unittest build pyunittest

.PHONY: build
build: build/codeprocessingnative.so

build/codeprocessingnative.so: cpp/CodeProcessing/pythonmodule.cpp
	-mkdir $(@D)
	g++ -shared $< -o $@ -Wall -Werror -fPIC -Icpp -I/usr/include/python3.6/ -L/usr/lib/x86_64-linux-gnu -I/System/Library/Frameworks/Python.framework/Versions/3.6/include/python3.6 -L/System/Library/Frameworks/Python.framework/Versions/3.6/lib/ -lpython3.6m -std=gnu++11 -MMD -MF $@.deps
-include build/codeprocessingnative.so.deps

clean:
	rm -fr build

export CXXTEST_FIND_ROOT = cpp
export UNITTEST_INCLUDES = -Ibuild_unittest/voodoo/cpp -Icpp -I.
export VOODOO_SCAN_HEADERS_ROOTS = cpp
export VOODOO_INCLUDES = --includePath=cpp
export VOODOO_FLAGS = --define=DEBUG --define=BOOST_ASIO_HAS_MOVE '--excludeFilesPattern=\bError.h\b'
export VOODOO_ROOT_DIR = ../voodoo-mock

-include $(VOODOO_ROOT_DIR)/make/integrations/complete.Makefile
unittest:
	$(MAKE) -f $(VOODOO_ROOT_DIR)/make/1_generate.Makefile
	$(MAKE) -f $(VOODOO_ROOT_DIR)/make/2_build.Makefile
	$(MAKE) -f $(VOODOO_ROOT_DIR)/make/3_run.Makefile

PYTHON_UNITTESTS=$(shell find py -name 'test_*.py' | sort)
.PHONY: pyunittest
pyunittest:
	for testfile in $(PYTHON_UNITTESTS); do PYTHONPATH=py:build python $$testfile || exit 4; done
