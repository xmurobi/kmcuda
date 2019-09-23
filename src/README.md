../README.md


cmake -G "NMake Makefiles" -DINTEL_CPP=y -DCMAKE_BUILD_TYPE=Release -DDISABLE_R=y -DCUDA_ARCH=30 -DSUFFIX=.pyd .

nmake

Change Xnvlink path in build.make to avoid space in path error

nmake again

https://docs.python.org/3/faq/windows.html#is-a-pyd-file-the-same-as-a-dll