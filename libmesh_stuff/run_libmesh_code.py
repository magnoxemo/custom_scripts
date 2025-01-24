import argparse
import os

_parser = argparse.ArgumentParser()
_parser.add_argument("--cpp", help=" name of the cpp src file ")
_parser.add_argument("--exe", help=" name of the cpp exe file ")

_libmesh_include_path = "/home/ebny_walid/libmesh_opt/include"
_libmesh_link_path = "/home/ebny_walid/libmesh_opt/lib"
_eigen_path ="/usr/include/eigen3"

_args = _parser.parse_args()

_run_command = (
    f"mpicxx {_args.cpp} -o {_args.exe} "
    f"-I{_libmesh_include_path} "
    f"-I{_eigen_path} "
    f"-Wl,-rpath,{_libmesh_link_path} "
    f"-L{_libmesh_link_path} "
    f"-lmesh_opt -ltimpi_opt -lnglib -lngcore -lz -ltirpc "
    f"-O2 -felide-constructors -fstrict-aliasing -Wdisabled-optimization "
    f"-funroll-loops -ftrapping-math -fopenmp"
)

_executable_command = "./" +_args.exe
os.system(_run_command)
os.system(_executable_command)

