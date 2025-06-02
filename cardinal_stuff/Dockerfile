FROM ubuntu:24.04 

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
        nano 


WORKDIR /cardinal-build

RUN git clone --branch ${BRANCH_NAME} https://github.com/magnoxemo/cardinal.git

WORKDIR /cardinal-build/cardinal

ENV LIBMESH_JOBS=30

RUN ./scripts/get-dependencies.sh && \
    ./contrib/moose/scripts/update_and_rebuild_petsc.sh && \
    ./contrib/moose/scripts/update_and_rebuild_libmesh.sh && \
    ./contrib/moose/scripts/update_and_rebuild_wasp.sh && \
    ./scripts/download-openmc-cross-sections.sh 


WORKDIR /cardinal-build/cardinal

ENV NEKRS_HOME=/cardinal-build/cardinal/install 
ENV CC=mpicc 
ENV CXX=mpicxx  
ENV FC=mpif90 
 

RUN make -j12 METHOD=${BUILD_METHOD}

RUN cd contrib/openmc &&\
    pip install . --break-system-packages
ENV OPENMC_CROSS_SECTIONS=$PWD/../cross_sections/endfb-vii.1-hdf5/cross_sections.xml
