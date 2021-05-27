# reads from metadata-xml and generates yaml file for the use of cytokit
import os
import glob
import xmltodict
from aicspylibczi import CziFile
import numpy as np
import json
import lxml
from lxml import etree

# INFORMATION:
# HARDCODED:
#   - channel_names
#   - tiling_mode = grid
#   - correction to default cytokit units (nanometers)
#       (default_corr_to_cytokit_units = 10**9)
#   - for finding number of cycles: searches for '.czi' files in directory
#       path_czi_files
#   - tile_x_overl determined by difference between first two tiles
#   - path_formats: keyence_multi_cycle_v01
#      depending on if we want to consider multiple cycles, or one cycle:
#       - keyence_single_cycle_v01:
#           image file name should be in format:
#           {region:d}_{tile:05d}_Z{z:03d}_CH{channel:d}.tif
#       - keyence_multi_cycle_v01
#           image file name should be in format:
#           Cyc{cycle:d}_reg{region:d}/{region:d}_{tile:05d}_Z{z:03d}_CH{channel:d}.tif
#       for more information, see cytokit/python/pipeline/cytokit/io.py


def meta_to_json(meta: str,
                 image_path: str,
                 outdir: str,
                 channelnames:str,
                 exposuretime:str):
    """
    Creates channelnames.txt, exposure_times.txt and experiment.json.
    Parameters
    ----------
    meta: [Optional: str (path to metadata .xml) or etree]
        metadata, either path to xml-file, or etree-Object (directly inferred
        from czi2tif function)
    image_path: str
        directory to czi file
    outdir: str
        where to save json file
    channelnames: str
        path to channelnames.txt file
    exposuretime: str
        path to exposure_times.txt file
    """
    tiling_mode = 'grid'    # TODO infer or user input?

    basename, _ = os.path.splitext(os.path.basename(image_path))
    path_czi_files = os.path.dirname(image_path)

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
    d_region = d_meta['Experiment']['ExperimentBlocks']['AcquisitionBlock'][
        'SubDimensionSetups']['RegionsSetup']['SampleHolder']['TileRegions'][
        'TileRegion']

    # Cycle information
    files_czi = glob.glob(path_czi_files + '*.czi')
    # get cycle numbers
    cycles_nr_list = []
    for i in range(len(files_czi)):
        cycles_nr_list.append(int(os.path.splitext(os.path.basename(
            files_czi[i]))[0][-2:]))

    # read channelnames.txt and exposure_time.txt
    cn = open(channelnames, "r")
    et = open(exposuretime, "r")

    # Per_cycle_channel_names & Emission wavelength
    channel_names = []
    em_wv = []
    for i_c in range(len(d_channel)):
        channel_names.append(d_channel[i_c]['@Name'])
        em_wv.append(d_channel[i_c]['EmissionWavelength'])

        # Region_height, region_width
        region_width = int(d_region['Columns'])
        region_height = int(d_region['Rows'])

        # Tile width, tile height
        # Tile_overlap: calculate with read_subblock_rect
        czi = CziFile(os.path.join(path_czi_files, basename + '.czi'))
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
            for i_y in np.arange(0, M - region_width,region_width):
                tile_y_overl.append((tilepos[i_y][1] + tile_height) -
                                    tilepos[i_y + region_width][1])
        else:
            raise Exception(
                'Calculation of tile overlaps for other tiling_modes'
                '(than grid) not implemented yet. Please do so.')
        # TODO: (?) FOR NOW: TAKE THE OVERLAP BETWEEN THE FIRST TWO TILES
        #  (although there are inconsistencies, we might need to check and
        #  incorporate! [205,205,205,204]
        tile_overlap_x = tile_x_overl[0]
        tile_overlap_y = tile_y_overl[0]

    # WRITE JSON
    # Dictionary with all entries for json file
    dict_json = {}

    dict_json['name'] = basename
    dict_json['date'] = d_meta['Information']['Document']['CreationDate']
    dict_json['path'] = path_czi_files
    dict_json['outputPath'] = outdir
    dict_json['codex_instrument'] = "CODEX instrument" # ???
    dict_json['microscope'] = d_meta['Information']['Instrument'][
        'Microscopes']['Microscope']['@Name']
    dict_json['magnification'] = d_obj['NominalMagnification']
    dict_json['numerical_aperture'] = d_obj['LensNA']
    dict_json['objectiveType'] = d_obj['Immersion']
    dict_json['xyResolution'] = "TODO 377.442"     # TODO
    dict_json['zPitch'] = "TODO 1500.0"       # TODO
    # dict_json['channel_arrangement'] = "grayscale" # TODO
    dict_json['per_cycle_channel_names'] = channel_names  # [', '.join(map(str, channel_names))]
    dict_json['wavelengths'] = list(map(int, em_wv)) #[', '.join(map(int, em_wv))]
    dict_json['bitDepth'] = int(d_meta['Information']['Image'][
                                    'ComponentBitCount'])
    dict_json['numRegions'] = S         # TODO: number of regions = number of
                                        #  scenes ? is that correct?
    dict_json['numCycles'] = len(files_czi)
    dict_json['numZPlanes'] = Z
    dict_json['numChannels'] = C
    dict_json['regionWidth'] = region_width
    dict_json['regionHeight'] = region_height
    dict_json['tileWidth'] = tile_width  # tile width
    dict_json['tileHeight'] = tile_height  # tile height
    dict_json['tileOverlapX'] = tile_overlap_x
    dict_json['tileOverlapY'] = tile_overlap_y
    dict_json['tilingMode'] = "TODO gridrows"        # ?? TODO
    dict_json['referenceCycle'] = "TODO 2"             # ?? TODO
    dict_json['referenceChannel'] = "TODO 1"           # ?? TODO
    dict_json['numSubTiles'] = "TODO 1"                # ?? TODO
    dict_json['deconvolutionIterations'] = "TODO 25"  # ?? TODO
    dict_json['deconvolutionModel'] = "vectorial"  # ?? TODO
    dict_json['focusingOffset'] = "TODO 0"  # ?? TODO
    dict_json['useBackgroundSubtraction'] = True  # ?? TODO
    dict_json['useDeconvolution'] = True  # ?? TODO
    dict_json['useExtendedDepthOfField'] = True  # ?? TODO
    dict_json['useShadingCorrection'] = True  # ?? TODO
    dict_json['use3dDriftCompensation'] = True  # ?? TODO
    dict_json['useBleachMinimizingCrop'] = False  # ?? TODO
    dict_json['useBlindDeconvolution'] = False  # ?? TODO
    dict_json['useDiagnosticMode'] = False  # ?? TODO
    dict_json['channelNames'] = {'channelNamesArray': [x.strip() for x in cn]}
    dict_json['exposureTimes'] = {
        'exposureTimesArray': [(line.strip()).split(',') for line in et]}

    dict_json['projName'] = basename
    dict_json['regIdx'] = [S]           # TODO, is that correct?
    dict_json['cycle_lower_limit'] = min(cycles_nr_list)
    dict_json['cycle_upper_limit'] = max(cycles_nr_list)
    dict_json['num_z_planes'] = "TODO 1"     # TODO?
    dict_json['region_width'] = region_width
    dict_json['region_height'] = region_height
    dict_json['tile_width'] = "TODO 1844"  # TODO ??? Above tile_width was 2048, where is this 1844 coming from?
    dict_json['tile_height'] = "TODO 1844" # TODO ??? Above tile_height was 2048

    # Write JSON file
    with open(os.path.join(outdir, 'experiment_test.json'), 'w',
              encoding='utf-8') as json_file:
        json.dump(dict_json, json_file, ensure_ascii=False, indent=4)


    #
    #
    # # "cycle_upper_limit": 8,
    # # "cycle_lower_limit": 1,
    # # "regIdx": [1],
    # # "region_names": ["Region 1"],
    # # "tiling_mode": "snake",
    # # "region_width": 5,
    # # "region_height": 5,
    # # "tile_overlap_X": 576,
    # # "tile_overlap_Y": 432,
    # # "readout_channels": [2,
    # #                      3,
    # #                      4],
    # # DONE ____ "objectiveType": "air",
    # # "HandEstain": false,
    # # "tile_height": 1008,
    # # "tile_width": 1344,
    # # "driftCompReferenceCycle": 1,
    # # "bestFocusReferenceCycle": 1,
    # # "projName": "1",
    # # "optionalFocusFragment": true,
    # # "focusing_offset": 0,
    # # "microscopeTypes": ["Keyence BZ-X710",
    # #                     "Zeiss ZEN"]
    #
    #
    #
    #
    #
    #
    #
    #
    #
    # old = True
    # if not old:
    #     # units in cytokit are in nanometers
    #     default_corr_to_cytokit_units = 1e9
    #
    #     # Axial_resolution is the distance between Z layers
    #     zdis_hier = d_region['SubDimensionSetups']['TilesSetup']['SubDimensionSetups']['MultiTrackSetup']['SubDimensionSetups']['ZStackSetup']['Interval']['Distance']
    #     dict_json['axial_resolution'] = float(zdis_hier['Value'])*default_corr_to_cytokit_units
    #     # compare to axial_resolution from Distance tag Z-distance
    #     dist_hier = d_meta['Scaling']['Items']['Distance']
    #     for i_dim in range(len(dist_hier)):
    #         if dist_hier[i_dim]['@Id'] == 'Z':
    #             axial_resolution = float(dist_hier[i_dim]['Value']) * default_corr_to_cytokit_units
    #     if dict_json['axial_resolution'] != axial_resolution:
    #         raise Exception('Axial resolutions inferred from two independent spots'
    #                         ' are not the same! Please check!')
    #
    #     # Lateral_resolution = pixelsize / magnification
    #     pixelsize_str = d_meta['ImageScaling']['ImagePixelSize']
    #     pixelsize_map = map(float, pixelsize_str.split(','))
    #     pixelsize = list(pixelsize_map)
    #     if pixelsize[0] == pixelsize[1]:
    #          dict_json['lateral_resolution'] = \
    #              pixelsize[0]/float(dict_json['magnification'])*\
    #              1e-6*default_corr_to_cytokit_units
    #     else:
    #         raise Exception('Pixelsize is not squared, does this make sense?')
    #     # compare to Lateral_resolution from Distance tag
    #     for i_dim in range(len(dist_hier)):
    #         if dist_hier[i_dim]['@Id'] == 'X':
    #             lat_resolutionx = float(
    #                 dist_hier[i_dim]['Value']) * default_corr_to_cytokit_units
    #         if dist_hier[i_dim]['@Id'] == 'Y':
    #             lat_resolutiony = float(
    #                 dist_hier[i_dim]['Value']) * default_corr_to_cytokit_units
    #
    #     if lat_resolutionx != lat_resolutiony:
    #         raise Exception('Distance x resolution does not equal Distance y resolution.'
    #                         'Please check!')
    #     if dict_json['lateral_resolution'] != lat_resolutionx:
    #         raise Exception('Computed lateral resolution and shown in X-Distance is not '
    #                         'the same! Please check!')
    #
    #
    #
    # # --------- WRITE FILES ------------------------------------------------
    # # Write channelnames.txt
    # # file_object = open(os.path.join(outdir, 'channelnames.txt'), 'w')
    # #
    # # ch_content = [dict_json['per_cycle_channel_names']]
    # # file_object.writelines(ch_content)
    # # file_object.close()
    #
    # # Write exposure_times.txt
    # # todo
    #
    #
    #
    #
    #
    # if not old:
    #     # Write yaml file
    #     file_object = open(outdir + basename[:-2] + '.yaml', 'w')
    #     yaml_content = ['date: \n',
    #                     'environment:\n',
    #                     '  path_formats: keyence_multi_cycle_v01\n',
    #                     'acquisition:\n',
    #                     '  per_cycle_channel_names: [' + dict_json['per_cycle_channel_names'] +']\n',
    #                     '  channel_names: [DAPI, blank, blank, blank, DAPI, cy3-ki67, cy5-CD107a, cy7-CD20, DAPI, cy3-cd8, cy5-CD45a, cy7-PanCK, DAPI, blank, blank, blank]\n',
    #                     '  emission_wavelengths: ['+ dict_json['emission_wavelengths'] +']\n',
    #                     '  axial_resolution: '+ str(dict_json['axial_resolution']) +'\n',
    #                     '  lateral_resolution: '+ str(dict_json['lateral_resolution']) +'\n',
    #                     '  magnification: '+ dict_json['magnification'] +'\n',
    #                     '  num_cycles: ' + str(dict_json['num_cycles']) + '\n',
    #                     '  numerical_aperture: '+ dict_json['numerical_aperture'] +'\n',
    #                     '  objective_type: '+ dict_json['objective_type'] +'\n',
    #                     '  region_names: ['+dict_json['region_names'] +']\n',
    #                     '  region_height: '+ str(dict_json['region_height']) +'\n',
    #                     '  region_width: '+ str(dict_json['region_width']) +'\n',
    #                     '  tile_height: '+ str(dict_json['tile_height'])+'\n',
    #                     '  tile_overlap_x: '+ str(dict_json['tile_overlap_x']) +'\n',
    #                     '  tile_overlap_y: '+ str(dict_json['tile_overlap_y']) +'\n',
    #                     '  tile_width: '+ str(dict_json['tile_width']) +'\n',
    #                     '  tiling_mode: '+ tiling_mode + '\n']
    #
    #     file_object.writelines(yaml_content)
    #     file_object.close()

    return
