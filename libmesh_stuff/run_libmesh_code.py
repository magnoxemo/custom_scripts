import argparse
import os

_parser = argparse.ArgumentParser()
_parser.add_argument("--cpp", help = " name of the cpp src file ")
_parser.add_argument("--exe", help = " name of the cpp exe file ")
_parser.add_argument("--rebuild", help = "If the program needs to be rebuild",default = False)

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

if os.path.exists(_args.exe) and _args.rebuild :
    print("===================================================")
    print("=== removing existing executable and rebuilding ===")
    print("===================================================")
    os.system(f"rm {_args.exe}")
    os.system(_run_command)
    print(f"running the new {_args.exe}")
    os.system(_executable_command)
else:
    if os.path.exists(_args.exe):
        os.system(_executable_command)
    else:
        print( "===================================================")
        print(f"=====  {_args.exe} doesn't exists so building it   =======")
        print( "===================================================")
        os.system(_run_command)
        os.system(_executable_command)



