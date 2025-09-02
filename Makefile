PY3 = python3

make: clean package

package:
	$(PY3) -m PyInstaller -F --distpath ./ -n run main.py
	@chmod +x ./run

clean:
	rm -rf build
	rm -rf dist
	rm -rf run
	rm -rf run.spec