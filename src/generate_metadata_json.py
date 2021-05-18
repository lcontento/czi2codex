# reads from metadata-xml and generates yaml file for the use of cytokit
import os
import glob
import xmltodict
from aicspylibczi import CziFile
import numpy as np

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


def meta_to_yaml(path_meta_xml: str, path_czi_files: str, outdir: str):
    """
    path_meta_xml: str
        directory of the xml-metafile
    path_czi_files: str
        folder directory where the czi files are located
    outdir: str
        where to save yaml file
    """

    basename, _ = os.path.splitext(os.path.basename(path_meta_xml))
    tiling_mode = 'grid'

    with open(path_meta_xml, 'r') as f:
        contents = f.read()
    d = xmltodict.parse(contents)

    # Dictionary with all entries for yaml file
    dict_yaml_entries = {}

    # Per_cycle_channel_names & Emission wavelength
    channel_names = []
    em_wv = []
    channel_hier = d['ImageDocument']['Metadata']['Information']['Image']['Dimensions']['Channels']['Channel']
    for i_c in range(len(channel_hier)):
        channel_names.append(channel_hier[i_c]['@Name'])
        em_wv.append(channel_hier[i_c]['EmissionWavelength'])

    dict_yaml_entries['per_cycle_channel_names'] = ', '.join(map(str,channel_names))
    dict_yaml_entries['emission_wavelengths'] = ', '.join(map(str,em_wv))

    # Magnification & Objective-type & Numerical Aperture
    obj_hier = d['ImageDocument']['Metadata']['Information']['Instrument']['Objectives']['Objective']
    dict_yaml_entries['magnification'] = obj_hier['NominalMagnification']
    dict_yaml_entries['objective_type'] = obj_hier['Immersion']
    dict_yaml_entries['numerical_aperture'] = obj_hier['LensNA']

    # Tile_height, tile_width
    region_hier = d['ImageDocument']['Metadata']['Experiment']['ExperimentBlocks']['AcquisitionBlock']['SubDimensionSetups']['RegionsSetup']

    # dict_yaml_entries['tile_width']  = float(region_hier['SampleHolder']['TileDimension']['Width'])  -> 665.6 undefined unit
    # dict_yaml_entries['tile_height'] = float(region_hier['SampleHolder']['TileDimension']['Height'])
    # Region name
    dict_yaml_entries['region_names'] = region_hier['SampleHolder']['TileRegions']['TileRegion']['@Name']
    dict_yaml_entries['region_height'] = int(region_hier['SampleHolder']['TileRegions']['TileRegion']['Rows'])
    dict_yaml_entries['region_width'] = int(region_hier['SampleHolder']['TileRegions']['TileRegion']['Columns'])

    # Tile_overlap_x & tile_overlap_y calculate with overlap percentage * pixel size
    # overlap_perc = float(region_hier['SampleHolder']['Overlap'])
    # camera_hier = d['ImageDocument']['Metadata']['Experiment']['ExperimentBlocks']['AcquisitionBlock']['HelperSetups']['AcquisitionModeSetup']['Detectors']['Camera']
    # pixel_str = camera_hier['Frame']['#text']
    # pixel_map = map(int, pixel_str.split(','))
    # pixel = list(pixel_map)
    # pixel_width = pixel[2]
    # pixel_height = pixel[3]
    # dict_yaml_entries['tile_overlap_x'] =  pixel_width * overlap_perc
    # dict_yaml_entries['tile_overlap_y'] =  pixel_height * overlap_perc

    # Tile_overlap: calculate with read_subblock_rect
    czi = CziFile(path_czi_files + basename + '.czi')
    S, T, C, Z, M, Y, X = czi.size
    tilepos = []
    # Get tile position
    for m in range(M):
        tilepos.append(czi.read_subblock_rect(S=0, T=0, C=0, Z=0, M=m))
    dict_yaml_entries['tile_width'] = tilepos[0][2] # tile width
    dict_yaml_entries['tile_height'] = tilepos[0][3] # tile height
    tile_x_overl = []
    tile_y_overl = []
    if tiling_mode == 'grid':
        for i_x in range(dict_yaml_entries['region_width'] - 1):
            tile_x_overl.append((tilepos[i_x][0] + dict_yaml_entries['tile_width']) - tilepos[i_x + 1][0])
        for i_y in np.arange(0, M - dict_yaml_entries['region_width'],
                             dict_yaml_entries['region_width']):
            tile_y_overl.append((tilepos[i_y][1] + dict_yaml_entries['tile_height']) -
                                tilepos[i_y + dict_yaml_entries['region_width']][1])
    else:
        raise Exception('Calculation of tile overlaps for other tiling_modes'
                        '(than grid) not implemented yet. Please do so.')
    # TODO: (?) FOR NOW: TAKE THE OVERLAP BETWEEN THE FIRST TWO TILES (although there are
    # inconsistencies, we might need to check and incorporate! [205,205,205,204]
    dict_yaml_entries['tile_overlap_x'] = tile_x_overl[0]
    dict_yaml_entries['tile_overlap_y'] = tile_y_overl[0]

    # units in cytokit are in nanometers
    default_corr_to_cytokit_units = 1e9

    # Axial_resolution is the distance between Z layers
    zdis_hier = region_hier['SubDimensionSetups']['TilesSetup']['SubDimensionSetups']['MultiTrackSetup']['SubDimensionSetups']['ZStackSetup']['Interval']['Distance']
    dict_yaml_entries['axial_resolution'] = float(zdis_hier['Value'])*default_corr_to_cytokit_units
    # compare to axial_resolution from Distance tag Z-distance
    dist_hier = d['ImageDocument']['Metadata']['Scaling']['Items']['Distance']
    for i_dim in range(len(dist_hier)):
        if dist_hier[i_dim]['@Id'] == 'Z':
            axial_resolution = float(dist_hier[i_dim]['Value']) * default_corr_to_cytokit_units
    if dict_yaml_entries['axial_resolution']  != axial_resolution:
        raise Exception('Axial resolutions inferred from two independent spots are '
                        'not the same! Please check!')

    # Lateral_resolution = pixelsize  / magnification
    pixelsize_str = d['ImageDocument']['Metadata']['ImageScaling']['ImagePixelSize']
    pixelsize_map = map(float, pixelsize_str.split(','))
    pixelsize = list(pixelsize_map)
    if pixelsize[0] == pixelsize[1]:
         dict_yaml_entries['lateral_resolution'] = \
             pixelsize[0]/float(dict_yaml_entries['magnification'])*\
             1e-6*default_corr_to_cytokit_units
    else:
        raise Exception('Pixelsize is not squared, does this make sense?')
    # compare to Lateral_resolution from Distance tag
    for i_dim in range(len(dist_hier)):
        if dist_hier[i_dim]['@Id'] == 'X':
            lat_resolutionx = float(
                dist_hier[i_dim]['Value']) * default_corr_to_cytokit_units
        if dist_hier[i_dim]['@Id'] == 'Y':
            lat_resolutiony = float(
                dist_hier[i_dim]['Value']) * default_corr_to_cytokit_units

    if lat_resolutionx != lat_resolutiony:
        raise Exception('Distance x resolution does not equal Distance y resolution.'
                        'Please check!')
    if dict_yaml_entries['lateral_resolution'] != lat_resolutionx:
        raise Exception('Computed lateral resolution and shown in X-Distance is not '
                        'the same! Please check!')


    # how many cycles
    files_list = glob.glob(path_czi_files + '*.czi')
    dict_yaml_entries['num_cycles'] = len(files_list)


    # Write yaml file
    file_object  = open(outdir + basename[:-2] + '.yaml', 'w')
    yaml_content = ['date: \n',
                    'environment:\n',
                    '  path_formats: keyence_multi_cycle_v01\n',
                    'acquisition:\n',
                    '  per_cycle_channel_names: ['+ dict_yaml_entries['per_cycle_channel_names'] +']\n',
                    '  channel_names: [DAPI, blank, blank, blank, DAPI, cy3-ki67, cy5-CD107a, cy7-CD20, DAPI, cy3-cd8, cy5-CD45a, cy7-PanCK, DAPI, blank, blank, blank]\n',
                    '  emission_wavelengths: ['+ dict_yaml_entries['emission_wavelengths'] +']\n',
                    '  axial_resolution: '+ str(dict_yaml_entries['axial_resolution']) +'\n',
                    '  lateral_resolution: '+ str(dict_yaml_entries['lateral_resolution']) +'\n',
                    '  magnification: '+ dict_yaml_entries['magnification'] +'\n',
                    '  num_cycles: ' + str(dict_yaml_entries['num_cycles']) + '\n',
                    '  numerical_aperture: '+ dict_yaml_entries['numerical_aperture'] +'\n',
                    '  objective_type: '+ dict_yaml_entries['objective_type'] +'\n',
                    '  region_names: ['+dict_yaml_entries['region_names'] +']\n',
                    '  region_height: '+ str(dict_yaml_entries['region_height']) +'\n',
                    '  region_width: '+ str(dict_yaml_entries['region_width']) +'\n',
                    '  tile_height: '+ str(dict_yaml_entries['tile_height'])+'\n',
                    '  tile_overlap_x: '+ str(dict_yaml_entries['tile_overlap_x']) +'\n',
                    '  tile_overlap_y: '+ str(dict_yaml_entries['tile_overlap_y']) +'\n',
                    '  tile_width: '+ str(dict_yaml_entries['tile_width']) +'\n',
                    '  tiling_mode: '+ tiling_mode + '\n']

    file_object.writelines(yaml_content)
    file_object.close()

    return
