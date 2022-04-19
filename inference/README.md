# dSHARK Backend

The triton backend for shark.  Still in developement

# Build

First install dependancies

```
$ apt-get install patchelf rapidjson-dev python3-dev
mkdir thirdparty
cd thirdparty
git clone https://github.com/google/iree.git
cd iree
git submodule update --init
```

```
cmake -GNinja -B ../iree-build/ -S . \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DIREE_ENABLE_ASSERTIONS=ON \
    -DCMAKE_C_COMPILER=clang \
    -DCMAKE_CXX_COMPILER=clang++ \
    -DIREE_ENABLE_LLD=ON

cmake --build ../iree-build/
```

(I know this part is kind of messy, I'm working on having an easier instilation method implemented)

```
cd ../../build
cmake \
-DCMAKE_INSTALL_PREFIX:PATH=`pwd`/install \ -DTRITON_BACKEND_REPO_TAG=r22.02 \
-DTRITON_CORE_REPO_TAG=r22.02 \
-DTRITON_COMMON_REPO_TAG=r22.02 ..
make install
```

There should be a file at /build/install/backends/dshark/libtriton_dshark.so.  Copy it into your triton server image.  https://github.com/triton-inference-server/server/blob/main/docs/compose.md#triton-with-unsupported-and-custom-backends




