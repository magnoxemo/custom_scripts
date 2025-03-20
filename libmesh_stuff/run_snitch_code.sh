snitch_branch_path_name=$1
echo $snitch_branch_path_name
git clone --branch="$snitch_branch_path_name" https://github.com/magnoxemo/snitch.git
cd snitch ||exit 1
mkdir build 
cd build
cmake ..
make 

for file in *; do
    if [[ -x "$file" && ! -d "$file" ]]; then
        echo "Running $file"
        ./$file
    fi
donesnitch_branch_path_name



