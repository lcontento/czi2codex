from czi2tif_codex import czi_to_tiffs
from generate_metadata_json import meta_to_json
import argparse
import yaml


def czi2codex_all(czidir: str,
                  outdir: str,
                  channelnames_dir: str,
                  options_dir: str,
                  out_template: str = '1_{m:05}_Z{z:03}_CH{c:03}',
                  overwrite_exposure: bool = False):
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
    # convert czi to tifs & generate exposure_times.txt
    _, _, _, meta, _ = czi_to_tiffs(czidir,
                                    outdir,
                                    out_template, overwrite_exposure)
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
    with open(args.options_dir) as yaml_file:
        user_input = yaml.load(yaml_file, Loader=yaml.FullLoader)

    czi2codex_all(czidir=user_input['1_czidir'],
                  outdir=user_input['1_outdir'],
                  channelnames_dir=user_input['1_channelnames_dir'],
                  options_dir=args.options_dir,
                  out_template=user_input['1_out_template'],
                  overwrite_exposure=user_input['1_overwrite_exposure_times'])

