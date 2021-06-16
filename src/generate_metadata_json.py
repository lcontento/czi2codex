# reads from meta-object / metadata-xml and generates json file for the
# use of codex processor
import os
import glob
import xmltodict
from aicspylibczi import CziFile
import numpy as np
import json
import yaml
import lxml
from lxml import etree
from typing import Union
import shutil
from datetime import datetime

# TODO: cannot find wavelengths, that are given in Sonias experiment.json file
#   "wavelengths": [
#    358,
#    488,
#    550,
#    650
#  ], (mine (Emission Wavelenghts are: [465, 561, 673, 773]
# TODO: call from terminal
# TODO: add documentation
# INFORMATION:
#   - For now: take only the metadata of first cycle to infer all necessary
#     information
#   - correction to default units in codex (nanometers)
#     default_corr_to_codex_units = 1e9
#     correction in: zPitch, xyResolution
#   - for finding number of cycles: searches for '.czi' files in directory
#       basedir
#   - tile_x_overl determined by difference between first two tiles, FOR NOW:
#         # TAKE THE OVERLAP BETWEEN THE FIRST TWO TILES
#         #  (although there are inconsistencies, we might need to check and
#         #  incorporate! [205,205,205,204]


def convert_str2float_or_int(x):
    conv_x = float(x) if '.' in x else int(x)
    return conv_x


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
    user_setting = {'1_czidir': "/home/erika/Documents/Projects/CODEX/Data/Collaborators_OriginalData/20200708 Tonsil_beta_after2_compressed/2020.07.08 Tonsil_betaTEST_sfter2-{:02}.czi",
                    '1_outdir': "/home/erika/Documents/Projects/CODEX/Data/test_czi2codex/all_cycles/",
                    '1_channelnames_dir': "/home/erika/Documents/Projects/CODEX/Data/test_czi2codex/ORIGINAL_FILES/channelNamesSONIA.txt",
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
                    'tile_height_minus_overlap': None}

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


def process_user_options(options_dir: str):
    """Process the user-input-options.yaml file. Add remaining default values,
    if not everything is given.
    options_dir: str
        directory to options.yaml file
    """
    default_options = generate_std_options_file(outdir='', filename='',
                                                save=False)

    with open(options_dir) as yaml_file:
        user_input = yaml.load(yaml_file, Loader=yaml.FullLoader)

    # overwrite default options with user input options
    for key in user_input.keys():
        default_options[key] = user_input[key]

    # check entries
    if default_options['tilingMode'] != "gridrows":
        raise ValueError("Not implemented. For now, only "
                         "'tilingMode'='gridrows' is implemented. ")

    return default_options


def meta_to_json(meta: Union[str, lxml.etree._Element],
                 czidir: str,
                 outdir: str,
                 channelnames: str,
                 options_dir: str,
                 exposuretime: str=None):
    """
    Creates experiment.json.
    Parameters
    ----------
    meta: [Optional: str (path to metadata .xml) or etree]
        metadata, either path to xml-file, or etree-Object (directly inferred
        from czi2tif function)
    czidir: str
        directory to czi files
    outdir: str
        where to save json file
    channelnames: str
        path to channelnames.txt file
    exposuretime: str
        path to exposure_times.txt file
    options_dir: str
        directory to options.json file
    """
    print(f"Starting to generate experiment.json file.")
    tiling_mode = 'grid'    # TODO infer or user input?

    # get user input options
    user_input = process_user_options(options_dir)

    # copy channelnames.txt to output directory
    if os.path.dirname(channelnames) != outdir:
        shutil.copyfile(channelnames, os.path.join(outdir, "channelnames.txt"))

    czi_filename, czi_ext = os.path.splitext(os.path.basename(czidir))
    basedir = os.path.dirname(czidir)
    # list of czi-files
    czi_files = glob.glob(os.path.join(basedir, '*' + czi_ext))
    num_cycles = len(czi_files)

    # For now:take only the metadata of first cycle to infer all necessary
    # information
    # TODO: read metadata for all cycles? is there more information
    #   available?
    basename = czi_filename.format(1) #'2020.07.08 Tonsil_betaTEST_sfter2-01'

    # parse Metadata to dict
    if isinstance(meta, str):
        # basename, _ = os.path.splitext(os.path.basename(meta))
        with open(meta, 'r') as f:
            contents = f.read()
        d = xmltodict.parse(contents)
    elif isinstance(meta, lxml.etree._Element):
        d = xmltodict.parse(etree.tostring(meta))

    # Introducing some shortcuts
    d_meta = d['ImageDocument']['Metadata']
    d_obj = d_meta['Information']['Instrument']['Objectives']['Objective']
    d_channel = d_meta['Information']['Image']['Dimensions']['Channels'][
        'Channel']
    d_region_00 = d_meta['Experiment']['ExperimentBlocks']['AcquisitionBlock'][
        'SubDimensionSetups']['RegionsSetup']
    d_region_tile = d_region_00['SampleHolder']['TileRegions'][
        'TileRegion']
    d_region_multitrack = d_region_00['SubDimensionSetups']['TilesSetup'][
        'SubDimensionSetups']['MultiTrackSetup']
    d_region_dist = d_region_multitrack['SubDimensionSetups'][
        'ZStackSetup']['Interval']['Distance']
    d_dist = d_meta['Scaling']['Items']['Distance']

    # ------------------
    # Cycle information
    # get cycle numbers
    cycles_nr_list = []
    for i in range(num_cycles):
        cycles_nr_list.append(int(os.path.splitext(os.path.basename(
            czi_files[i]))[0][-2:]))

    # ------------
    # read channelnames.txt and exposure_time.txt
    cn = open(channelnames, "r")

    if exposuretime is None:
        # default exposure-time directory
        exposuretime = os.path.join(outdir, "exposure_times.txt")

    if not os.path.exists(exposuretime):
        raise ValueError(exposuretime + " does not exist. Should be created"
                                         "when creating the tif-files with "
                                         "'czi2ti_codex.czi_to_tiffs()'.")
    et = open(exposuretime, "r")

    # --------
    # Per_cycle_channel_names & Emission wavelength
    channel_names = []
    em_wv = []
    for i_c in range(len(d_channel)):
        channel_names.append(d_channel[i_c]['@Name'])
        em_wv.append(d_channel[i_c]['EmissionWavelength'])

        # Region_height, region_width
        region_width = int(d_region_tile['Columns'])
        region_height = int(d_region_tile['Rows'])

        # ----------
        # Tile width, tile height
        # Tile_overlap: calculate with read_subblock_rect
        czi = CziFile(os.path.join(basedir, basename + '.czi'))
        S, T, C, Z, M, Y, X = czi.size
        tilepos = []
        # Get tile position,
        for m in range(M):
            tilepos.append(czi.read_subblock_rect(S=0, T=0, C=0, Z=0, M=m))
        tile_width = tilepos[0][2]
        tile_height = tilepos[0][3]
        tile_x_overl = []
        tile_y_overl = []
        if tiling_mode == 'grid':
            for i_x in range(region_width - 1):
                tile_x_overl.append((tilepos[i_x][0] + tile_width) -
                                    tilepos[i_x + 1][0])
            for i_y in np.arange(0, M - region_width, region_width):
                tile_y_overl.append((tilepos[i_y][1] + tile_height) -
                                    tilepos[i_y + region_width][1])
        else:
            raise Exception(
                'Calculation of tile overlaps for other tiling_modes'
                '(than grid) not implemented yet. Please do so.')
        # TODO: (?) FOR NOW: TAKE THE OVERLAP BETWEEN THE FIRST TWO TILES
        #  (although there are inconsistencies, we might need to check and
        #  incorporate! [205,205,205,204]
        tile_overlap_x = round(tile_x_overl[0]/tile_width, 1)
        tile_overlap_y = round(tile_y_overl[0]/tile_height, 1)


    # tile_width_after = tile_width - math.floor(tile_overlap_x*tile_width)
    # tile_height_after = tile_height - math.floor(tile_overlap_y*tile_height)

    # -------
    # Z Pitch = axial resolution
    # units in codex are in nanometers
    default_corr_to_codex_units = 1e9
    for i_dim in range(len(d_dist)):
        if d_dist[i_dim]['@Id'] == 'Z':
            axial_resolution = float(d_dist[i_dim]['Value']) * \
                               default_corr_to_codex_units
    # check - compare to axial_resolution from Distance tag Z-distance
    axial_resolution2 = float(d_region_dist['Value']) * \
                        default_corr_to_codex_units
    if axial_resolution != axial_resolution2:
        raise Exception('Axial resolutions inferred from two independent spots'
                        ' are not the same! Please check!')

    # -------
    # xyResolution = Lateral_resolution = pixelsize  / magnification
    magnification = float(d_obj['NominalMagnification'])
    pixelsize_str = d_meta['ImageScaling']['ImagePixelSize']
    pixelsize_map = map(float, pixelsize_str.split(','))
    pixelsize = list(pixelsize_map)
    if pixelsize[0] == pixelsize[1]:
        lateral_resolution = pixelsize[0] / magnification * \
                             1e-6 * default_corr_to_codex_units
    else:
        raise Exception('Pixelsize is not squared, does this make sense?')
    # compare to Lateral_resolution from Distance tag
    for i_dim in range(len(d_dist)):
        if d_dist[i_dim]['@Id'] == 'X':
            lat_resolutionx = float(
                d_dist[i_dim]['Value']) * default_corr_to_codex_units
        if d_dist[i_dim]['@Id'] == 'Y':
            lat_resolutiony = float(
                d_dist[i_dim]['Value']) * default_corr_to_codex_units
    if lat_resolutionx != lat_resolutiony:
        raise Exception(
            'Distance x resolution does not equal Distance y resolution.'
            'Please check!')
    if lateral_resolution != lat_resolutionx:
        raise Exception(
            'Computed lateral resolution and shown in X-Distance is not '
            'the same! Please check!')

    # ----------
    # Focus Offset
    focus_offset_list = []
    for i in range(len(d_region_multitrack['Track'])):
        focus_offset_list.append(d_region_multitrack['Track'][i]['FocusOffset'])
    # check if focus_offset is the same for all channels
    if len(set(focus_offset_list)) == 1:
        f_o = focus_offset_list[0]
        focus_offset = convert_str2float_or_int(f_o)
    else:
        raise ValueError('Focus offset is not the same for all channels. '
                         'Please check, which focus-offset value should be '
                         'taken.')

    timestamp = datetime.now()
    dateprocessed = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")

    # WRITE JSON
    # Dictionary with all entries for json file
    dict_json = {}

    dict_json['version'] = "1.x.x.x"    # TODO ? user defined?
    dict_json['name'] = basename
    dict_json['runName'] ="2020-11-04"  # TODO ? user defined?
    dict_json['date'] = d_meta['Information']['Document']['CreationDate']
    dict_json['dateProcessed'] = dateprocessed
    dict_json['path'] = basedir
    dict_json['outputPath'] = outdir
    dict_json['codex_instrument'] = user_input['codex_instrument'] # TODO done,  possibility of user input
    dict_json['microscope'] = d_meta['Information']['Instrument'][
        'Microscopes']['Microscope']['@Name']
    dict_json['magnification'] = magnification
    dict_json['aperture'] = float(d_obj['LensNA'])
    dict_json['objectiveType'] = d_obj['Immersion']
    dict_json['xyResolution'] = lateral_resolution    # 377.442
    dict_json['zPitch'] = axial_resolution     # 1500.0
    # dict_json['channel_arrangement'] = "grayscale" # TODO done, does not exist in SONIAs example file, only in codex-examplefile. tocheck
    dict_json['per_cycle_channel_names'] = channel_names  # [', '.join(map(str, channel_names))]
    dict_json['wavelengths'] = list(map(int, em_wv)) #[', '.join(map(int, em_wv))]
    dict_json['bitDepth'] = int(d_meta['Information']['Image'][
                                    'ComponentBitCount'])
    dict_json['numRegions'] = S
    dict_json['numCycles'] = len(czi_files)
    dict_json['numZPlanes'] = Z
    dict_json['numChannels'] = C
    dict_json['regionWidth'] = region_width
    dict_json['regionHeight'] = region_height
    dict_json['tileWidth'] = tile_width  # tile width
    dict_json['tileHeight'] = tile_height  # tile height
    dict_json['tileOverlapX'] = tile_overlap_x  # TODO: check: now in pixel, (in Sonia's file its in percentage, in codex-example-file its in pixel))
    dict_json['tileOverlapY'] = tile_overlap_y
    dict_json['tilingMode'] = user_input['tilingMode']       # ?? TODO done, raise NotImplementedError in the other cases
    dict_json['referenceCycle'] = user_input['referenceCycle']       # TODO done, user-specifiable but the default value will be the good one almost everytime
    dict_json['referenceChannel'] = user_input['referenceChannel']          # TODO done, user-specifiable but in almost all cases will be 1
    dict_json['numSubTiles'] = user_input['numSubTiles']             # TODO done, not sure, keep it fixed at 1 for now
    dict_json['deconvolutionIterations'] = user_input['deconvolutionIterations']  # TODO done, user specifiable
    dict_json['deconvolutionModel'] = user_input['deconvolutionModel']  # TODO done, user specifiable

    dict_json['focusingOffset'] = focus_offset  # TODO done
    dict_json['useBackgroundSubtraction'] = user_input['useBackgroundSubtraction']  # TODO done, use* options: should be set by the user in general
    dict_json['useDeconvolution'] = user_input['useDeconvolution']  # TODO done
    dict_json['useExtendedDepthOfField'] = user_input['useExtendedDepthOfField']  # TODO done
    dict_json['useShadingCorrection'] = user_input['useShadingCorrection']  # TODO done
    dict_json['use3dDriftCompensation'] = user_input['use3dDriftCompensation']  # TODO done
    dict_json['useBleachMinimizingCrop'] = user_input['useBleachMinimizingCrop']  # TODO done
    dict_json['useBlindDeconvolution'] = user_input['useBlindDeconvolution']  # TODO done
    dict_json['useDiagnosticMode'] = user_input['useDiagnosticMode']  # TODO done

    dict_json['channelNames'] = {'channelNamesArray': [x.strip() for x in cn]}
    dict_json['exposureTimes'] = {
        'exposureTimesArray': [(line.strip()).split(',') for line in et]}

    dict_json['projName'] = basename
    dict_json['regIdx'] = [S]           # TODO done, is that correct? no idea..., leave it as it is in the example
    dict_json['cycle_lower_limit'] = min(cycles_nr_list)
    dict_json['cycle_upper_limit'] = max(cycles_nr_list)
    dict_json['num_z_planes'] = user_input['num_z_planes']   # TODO done, Maybe the number of output z-planes (after focus merging), but I am not sure. For the moment I would leave it as in the example
    dict_json['region_width'] = region_width
    dict_json['region_height'] = region_height
    dict_json['tile_width'] = user_input['tile_width_minus_overlap'] # TODO done , could be defined by 2048-math.floor(2048*0.1) , Above tile_width was 2048, where is this 1844 coming from?
    dict_json['tile_height'] = user_input['tile_height_minus_overlap'] # TODO done , now: user defined. Above tile_height was 2048 ->  I think these are the tile dimensions after the overlap is subtracted (please check it)
    # TODO: to check: SONIA: tile_width = 2048, tileOverlapX=0.1,
    #  tile_width_after = 2048-2048*0.1 = 1843.2 ???

    # Write JSON file
    with open(os.path.join(outdir, 'experiment.json'), 'w',
              encoding='utf-8') as json_file:
        json.dump(dict_json, json_file, ensure_ascii=False, indent=4)
    print('...Finished writing experiment.json file!..... \n'
          f'...Saved in {outdir}')

    return

