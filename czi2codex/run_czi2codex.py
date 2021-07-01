# from .czi2tif_codex import czi_to_tiffs #for jupyter-notebook
# from .generate_metadata_json import meta_to_json #for jupyter-notebook
from czi2tif_codex import czi_to_tiffs
from generate_metadata_json import meta_to_json
import argparse
import yaml
import os


def czi2codex_all(options_dir: str):
    """
    Run the complete czi2codex-formatting. First create tif files for all
    cycles, channels, mosaics, Z-planes; then generate 'exposure_times.txt'-
    file; then generate 'experiment.json'-file.
    Parameters:
    -----------
    czidir: str
        directory of czi-files, with filename-template for the
        different cycles (e.g. '/dir/to/czifiles/filename_CYC{:02}.czi')
    outdir: str
        output directory, where everything should be saved
    channelnames_dir: str
        directory of channelnames.txt file,
        (e.g. '/dir/to/channelnames/channelnames.txt')
    options_dir: str
        directory of options.yaml file,
        (e.g. '/dir/to/czifiles/options.yaml')
    out_template: str
        output-filenaming template, default is: '1_{m:05}_Z{z:03}_CH{c:03}'
    overwrite_exposure: bool
        if exposure_times.txt exist, shall it then be overwritten?
    """
    # read standard options file
    with open(options_dir) as yaml_file:
        user_input = yaml.load(yaml_file, Loader=yaml.FullLoader)

    channelnames_dir = user_input['1_channelnames_dir']
    czidir = user_input['1_czidir']
    outdir = user_input['1_outdir']
    out_tempate = user_input['1_out_template']
    overwrite_exposure_times = user_input['1_overwrite_exposure_times']

    if not os.path.exists(channelnames_dir):
        raise FileNotFoundError('File not found. Please check directory to the '
                                'channelnames.txt, which should be defined in '
                                '"1_channelnames_dir:" in options.yaml. \nFile '
                                'not found: ' + channelnames_dir)
    if not os.path.exists(outdir):
        raise FileNotFoundError('Directory not found. Please check the ouput '
                                'directory '
                                'where the output shall be saved. The output '
                                'directory should be defined in "1_outdir:" '
                                'in options.yaml. \nDirectory  not found: ' +
                                outdir)

    # convert czi to tifs & generate exposure_times.txt
    _, _, _, meta, _ = czi_to_tiffs(czidir,
                                    outdir,
                                    out_tempate,
                                    overwrite_exposure_times)
    # generate experiment.json
    meta_to_json(meta, czidir, outdir,
                 channelnames_dir, options_dir)
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run conversion czi to codex-'
                                                 'format. Writes '
                                                 'exposure_times.txt and '
                                                 'experiment.json. Input: '
                                                 'Directory to options.yaml')
    parser.add_argument("options_dir", help="Directory to options.yaml file."
                                              " (e.g. '/dir/to/optionfile/"
                                              "options.yaml')",
                        type=str)

    args = parser.parse_args()
    # with open(args.options_dir) as yaml_file:
    #     user_input = yaml.load(yaml_file, Loader=yaml.FullLoader)

    czi2codex_all(options_dir=args.options_dir)

