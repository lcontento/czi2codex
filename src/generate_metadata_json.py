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
    files_czi = glob.glob(os.path.join(path_czi_files, '*.czi'))
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
    with open(os.path.join(outdir, 'experiment.json'), 'w',
              encoding='utf-8') as json_file:
        json.dump(dict_json, json_file, ensure_ascii=False, indent=4)
    print('.....finished writing experiment.json file!.....')

    return
