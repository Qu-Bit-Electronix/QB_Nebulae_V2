run:
	sh scripts/startup.sh

run3:
	python3 nebulae/nebulae.py

local:
	python instr_tester/nebulae.py

test:
	sh scripts/testrun.sh

test_csound:
	csound tests/test.csd

help:
	python nebulae/doc.py

cleanup_gpio:
	python3 nebulae/cleanup.py
	
clean:
	rm -rf nebulae/*.pyc instr_tester/*.pyc

kill:
	sudo pkill python

