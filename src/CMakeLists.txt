cmake_minimum_required(VERSION 3.2)

# Replace Intel C++
if (INTEL_CPP)
  set(CMAKE_CXX_COMPILER "icl")
endif()

project(KMCUDA LANGUAGES CXX CUDA)

set(CMAKE_MODULE_PATH ${CMAKE_HOME_DIRECTORY}/cmake)
set(CMAKE_INSTALL_PREFIX ".")

# OpenMP 
find_package(OpenMP REQUIRED)

# CUDA
if (APPLE AND NOT CUDA_HOST_COMPILER)
  # https://gitlab.kitware.com/cmake/cmake/issues/13674
  message(WARNING "CUDA_HOST_COMPILER is set to the default /usr/bin/clang; CUDA 8.0 requires 7.3 or older.")
  set(CUDA_HOST_COMPILER "/usr/bin/clang" CACHE FILEPATH "" FORCE)
endif()
find_package(CUDA REQUIRED)

# Windows nmake bug fix
if (WIN32)
  message(STATUS "Fix for cudart_static.lib in build.make which cause:: nvlink fatal : Could not open input file space in path issue")
  set(CUDA_LIBRARIES)
endif()

# Python
if (NOT DISABLE_PYTHON)
  if (APPLE)
    # workaround
    # https://github.com/Homebrew/legacy-homebrew/issues/25118
    # https://cmake.org/Bug/view.php?id=14809
    find_program(PYTHON_CONFIG_EXECUTABLE python3-config)
    #find_program(PYTHON_CONFIG_EXECUTABLE /usr/local/bin/python3-config)
    message("-- Found python3-config: ${PYTHON_CONFIG_EXECUTABLE}")
    execute_process(COMMAND ${PYTHON_CONFIG_EXECUTABLE} --prefix OUTPUT_VARIABLE PYTHON_PREFIX OUTPUT_STRIP_TRAILING_WHITESPACE)
    message("-- Discovered Python 3.x prefix: ${PYTHON_PREFIX}")
    set(PYTHON_EXECUTABLE "${PYTHON_PREFIX}/bin/python3")
  endif()
  find_package(PythonInterp 3 REQUIRED)
  find_package(PythonLibs 3 REQUIRED)
  if (NOT NUMPY_INCLUDES)
    execute_process(COMMAND ${PYTHON_EXECUTABLE} -c "import numpy; print(numpy.get_include())" OUTPUT_VARIABLE NUMPY_INCLUDES)
  endif()
endif()

# R
if (NOT DISABLE_R)
  find_package(R)
endif()

if (INTEL_CPP)
  message(STATUS "OpenMP Intel workaround")
  set(CMAKE_CXX_FLAGS "-openmp /MP")
else()
  if(MSVC)
    message(STATUS "OpenMP Windows MSVC workaround")
    set(CMAKE_CXX_FLAGS "/Qopenmp /MP")
  else()
    message(STATUS "OpenMP macOS workaround")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Xclang -fopenmp -std=c++11")
  endif()
endif()

if (PROFILE OR CMAKE_BUILD_TYPE STREQUAL "Debug")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DPROFILE -g")
endif()
#set(CMAKE_VERBOSE_MAKEFILE on)
if (NOT DEFINED CUDA_ARCH)
  set(CUDA_ARCH "61")
endif()
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DCUDA_ARCH=${CUDA_ARCH}")
set(SOURCE_FILES kmcuda.cc kmcuda.h wrappers.h private.h fp_abstraction.h tricks.cuh
                 metric_abstraction.h kmeans.cu knn.cu transpose.cu)
if (PYTHONLIBS_FOUND)
  list(APPEND SOURCE_FILES python.cc)
endif()
if (R_FOUND)
  list(APPEND SOURCE_FILES r.cc)
endif()
if (CMAKE_BUILD_TYPE STREQUAL "Debug")
  set(NVCC_FLAGS "-G -g")
endif()

set(CUDA_NVCC_FLAGS "${CUDA_NVCC_FLAGS} -arch sm_${CUDA_ARCH} -w -D_MWAITXINTRIN_H_INCLUDED -D_FORCE_INLINES")
if (CMAKE_MAJOR_VERSION LESS 4 AND CMAKE_MINOR_VERSION LESS 3)
  # workaround https://github.com/Kitware/CMake/commit/99abebdea01b9ef73e091db5594553f7b1694a1b
  message(STATUS "Applied CUDA C++11 workaround on CMake < 3.3")
  set(CUDA_NVCC_FLAGS "${CUDA_NVCC_FLAGS} --std c++11")
endif()

if (APPLE)
  message(STATUS "Applied CUDA OpenMP macOS workaround")
  set(CUDA_PROPAGATE_HOST_FLAGS OFF)
  set(CMAKE_SHARED_LIBRARY_CXX_FLAGS_BACKUP "${CMAKE_SHARED_LIBRARY_CXX_FLAGS}")
  set(CMAKE_SHARED_LIBRARY_CXX_FLAGS "${CMAKE_SHARED_LIBRARY_CXX_FLAGS} ${CMAKE_CXX_FLAGS} -Wno-unused-function")
  string(REGEX REPLACE "-fopenmp[^ ]*" "" CMAKE_SHARED_LIBRARY_CXX_FLAGS "${CMAKE_SHARED_LIBRARY_CXX_FLAGS}")
endif()

if (MSVC)
	add_definitions(-D_CRT_SECURE_NO_WARNINGS)
endif()

cuda_add_library(KMCUDA SHARED ${SOURCE_FILES} OPTIONS ${NVCC_FLAGS})

if (APPLE)
  set(CMAKE_SHARED_LIBRARY_CXX_FLAGS "${CMAKE_SHARED_LIBRARY_CXX_FLAGS_BACKUP}")
endif()

#target_compile_features(KMCUDA PUBLIC cxx_std_11)
#set_target_properties(KMCUDA PROPERTIES CUDA_SEPARABLE_COMPILATION ON)
#set_target_properties(KMCUDA PROPERTIES POSITION_INDEPENDENT_CODE ON)

if (WIN32)
  target_link_libraries(KMCUDA curand)
else()
  target_link_libraries(KMCUDA curand omp)
endif()

if (PYTHONLIBS_FOUND)
  include_directories(${PYTHON_INCLUDE_DIRS} ${NUMPY_INCLUDES})
  if (WIN32)
    # fix the build fail issue caused by space
    message(STATUS "Fixed for python:: nvlink fatal : Could not open input file space in path issue")
    target_link_libraries(KMCUDA "C:/PROGRA~2/IntelSWTools/intelpython3/libs/python36.lib")
    #target_link_libraries(KMCUDA ${PYTHON_LIBRARIES})
    set_target_properties(KMCUDA PROPERTIES PREFIX "lib")
  else()
    target_link_libraries(KMCUDA ${PYTHON_LIBRARIES})
  endif()
endif()
if (R_FOUND)
  include_directories(${R_INCLUDE_DIRS})
  target_link_libraries(KMCUDA ${R_LIBRARIES})
endif()

if (SUFFIX)
  set_target_properties(KMCUDA PROPERTIES SUFFIX ${SUFFIX})
endif()

