# Makefile for `dwim'.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 8, 2017
# URL: https://dwim.readthedocs.io

WORKON_HOME ?= $(HOME)/.virtualenvs
VIRTUAL_ENV ?= $(WORKON_HOME)/dwim
ACTIVATE = . $(VIRTUAL_ENV)/bin/activate

default:
	@echo 'Makefile for dwim'
	@echo
	@echo 'Usage:'
	@echo
	@echo '    make install    install the package in a virtual environment'
	@echo '    make reset      recreate the virtual environment'
	@echo '    make docs       update documentation using Sphinx'
	@echo '    make publish    publish changes to GitHub/PyPI'
	@echo '    make clean      cleanup all temporary files'
	@echo

install:
	test -d "$(VIRTUAL_ENV)" || virtualenv "$(VIRTUAL_ENV)"
	test -x "$(VIRTUAL_ENV)/bin/pip" || ($(ACTIVATE) && easy_install pip)
	test -x "$(VIRTUAL_ENV)/bin/pip-accel" || ($(ACTIVATE) && pip install pip-accel)
	$(ACTIVATE) && pip uninstall -y dwim || true
	$(ACTIVATE) && pip-accel install --editable .

reset:
	rm -Rf "$(VIRTUAL_ENV)"
	make --no-print-directory clean install

docs: install
	test -x "$(VIRTUAL_ENV)/bin/sphinx-build" || ($(ACTIVATE) && pip-accel install sphinx)
	$(ACTIVATE) && cd docs && sphinx-build -b html -d build/doctrees . build/html

publish:
	git push origin && git push --tags origin
	make clean && python setup.py sdist upload

clean:
	rm -Rf *.egg *.egg-info build dist docs/build
	find -depth -type d -name __pycache__ -exec rm -Rf {} \;
	find -type f -name '*.pyc' -delete

.PHONY: default install reset docs publish clean
