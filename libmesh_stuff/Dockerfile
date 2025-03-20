FROM ubuntu:24.04 as libMesh-base 

RUN apt-get update --yes &&\
    apt-get upgrade --yes &&\
    apt-get install --yes build-essential cmake git

RUN mkdir -p /SNITCH_TEST_SYSTEM/LIBMESH &&\
    mkdir -p /SNITCH_TEST_SYSTEM/libmesh_install_dir &&\
    cd /SNITCH_TEST_SYSTEM/LIBMESH &&\
    git clone https://github.com/libMesh/libmesh.git && \
    cd libmesh && \
    mkdir build && cd build && \
    ../configure --prefix=/SNITCH_TEST_SYSTEM/libmesh_install_dir &&\
    make -j$(nproc) install

ENV LIBMESH_INSTALL_PATH=/SNITCH_TEST_SYSTEM/libmesh_install_dir

