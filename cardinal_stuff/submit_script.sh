#!/bin/sh
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=64
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=2000
#SBATCH --time=0-48:00:00
#SBATCH --error=job.%J.err
#SBATCH --output=job.%J.out

module load openmpi

export image_path=/scratch/eahammed/
export bind_path=/scratch/eahammed/cardinal_amr
export cross_sections=/scratch/eahammed/cross_sections/endfb-viii.0-hdf5

srun apptainer exec \
    --bind ${bind_path}:${bind_path} \
    --bind ${cross_sections}:${cross_sections} \
    ${image_path}/cardinal_on_hpc.sif \
    bash -c "export OPENMC_CROSS_SECTIONS=${cross_sections}/cross_sections.xml && \
             cd ${bind_path}/models/sfr/assembly && \
             /opt/cardinal-build/cardinal/cardinal-opt -i openmc.i --n-threads=2 > logfile.\${SLURM_PROCID}.txt 2>&1"
