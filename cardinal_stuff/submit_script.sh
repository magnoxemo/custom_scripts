#!/bin/sh
#SBATCH --partition=pre
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=64
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2000
#SBATCH --time=0-4:00:00
#SBATCH --error=job.%J.err
#SBATCH --output=job.%J.out

module load openmpi
export UCX_POSIX_USE_PROC_LINK=n
export image_path=/scratch/eahammed/software/cardinal_dev/cardinal.sif
export bind_path=$PWD
export cross_sections=/scratch/eahammed/cross_sections/endfb-viii.0-hdf5/
TOTAL_THREADS=$(( SLURM_NTASKS_PER_NODE * SLURM_CPUS_PER_TASK ))

srun apptainer exec \
    --bind ${bind_path}:${bind_path} \
    --bind ${cross_sections}:${cross_sections} \
    ${image_path} \
    bash -c "export OPENMC_CROSS_SECTIONS=${cross_sections}/cross_sections.xml && \
             cd ${bind_path} && \
             /opt/cardinal-build/cardinal/cardinal-opt -i 3D_bpf_unit_cells.i --mesh-only --n-threads=${TOTAL_THREADS} && \
             /opt/cardinal-build/cardinal/cardinal-opt -i openmc.i --n-threads=${TOTAL_THREADS}"
