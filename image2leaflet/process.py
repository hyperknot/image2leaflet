import os
import sys

from osgeo import gdal

from .tiles import make_zoom_info, process_max_level, process_lower_levels
from .utils import delete_dir


def process_image(input_file_path, subfolder=None):
    input_file_path = os.path.abspath(input_file_path)
    if not os.path.isfile(input_file_path):
        sys.exit('Input file does not exists')

    if not subfolder:
        basename = os.path.splitext(os.path.basename(input_file_path))[0]
        subfolder = os.path.join(os.path.dirname(input_file_path), basename)

    subfolder = os.path.abspath(subfolder)

    gdal.AllRegister()
    out_drv = gdal.GetDriverByName('PNG')
    mem_drv = gdal.GetDriverByName('MEM')

    if not out_drv or not mem_drv:
        sys.exit('Driver not found')

    gd_orig = gdal.Open(input_file_path, gdal.GA_ReadOnly)

    if not gd_orig:
        sys.exit('Cannot open input file')

    width = gd_orig.RasterXSize
    height = gd_orig.RasterYSize
    tilebands = gd_orig.RasterCount

    print('Input file: {}x{} pixels, {} bands'.format(width, height, tilebands))

    zoom_info = make_zoom_info(width, height)

    delete_dir(subfolder)

    print('Generating zoom level: {}'.format(zoom_info[-1]['zoom']))
    process_max_level(zoom_info, subfolder, gd_orig, width, height, tilebands, mem_drv, out_drv)

    for dst_level in range(len(zoom_info) - 2, 0, -1):
        print('Generating zoom level: {}'.format(dst_level))
        process_lower_levels(dst_level, zoom_info, subfolder, tilebands, mem_drv, out_drv)

    print('Done')


