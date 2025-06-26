import os
import numpy as np

tolerance = np.linspace(0.001, 0.1, 10)

for tol in tolerance:
    command = ""
    # check if I am in the right directory
    if os.path.exists(f"{os.getcwd()}/optical_depth_{tol}"):
        # don't make it just move to that dir
        command += f"cd {os.getcwd()}/optical_depth_{tol}"

    else:
        command += f"mkdir optical_depth_{tol} &&" \
                   f"cd {os.getcwd()}/optical_depth_{tol} && "

    command += f"ln -s ../mesh.i && ln -s ../../ware_house/openmc.i && ln -s ../model.xml &&"  # create symbolic_links
    command += f"/cardinal-build/cardinal/cardinal-opt -i openmc.i --n-threads=32 UserObjects/clustering_1/tolerance={tol}"  # code run command

    os.system(command)
