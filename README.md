# czi2codex
Convert czi files to Codex-Processor format.

from multicycle, multi-region czi files `czi2codex` will generate
the following folder structure:
```
- **cyc001_reg001**
    - 1_00001_Z001_CH1.tif
    - ...
- **cyc002_reg001**
- **cyc003_reg001** 
- ...
- experiment.json
- channelnames.txt
- exposure_times.txt
- options.yaml
```
# Installation
## Linux
### Optional: 
Create a conda-environment where all needed packages with the needed correct versions will be installed. 
Type in your terminal:
```buildoutcfg
$ conda create --name codex-env python=3.8
```
Your conda-environment will be then called `condex-env`.
Now, everytime you want to work within this environment with all necessary, installed, packages
call:
```buildoutcfg
$ conda activate codex-env
```
Enter the czi2codex directory, in which the `setup.py` file is 
located, and run:
```
$ pip install .
```
Enter the directory of the source code:
```
$ cd src
```
# Generation of standard setting file
A prerequisite of using the czi2codex conversion-tool is having a 
`options.yaml` file, where mandatory user settings can be saved/changed. In order
to generate the backbone of this file, which then needs to be filled by the 
user, you can run:
```buildoutcfg
$ python3 run_generate_std_options_file.py /dir/to/optionsfile/options.yaml
```
with `/dir/to/optionsfile/options.yaml`, being the directory path, where this 
settings-file should be saved. 
# Run czi2codex conversion
Then you can call the czi2codex conversion tool:
```buildoutcfg
$ python3 run_czi2codex.py /dir/to/optionsfile/options.yaml
```
with `/dir/to/optionsfile/options.yaml`, being the directory path, where 
`options.yaml` is located. 