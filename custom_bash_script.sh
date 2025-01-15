#this should try to build cardinal inside a docker image given that 
#that docker image contains all the dependencies 

git clone -b mesh_tally_amalgamation https://github.com/magnoxemo/cardinal.git
cd cardinal
git config --file .gitmodules submodule.contrib/moose.url https://github.com/magnoxemo/moose.git &&\
    git config --file .gitmodules submodule.contrib/moose.branch element_amalgamation  && \
    git submodule sync && \
    git submodule update --init contrib/moose

./scripts/get-dependencies.sh
./contrib/moose/scripts/update_and_rebuild_petsc.sh
./contrib/moose/scripts/update_and_rebuild_libmesh.sh 
./contrib/moose/scripts/update_and_rebuild_wasp.sh 
./scripts/download-openmc-cross-sections.sh 

export NEKRS_HOME=$PWD/install

make -j 12
