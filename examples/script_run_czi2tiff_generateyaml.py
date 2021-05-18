import czi2tif_codex
import generate_yaml
#

# convert czi to tiff
image_path = '/home/erika/Documents/Projects/CODEX/Data/' \
             '20200708 Tonsil_beta_after2_compressed/' \
             '2020.07.08 Tonsil_betaTEST_sfter2-04.czi'
outdir = '/home/erika/Documents/Projects/CODEX/Data/test_czi2codex/'
template = '1_{m}_Z{z}_CH{c}'
C, Z, tiles, meta, tile_meta = czi2tif_codex.czi_to_tiffs(image_path, outdir,
                                                          template)
#

# generate yaml file from xml
path_meta_xml = '/home/erika/Documents/Projects/CODEX/Data/' \
                '2020.07.08 Tonsil_betaTEST_sfter2-01.xml'
path_czi_files = '/home/erika/Documents/Projects/CODEX/Data/' \
                 '20200708 Tonsil_beta_after2_compressed/'
outdir = '/home/erika/Documents/Projects/CODEX/Data/'

# generate_yaml.meta_to_yaml(path_meta_xml, path_czi_files, outdir)
