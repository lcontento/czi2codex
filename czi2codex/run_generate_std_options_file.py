import argparse
import yaml
import os


def generate_std_options_file(outdir: str,
                              filename: str = '',
                              save=True):
    """
    Generates a standard options-.yaml file, where the user can specify
    her/his preferred microscopy/experiment settings.
    outdir: str
        directory where the options.yaml file will be saved.
    filename: str
        add-ons for the filename: options_ADD_ON_FILENAME.yaml
    """
    user_setting = {'1_czidir': os.path.join(outdir,"dataXYZ-CYC{:02}.czi"),
                    '1_outdir': outdir,
                    '1_channelnames_dir': os.path.join(outdir,"channelnames.txt"),
                    '1_overwrite_exposure_times': False,
                    '1_out_template': "1_{m:05}_Z{z:03}_CH{c:03}",
                    'codex_instrument': "CODEX instrument",
                    'tilingMode': "gridrows",
                    'referenceCycle': 2,
                    'referenceChannel': 1,
                    'numSubTiles': 1,
                    'deconvolutionIterations': 25,
                    'deconvolutionModel': "vectorial",
                    'useBackgroundSubtraction': True,
                    'useDeconvolution': True,
                    'useExtendedDepthOfField': True,
                    'useShadingCorrection': True,
                    'use3dDriftCompensation': True,
                    'useBleachMinimizingCrop': False,
                    'useBlindDeconvolution': False,
                    'useDiagnosticMode': False,
                    'num_z_planes': 1,
                    'tile_width_minus_overlap': None,
                    'tile_height_minus_overlap': None,
                    'wavelengths': [1,2,3,4]}

    # Write YAML file
    if save:
        with open(os.path.join(outdir, 'options' + filename + '.yaml'), 'w',
                  encoding='utf-8') as yaml_file:
            yaml.dump(user_setting, yaml_file)
        print("...finished generating the standard options.yaml file. \n"
              "Saved in "
              f"{os.path.join(outdir,'options' + filename + '.yaml')}")
            # json.dump(user_setting, json_file, ensure_ascii=False, indent=4)

    return user_setting


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate standard '
                                                 'options.yaml file.')
    parser.add_argument("options_dir", help="Directory to options.yaml file."
                                            " (e.g. '/dir/to/optionfile/')",
                        type=str)

    args = parser.parse_args()

    generate_std_options_file(args.options_dir, filename='', save=True)



