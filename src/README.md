../README.md


cmake -G "NMake Makefiles" -DINTEL_CPP=y -DCMAKE_BUILD_TYPE=Release -DDISABLE_R=y  -DCUDA_ARCH=30 .

nmake

Change Xnvlink path in build.make to avoid space in path error

nmake again
