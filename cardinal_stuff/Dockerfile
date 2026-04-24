FROM ubuntu:24.04 

ARG BRANCH_NAME="my_testing"
ARG BUILD_METHOD="opt"

RUN apt-get update --yes && \
    apt-get install --yes \
        git \
        make \
        autoconf \
        automake \
        libtool \
        flex \
        bison \
        cmake \
        g++ \
        gfortran \
        libhdf5-dev \
        mpich \
        libtirpc-dev \
        python3 \
        python3-pip \
        python3-packaging \
        python3-jinja2 \
        python3-yaml \
        python3-pkgconfig\
        curl \
        nano 


WORKDIR /cardinal-build

RUN git clone --branch ${BRANCH_NAME} https://github.com/magnoxemo/cardinal.git

WORKDIR /cardinal-build/cardinal

ENV LIBMESH_JOBS=30
ENV NEKRS_HOME=/cardinal-build/cardinal/install 
ENV CC=mpicc 
ENV CXX=mpicxx  
ENV FC=mpif90 

RUN ./scripts/get-dependencies.sh && \
    cd contrib/openmc && \
    git remote add magnoxemo https://github.com/magnoxemo/openmc.git || true && \
    git fetch magnoxemo && \
    git checkout -b mesh_tally_amalgamation magnoxemo/mesh_tally_amalgamation && \
    cd ../../ && \
    ./contrib/moose/scripts/update_and_rebuild_petsc.sh && \
    ./contrib/moose/scripts/update_and_rebuild_libmesh.sh && \
    ./contrib/moose/scripts/update_and_rebuild_wasp.sh && \
    make -j $nproc
