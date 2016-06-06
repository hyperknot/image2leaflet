import os
import jinja2

from osgeo import gdal

from .tiles import make_zoom_info, process_max_level, process_lower_levels, convert_jpgs
from .utils import delete_dir, read_file_contents, write_file_contents



def process_image(input_file_path, ext='jpg', subfolder=None):
    input_file_path = os.path.abspath(input_file_path)
    if not os.path.isfile(input_file_path):
        raise ValueError('Input file does not exists')

    basename = os.path.splitext(os.path.basename(input_file_path))[0]

    if not subfolder:
        subfolder = os.path.join(os.path.dirname(input_file_path), basename)

    ext = ext.lower()
    if ext == 'png':
        out_drv_str = 'PNG'
    elif ext == 'jpg':
        out_drv_str = 'BMP'
    else:
        raise ValueError('Output extension must be JPG or PNG')

    subfolder = os.path.abspath(subfolder)

    gdal.AllRegister()

    out_drv = gdal.GetDriverByName(out_drv_str)
    mem_drv = gdal.GetDriverByName('MEM')

    if not out_drv or not mem_drv:
        raise ValueError('Driver not found')

    gd_orig = gdal.Open(input_file_path, gdal.GA_ReadOnly)

    if not gd_orig:
        raise ValueError('Cannot open input file')

    width = gd_orig.RasterXSize
    height = gd_orig.RasterYSize
    tilebands = gd_orig.RasterCount

    print('Input file: {}x{} pixels, {} bands'.format(width, height, tilebands))

    zoom_info = make_zoom_info(width, height)

    delete_dir(subfolder)

    print('Generating zoom level: {}'.format(zoom_info[-1]['zoom']))
    process_max_level(zoom_info, subfolder, gd_orig, width, height, tilebands, mem_drv, out_drv, out_drv_str.lower())

    for dst_level in range(len(zoom_info) - 2, -1, -1):
        print('Generating zoom level: {}'.format(dst_level))
        process_lower_levels(dst_level, zoom_info, subfolder, tilebands, mem_drv, out_drv, out_drv_str.lower())

    if ext == 'jpg':
        print('Converting JPGs')
        convert_jpgs(zoom_info, subfolder, out_drv_str)

    print('Generating index.html')
    generate_index_html(width, height, ext, basename, subfolder)

    print('Done')


def generate_index_html(width, height, ext, title, subfolder):
    templates_folder = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(templates_folder, 'templates', 'index.html')

    template_str = read_file_contents(template_path)

    template = jinja2.Template(template_str)
    rendered_str = template.render(width=width, height=height, ext=ext, title=title)

    rendered_path = os.path.join(subfolder, 'index.html')
    write_file_contents(rendered_path, rendered_str)





