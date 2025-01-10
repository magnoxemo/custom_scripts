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
 

RUN make -j32

RUN cd contrib/openmc &&\
    pip install . 


#docker build -t cardinal-build .
#docker run -v $PWD:/cardinal-build -it   cardinal-build
