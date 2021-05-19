# czi2codex
Convert czi files to Codex-Input format

from multicycle, multi-region czi files `czi2codex` will generate
the following folder structure:

- cyc001_reg001
    - 1_00001_Z001_CH1.tif
    - ...
- cyc002_reg001 
- cyc003_reg001 
- ...
- Experiment.json
- channelnames.txt
- exposure_times.txt
