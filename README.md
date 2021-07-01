# czi2codex
Convert czi files to Codex-Processor format.

from multicycle, multi-region czi files `czi2codex` will generate
the following folder structure:

<pre>
outdir
    |_ <b>cyc001_reg001</b>
    |    |
    |    |_ 1_00001_Z001_CH1.tif
    |    |_ 1_00001_Z001_CH2.tif
    |    |_ ...
    |_ <b>cyc002_reg001</b>
    |_ <b>cyc003_reg001</b> 
    |_ ...
    |_ experiment.json
    |_ channelnames.txt
    |_ exposure_times.txt
    |_ options.yaml
</pre>

# Installation 
## Linux
### Optional (Creating an environment) 
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
### Installation
Enter the czi2codex directory, in which the `setup.py` file is 
located, and run:
```
$ pip install .
```

# Generation of standard options file
Enter the directory of the source code:
```
$ cd czi2codex
```
A prerequisite of using the czi2codex conversion-tool is having an 
`options.yaml` file, where mandatory user options can be saved/changed. In order
to generate the backbone of this file, which then needs to be filled by the 
user, you can run:
```buildoutcfg
$ python3 run_generate_std_options_file.py /dir/to/optionsfile/
```
with `/dir/to/optionsfile/`, being the directory path, where this 
options-file should be saved. 
You can find an example in the folder `examples/options.yaml` 
for getting an idea how the `options.yaml` file will look like. 
# Run czi2codex conversion
Then you can call the czi2codex conversion tool:
```buildoutcfg
$ python3 run_czi2codex.py /dir/to/optionsfile/options.yaml
```
with `/dir/to/optionsfile/options.yaml`, being the directory path, where 
`options.yaml` is located. 
This will generate 
- the `.tif` files for each cycle, channel and tile
- `exposure_times.txt`
- `experiment.json`
