# Build and install Cardinal in a Docker image without conda
#
# Divided into the following targets:
#
# cardinal-base: starting from an Ubuntu 24.04 image:
#     * installs all required packages
#
# cardinal-clone:
#     * clone cardinal repo
#
# cardinal-deps:
#     * run the get-dependency script
#
# cardinal-build:
#     * make cardinal using specific environment variables
#
FROM ubuntu:24.04 AS cardinal-base

# Install necessary dependencies
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
        curl 
FROM cardinal-base AS cardinal-clone
# COPY . /cardinal    
WORKDIR /cardinal-build

RUN git clone --branch custom_scripts https://github.com/magnoxemo/cardinal.git
FROM cardinal-clone AS cardinal-deps

WORKDIR /cardinal-build/cardinal

ENV LIBMESH_JOBS=16

RUN git config --file .gitmodules submodule.contrib/moose.url https://github.com/magnoxemo/moose.git &&\
    git submodule sync && \
    git submodule update --init contrib/moose


RUN ./scripts/get-dependencies.sh && \
    ./contrib/moose/scripts/update_and_rebuild_petsc.sh && \
    ./contrib/moose/scripts/update_and_rebuild_libmesh.sh && \
    ./contrib/moose/scripts/update_and_rebuild_wasp.sh && \
    ./scripts/download-openmc-cross-sections.sh 

FROM cardinal-deps AS cardinal-build

WORKDIR /cardinal-build/cardinal

RUN export NEKRS_HOME=/cardinal-build/cardinal/install && \
    export CC=mpicc  && \
    export CXX=mpicxx  && \
    export FC=mpif90  && \
    export OPENMC_CROSS_SECTIONS=${HOME}/cross_sections/endfb-vii.1-hdf5/cross_sections.xml 

RUN make -j32




#docker build -t cardinal-build .
#docker run -it -v  cardinal-build
