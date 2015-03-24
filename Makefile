VIRTUALENV = "virtualenv --python /usr/bin/python3"
SPHINX_BUILDDIR = docs/_build
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
PYTHON = $(VENV)/bin/python
DEV_STAMP = $(VENV)/.dev_env_installed.stamp
INSTALL_STAMP = $(VENV)/.install.stamp

.IGNORE: clean
.PHONY: all install virtualenv tests

OBJECTS = .venv .coverage

all: install
install: $(INSTALL_STAMP)
$(INSTALL_STAMP): $(PYTHON)
	$(VENV)/bin/pip install -e .
	touch $(INSTALL_STAMP)

install-dev: $(INSTALL_STAMP) $(DEV_STAMP)
$(DEV_STAMP): $(PYTHON)
	$(VENV)/bin/pip install -r dev-requirements.txt
	touch $(DEV_STAMP)

virtualenv: $(PYTHON)
$(PYTHON):
	$(VIRTUALENV) $(VENV)

serve: install
	$(VENV)/bin/remoteworker-serve

mock_worker: install
	$(PYTHON) clients_examples/worker.py

mock_client: install
	$(PYTHON) clients_examples/client.py

tests: install-dev
	$(VENV)/bin/nosetests -s --with-coverage --cover-package=remote_server
	$(VENV)/bin/flake8 remote_server

clean:
	find . -name '__pycache__' -type d -exec rm -fr {} \;

loadtest-check: install
	$(VENV)/bin/pserve loadtests/server.ini > remote_server.log & PID=$$! && \
	  rm remote_server.log || cat remote_server.log; \
	  sleep 1 && cd loadtests && \
	  make test SERVER_URL=http://127.0.0.1:8000; \
	  EXIT_CODE=$$?; kill $$PID; exit $$EXIT_CODE

docs: install-dev
	$(VENV)/bin/sphinx-build -b html -d $(SPHINX_BUILDDIR)/doctrees docs $(SPHINX_BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(SPHINX_BUILDDIR)/html/index.html"
