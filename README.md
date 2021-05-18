# czi2codex
Convert czi files to Codex-Input format

from multicycle, multi-region czi files `czi2codex` will generate
the following folder structure:

- Cyc1_reg1
    - filename_00001_Z001_CH1.tif
    - ...
- Cyc2_reg1 
- Cyc3_reg1 
- ...
- Experiment.json
- channelnames.txt
- exposure_times.txt
