../README.md

# windows make
Step 1.

`cmake -G "NMake Makefiles" -DINTEL_CPP=y -DCMAKE_BUILD_TYPE=Release -DDISABLE_R=y -DCUDA_ARCH=30 -DSUFFIX=.pyd .`

Step 2.

`nmake`

# python build

`python setup.py build`

# python install

`python setup.py install`

