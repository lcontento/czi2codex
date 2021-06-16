from generate_metadata_json import generate_std_options_file
import argparse
import yaml

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

    generate_std_options_file(user_input['1_outdir'], filename='', save=True)


