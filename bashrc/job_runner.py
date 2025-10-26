#!/usr/bin/env python
import os
import subprocess

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith('.sh'):
            script_path = os.path.join(root, file)
            full_script_path = os.path.abspath(script_path)
            subprocess.run(['sbatch', full_script_path], cwd=root)
