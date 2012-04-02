clean:
	rm -rf build
	rm -rf htmlcov

rm_pyc:
	find . -name '*.pyc' -delete
