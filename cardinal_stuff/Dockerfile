FROM ubuntu:24.04 AS cardinal-base

ARG BRANCH_NAME="devel"
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
        nano \

FROM cardinal-base AS cardinal-clone

WORKDIR /cardinal-build

RUN git clone --branch ${BRANCH_NAME} https://github.com/magnoxemo/cardinal.git
FROM cardinal-clone AS cardinal-deps

WORKDIR /cardinal-build/cardinal

ENV LIBMESH_JOBS=16

RUN ./scripts/get-dependencies.sh && \
    ./contrib/moose/scripts/update_and_rebuild_petsc.sh && \
    ./contrib/moose/scripts/update_and_rebuild_libmesh.sh && \
    ./contrib/moose/scripts/update_and_rebuild_wasp.sh && \
    ./scripts/download-openmc-cross-sections.sh 

FROM cardinal-deps AS cardinal-build

WORKDIR /cardinal-build/cardinal

RUN export NEKRS_HOME=~/cardinal-build/cardinal/install && \
    export CC=mpicc  && \
    export CXX=mpicxx  && \
    export FC=mpif90  && \
 

RUN make -j12 METHOD=${BUILD_METHOD}

RUN cd contrib/openmc &&\
    pip install . 

