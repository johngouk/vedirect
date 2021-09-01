# VEDirect

This is a Python library for decoding the Victron Energy VE.Direct text protocol used in their range of MPPT solar 
charge controllers, battery monitors, and inverters.  
This is a fork of a forked version of a package originally created by Janne Kario (https://github.com/karioja/vedirect).

This fork adds micropython support. It may need [pytomicropy](https://github.com/pfrnz/pytomicropy).

## Installation

To install directly from GitHub:
```
$ python3 -m pip install "git+https://github.com/nznobody/vedirect"
```

If you have cloned or forked the repo already to your local directory and want to use it in live (editable mode):
```
$ python3 -m pip install -e .
```
Note in both cases above, the dependencies needed to run the examples are also installed.

## Use

```python
from vedirect import VEDirect
ve = VEDirect("COM5")
# Or on micropython, e.g. Fipy
ve = VEDirect("1")
res = ve.read_data_single()
```
