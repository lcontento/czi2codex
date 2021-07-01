import os
import tifffile
import glob
import warnings
from xml.etree import ElementTree
from itertools import product
from aicspylibczi import CziFile
import xmltodict
from lxml import etree


def extension(path: str, *, lower: bool = True):
    _, ext = os.path.splitext(path)
    return ext.lower() if lower else ext


def replace_extension(path: str, ext: str):
    base, _ = os.path.splitext(path)
    return base + os.path.extsep + ext


def write_exposure_times(meta_dict, i_cycle, outdir,
                         overwrite_exposure=False):
    """Write exposure_times.txt. Infer the exposure times from given meta-xml
    given in dictionary format.
    Return path to saved exposure_times.txt file."""
    # Metadata►Information►Image►Dimensions►Channels►Channel►0►ExposureTime
    d_channel = meta_dict['ImageDocument']['Metadata']['Information']['Image'][
        'Dimensions']['Channels']['Channel']
    exptime = []
    default_scaling = 1E6
    for i in range(len(d_channel)):
        etime = float(d_channel[i]['ExposureTime'])/default_scaling
        if etime.is_integer():
            exptime.append(int(etime))
        else:
            exptime.append(etime)

    exp_filename = 'exposure_times.txt'
    # Check if exposure_times.txt already exist
    if os.path.exists(os.path.join(outdir, exp_filename)) and \
            overwrite_exposure is False:
        if i_cycle == 1:
            warnings.warn(
                f'\nWARNING: Exposure times file {exp_filename} already exist. '
                f'If it shall be replaced, define: overwrite_exposure_times: '
                f'true')
    else:
        if os.path.exists(os.path.join(outdir, exp_filename)) and \
                overwrite_exposure and i_cycle == 1:
            os.remove(os.path.join(outdir, exp_filename))
        # write exposure_times.txt file
        with open(os.path.join(outdir, exp_filename), 'a') as filehandle:
            if i_cycle == 1:
                filehandle.write('Cycle,CH1,CH2,CH3,CH4 \n')
            filehandle.write(str(i_cycle))
            for listitem in exptime:
                filehandle.write(',%s' % listitem)
            filehandle.write('\n')

    exptime_path = os.path.join(outdir, exp_filename)
    return exptime_path


# channel start from 1!!!
def czi_to_tiffs(czidir: str,
                 outdir: str,
                 template: str = '1_{m:05}_Z{z:03}_CH{c:03}',
                 overwrite_exposure: bool = False,
                 #'1_{m}_Z{z}_CH{c}',
                 *,
                 compression: str = 'zlib',
                 save_tile_metadata: bool = False):
    """
    Reads czi files and converts them to tifs. Furthermore exposure_times.txt
    files are created.
    Parameters:
    -----------
    czidir: str
        directory of czi-files, with filename-template for the
        different cycles (e.g. '/dir/to/czifiles/filename_CYC{:02}.czi')
    outdir: str
        output directory, where everything should be saved
    template: str
        output-filenaming template, default is: '1_{m:05}_Z{z:03}_CH{c:03}'
    overwrite_exposure: bool
        if exposure_times.txt already exists, should it be overwritten or not?
    compression: str
        tiffile-compression
    save_tile_metadata: bool
        save metadata for each tile?
    Returns:
    --------
    C - Channels
    Z - Z-Planes
    tiles
    meta: lxml.etree._Element
        metadata-object
    tile_meta:
        metadata for each tile
    """
    print('.......................................')
    print('Starting to run conversion czi to tifs.')
    czi_filename, czi_ext = os.path.splitext(os.path.basename(czidir))
    basedir = os.path.dirname(czidir)
    # list of czi-files
    czi_files = glob.glob(os.path.join(basedir, '*' + czi_ext))
    num_cycles = len(czi_files)
    if num_cycles==0:
        raise FileNotFoundError('No czi-files where found in the '
                                'user specified directory: \n' + czidir +
                                '\n Please check the defined directory '
                                '"1_czidir" in the options.yaml file.')

    # loop over cycles
    for i_cyc in range(1, num_cycles+1):
        # name of czi file without .czi extension
        basename = czi_filename.format(i_cyc)

        czi = CziFile(os.path.join(basedir, basename + czi_ext))

        # output dir and foldername
        if not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)
        foldername = 'cyc{:03}_reg001'.format(int(basename[-2:]))  # Cyc{cycle:d}_reg{region:d}
        if not os.path.exists(os.path.join(outdir, foldername)):
            os.makedirs(os.path.join(outdir, foldername), exist_ok=True)

        # Extract and check dimensions
        # S: scene
        # T: time
        # C: channel
        # Z: focus position
        # M: tile index in a mosaic
        # Y, X: tile dimensions
        if czi.dims != 'STCZMYX':
            raise Exception('unexpected dimension ordering')
        # Scene, Timepoints, Channels, Z-slices, Mosaic, Height, Width
        S, T, C, Z, M, Y, X = czi.size
        if S != 1:
            raise Exception('only one scene expected')
        if T != 1:
            raise Exception('only one timepoint expected')

        # Check zero-based indexing
        dims_shape, = czi.dims_shape()
        # dims_shape is a dictionary which maps each dimension to its index
        # range
        for axis in dims_shape.values():
            if axis[0] != 0:
                raise Exception('expected zero-based indexing in CZI file')

        if not czi.is_mosaic():
            raise Exception('expected a mosaic image')

        # Save tiles
        tiles = []
        tile_meta = {}
        for m in range(M):
            # Get tile position
            tilepos = czi.read_subblock_rect(S=0, T=0, C=0, Z=0, M=m) # returns: (x, y, w, h)
            tiles.append(tilepos)
            # Iterate over channel and focus
            for (c, z) in product(range(C), range(Z)):
                # Get tile position
                cur_tilepos = czi.read_subblock_rect(S=0, T=0, C=c, Z=z, M=m)
                if cur_tilepos != tilepos:
                    raise Exception('tile rect expected to be independent of Z and'
                                    ' C dimensions')
                # Get tile metadata
                # _, cur_tile_meta = czi.read_subblock_metadata(unified_xml=True,
                # S=0, T=0, C=c, Z=z, M=m)#[0]
                cur_tile_meta = czi.read_subblock_metadata(unified_xml=True, S=0,
                                                           T=0, C=c, Z=z, M=m)
                # tile_meta[(c, z, m)] = cur_tile_meta[1]
                # Save tile as tiff
                # filename = template.format(c=c, z=z, m=m, basename=basename)
                # filename = os.path.join(outdir, filename)

                filename = template.format(c=c+1, z=z+1, m=m+1) # Codex format starts at 1!
                filename = os.path.join(outdir, foldername, filename)
                tile_data, tile_shape = czi.read_image(S=0, T=0, C=c, Z=z, M=m)
                tifffile.imwrite(filename + '.tif', tile_data, compression=compression)
                # Save tile metadata
                if save_tile_metadata:
                    cur_tile_meta.getroottree().write(filename + '.xml')

        # Extract & save metadata
        meta = czi.meta
        with open(os.path.join(outdir, basename + '.xml'), 'w') as f:
            f.write(ElementTree.tostring(meta, encoding='unicode'))

        # save exposure_times.txt for each cycle
        meta_dict = xmltodict.parse(etree.tostring(meta))

        if i_cyc == 1:
            print('Starting to write the exposure.txt file. \n'
                  f'Cycle = {str(i_cyc)}')
        else:
            print(f'Cycle = {str(i_cyc)}')
        write_exposure_times(meta_dict, i_cyc, outdir,
                             overwrite_exposure)

    print(f"...finished generation of .tif files and exposure.txt file! ...\n"
          f"...Saved in {outdir}")

    # Return shape and metadata
    return C, Z, tiles, meta, tile_meta
