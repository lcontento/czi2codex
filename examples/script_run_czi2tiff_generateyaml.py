import czi2tif_codex
import generate_metadata_json

# convert czi to tiff
image_path = '/home/erika/Documents/Projects/CODEX/Data/Collaborators_OriginalData/' \
             '20200708 Tonsil_beta_after2_compressed/' \
             '2020.07.08 Tonsil_betaTEST_sfter2-04.czi'
outdir = '/home/erika/Documents/Projects/CODEX/Data/test_czi2codex/'
template = '1_{m:05}_Z{z:03}_CH{c:03}'
C, Z, tiles, meta, tile_meta = czi2tif_codex.czi_to_tiffs(image_path, outdir,
                                                          template)
##
# generate experiment.json file from xml
# path_meta_xml = '/home/erika/Documents/Projects/CODEX/Data/' \
#                 '2020.07.08 Tonsil_betaTEST_sfter2-01.xml'
# path_meta_xml = '/home/erika/Documents/Projects/CODEX/Data/test_czi2codex/' \
#                 '2020.07.08 Tonsil_betaTEST_sfter2-04.xml'
path_meta_xml = meta
image_path = '/home/erika/Documents/Projects/CODEX/Data/Collaborators_OriginalData/' \
             '20200708 Tonsil_beta_after2_compressed/' \
             '2020.07.08 Tonsil_betaTEST_sfter2-04.czi'

outdir = '/home/erika/Documents/Projects/CODEX/Data/test_czi2codex/'
channelnames = '/home/erika/Documents/Projects/CODEX/Data/test_czi2codex/' \
               'ORIGINAL_FILES/channelNamesSONIA.txt'
exposuretime = '/home/erika/Documents/Projects/CODEX/Data/test_czi2codex/' \
               'ORIGINAL_FILES/exposure_timesSONIA.txt'

generate_metadata_json.meta_to_json(path_meta_xml, image_path, outdir,
                                    channelnames, exposuretime)
