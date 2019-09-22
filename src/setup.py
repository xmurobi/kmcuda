from multiprocessing import cpu_count
import os
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
from setuptools.dist import Distribution
from shutil import copyfile
from subprocess import check_call
from sys import platform

class SetupConfigurationError(Exception):
    pass


class CMakeBuild(build_py):
    SHLIB = "libKMCUDA.so"

    def run(self):
        if not self.dry_run:
            self._cmake()
            self._build()
        else:
            self._build()

        super(CMakeBuild, self).run()

    def get_outputs(self, *args, **kwargs):
        outputs = super(CMakeBuild, self).get_outputs(*args, **kwargs)
        outputs.extend(self._shared_lib)
        return outputs

    def _cmake(self):
        if platform == "win32":
            self.SHLIB = "libKMCUDA.pyd"
            check_call(("cmake", 
                "-G",
                "NMake Makefiles", 
                "-DCMAKE_BUILD_TYPE=Release", 
                "-DDISABLE_R=y",
                "-DCUDA_ARCH=30",
                "-DSUFFIX=.pyd",
                "-DPREFIX=lib",
                "."))
        elif platform != "darwin":
            cuda_toolkit_dir = os.getenv("CUDA_TOOLKIT_ROOT_DIR")
            cuda_arch = os.getenv("CUDA_ARCH", "61")
            if cuda_toolkit_dir is None:
                raise SetupConfigurationError(
                    "CUDA_TOOLKIT_ROOT_DIR environment variable must be defined")
            check_call(("cmake", "-DCMAKE_BUILD_TYPE=Release", "-DDISABLE_R=y",
                        "-DCUDA_TOOLKIT_ROOT_DIR=%s" % cuda_toolkit_dir,
                        "-DCUDA_ARCH=%s" % cuda_arch,
                        "."))
        else:
            # ccbin = os.getenv("CUDA_HOST_COMPILER", "/usr/local/opt/llvm/bin/clang")
            # env = dict(os.environ)
            # env.setdefault("CC", "/usr/local/opt/llvm/bin/clang")
            # env.setdefault("CXX", "/usr/local/opt/llvm/bin/clang++")
            # env.setdefault("LDFLAGS", "-L/usr/local/opt/llvm/lib/")
            # check_call(("cmake", "-DCMAKE_BUILD_TYPE=Release", "-DDISABLE_R=y",
            #             "-DCUDA_HOST_COMPILER=%s" % ccbin, "-DSUFFIX=.so", "."),
            #            env=env)
            check_call(("cmake", 
                "-DCMAKE_BUILD_TYPE=Release", 
                "-DDISABLE_R=y",
                "-DCUDA_ARCH=30",
                # "-DCUDA_HOST_COMPILER=%s" % ccbin,
                "-DSUFFIX=.so",
                "."), env=env)



    def _build(self, builddir=None):
       
        if platform == "win32":
            check_call(("nmake"))
        else:
            check_call(("make", "-j%d" % cpu_count()))

        self.mkpath(self.build_lib)
        dest = os.path.join(self.build_lib, self.SHLIB)
        copyfile(self.SHLIB, dest)
        self._shared_lib = [dest]


class BinaryDistribution(Distribution):
    """Distribution which always forces a binary package with platform name"""
    def has_ext_modules(self):
        return True

    def is_pure(self):
        return False
        
        
class HackedSdist(sdist):
    def run_command(self, command):
        super().run_command(command)
        if command == "egg_info":
            self.get_finalized_command("egg_info").filelist.extend([
                "fp_abstraction.h",
                "CMakeLists.txt",
                "kmcuda.cc",
                "kmcuda.h",
                "kmeans.cu",
                "knn.cu",
                "metric_abstraction.h",
                "private.h",
                "python.cc",
                "test.py",
                "transpose.cu",
                "tricks.cuh",
                "wrappers.h",
            ])

setup(
    name="libKMCUDA",
    description="Accelerated K-means and K-nn on GPU",
    version="6.2.3",
    license="Apache Software License",
    author="Vadim Markovtsev",
    author_email="vadim@sourced.tech",
    url="https://github.com/src-d/kmcuda",
    download_url="https://github.com/src-d/kmcuda",
    py_modules=["libKMCUDA"],
    install_requires=["numpy"],
    distclass=BinaryDistribution,
    cmdclass={'build_py': CMakeBuild, "sdist": HackedSdist},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: Windows :: POSIX :: Linux",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ]
)

# python3 setup.py bdist_wheel
# auditwheel repair -w dist dist/*
# twine upload dist/*manylinux*
