.PHONY: test
test: mocha

.PHONY: clean
clean:
	rm -rf node_modules

.PHONY: mocha
mocha:
	@if [ `ulimit -n` -lt 1024 ]; then echo "ulimit is too low. Please run 'ulimit -S -n 2048' before running tests."; exit 1; fi
	@./node_modules/mocha/bin/mocha tests/* --reporter spec
