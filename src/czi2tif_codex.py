import os
import tifffile

from xml.etree import ElementTree
from itertools import product
from aicspylibczi import CziFile


def extension(path: str, *, lower: bool = True):
    _, ext = os.path.splitext(path)
    return ext.lower() if lower else ext


def replace_extension(path: str, ext: str):
    base, _ = os.path.splitext(path)
    return base + os.path.extsep + ext

# savefile should be in format:
# {region:d}_{tile:05d}_Z{z:03d}_CH{channel:d}.tif
# (-> keyence_single_cycle_v01)
# for multiple cycles:
# Cyc{cycle:d}_reg{region:d}/{region:d}_{tile:05d}_Z{z:03d}_CH{channel:d}.tif
# (-> keyence_multi_cycle_v01)
# see cytokit/python/pipeline/cytokit/io.py
# (before: template: str = '{basename}_M{m}_C{c}_Z{z}')


# TODO: filenames: channel should start from 1!!!
def czi_to_tiffs(path: str,
                 outdir: str,
                 template: str = '1_{m:05}_Z{z:03}_CH{c:03}',
                 #'1_{m}_Z{z}_CH{c}',
                 *,
                 compression: str = 'zlib',
                 save_tile_metadata: bool = False):

    basename, _ = os.path.splitext(os.path.basename(path))
    if not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)
    if not os.path.exists(outdir + 'Cyc' + basename[-2:] + '_reg1'):
        os.makedirs(outdir + 'Cyc' + basename[-2:] + '_reg1', exist_ok=True)

    czi = CziFile(path)

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
    # dims_shape is a dictionary which maps each dimension to its index range
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
            foldername = 'Cyc' + basename[-2:] + '_reg1' # Cyc{cycle:d}_reg{region:d}
            filename = os.path.join(outdir, foldername, filename)
            tile_data, tile_shape = czi.read_image(S=0, T=0, C=c, Z=z, M=m)
            tifffile.imwrite(filename + '.tif', tile_data, compression=compression)
            # Save tile metadata
            if save_tile_metadata:
                cur_tile_meta.getroottree().write(filename + '.xml')

    # Extract metadata
    meta = czi.meta
    with open(os.path.join(outdir, basename + '.xml'), 'w') as f:
        f.write(ElementTree.tostring(meta, encoding='unicode'))

    # Return shape and metadata
    return C, Z, tiles, meta, tile_meta