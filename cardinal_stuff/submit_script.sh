#!/bin/sh

#SBATCH --partition=shared
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=128
#SBATCH --mem-per-cpu=2000
#SBATCH --time=0-48:00:00
#SBATCH --error=job.%J.err
#SBATCH --output=job.%J.out

module load openmpi

export image_path=/scratch/eahammed/
export bind_path=/scratch/eahammed/cardinal_amr

tasks=$((SLURM_NNODES * SLURM_NTASKS_PER_NODE))
threads=$((SLURM_CPUS_PER_TASK * 2))

srun apptainer exec --bind ${bind_path}:${bind_path} ${image_path}/cardinal_on_hpc.sif \
    bash -c "cd ${bind_path}/models/sfr/assembly && \
    ~/opt/cardinal-build/cardinal/cardinal_opt -i openmc.i --n-threads=${threads} > logfile.\${SLURM_PROCID}.txt"
