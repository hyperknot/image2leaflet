import os
import sys
import math

from osgeo import gdal
from .utils import ensure_dir, get_path_by_list, run_cmd

tilesize = 256

try:
    mozjpeg_path = get_path_by_list(None, ['/usr/local/opt/mozjpeg/bin/cjpeg', r'C:\Program Files (x86)\mozjpeg\cjpeg.exe'])
except Exception:
    sys.exit('mozjpeg missing, please install mozjpeg')


def gen_tile_path(subfolder, ext, x, y, zoom):
    output_folder_name = os.path.join(subfolder, str(zoom), str(x))
    output_file_path = os.path.join(output_folder_name, '{}.{}'.format(y, ext.lower()))
    return output_file_path, output_folder_name


def make_zoom_info(width, height):
    larger_side_size = max(width, height)
    max_native_zoom = int(math.ceil(math.log(larger_side_size / float(tilesize), 2)))

    zoom_info = list()

    for zoom in range(0, max_native_zoom + 1):
        coverage = 2 ** zoom * tilesize
        meta_size = 2 ** (max_native_zoom - zoom) * tilesize

        meta_width_float = width / 2.0 ** (max_native_zoom - zoom)
        meta_height_float = height / 2.0 ** (max_native_zoom - zoom)

        zoom_data = {
            'zoom': zoom,
            'coverage': coverage,
            'meta_size': meta_size,
            'meta_width_float': meta_width_float,
            'meta_height_float': meta_height_float,
            'meta_width_crop': int(meta_width_float),
            'meta_height_crop': int(meta_height_float),
            'tile_x': int(math.ceil(width / float(meta_size))) - 1,
            'tile_y': int(math.ceil(height / float(meta_size))) - 1,
        }

        zoom_info.append(zoom_data)

    from pprint import pprint
    pprint(zoom_info)

    return zoom_info


def process_max_level(zoom_info, subfolder, orig_gd, width, height, tilebands, mem_drv, out_drv, ext):
    level = -1
    zoom = zoom_info[level]['zoom']
    tile_count_x = zoom_info[level]['tile_x'] + 1
    tile_count_y = zoom_info[level]['tile_y'] + 1
    # tile_count_total = tile_count_x * tile_count_y

    # count = 0

    for x in range(tile_count_x):
        # calculate dst_x, dst_width
        dst_x = x * tilesize
        if x == tile_count_x - 1:
            dst_width = width % tilesize
        else:
            dst_width = tilesize

        for y in range(tile_count_y):
            output_file_name, output_folder_name = gen_tile_path(subfolder, ext, x, y, zoom)
            ensure_dir(output_folder_name)

            # calculate dst_y, dst_height
            dst_y = y * tilesize
            if y == tile_count_y - 1:
                dst_height = height % tilesize
            else:
                dst_height = tilesize

            dst_gd = mem_drv.Create('', dst_width, dst_height, tilebands)
            data = orig_gd.ReadRaster(dst_x, dst_y, dst_width, dst_height, dst_width, dst_height)

            dst_gd.WriteRaster(0, 0, dst_width, dst_height, data)
            out_drv.CreateCopy(output_file_name, dst_gd, strict=0)

            # count += 1
            # print count, tile_count_total


def process_lower_levels(dst_level, zoom_info, subfolder, tilebands, mem_drv, out_drv, ext):
    dst_zoom = zoom_info[dst_level]['zoom']
    assert dst_zoom == dst_level

    dst_tile_count_x = zoom_info[dst_level]['tile_x'] + 1
    dst_tile_count_y = zoom_info[dst_level]['tile_y'] + 1
    dst_meta_width_crop = zoom_info[dst_level]['meta_width_crop']
    dst_meta_height_crop = zoom_info[dst_level]['meta_height_crop']

    # dst_tile_count_total = dst_tile_count_x * dst_tile_count_y

    src_level = dst_level + 1
    src_zoom = zoom_info[src_level]['zoom']
    src_tile_count_x = zoom_info[src_level]['tile_x'] + 1
    src_tile_count_y = zoom_info[src_level]['tile_y'] + 1

    # count = 0

    for dst_x in range(dst_tile_count_x):
        if dst_x == dst_tile_count_x - 1:
            dst_width = dst_meta_width_crop % tilesize
        else:
            dst_width = tilesize

        for dst_y in range(dst_tile_count_y):
            output_file_name, output_folder_name = gen_tile_path(subfolder, ext, dst_x, dst_y, dst_zoom)
            ensure_dir(output_folder_name)

            if dst_y == dst_tile_count_y - 1:
                dst_height = dst_meta_height_crop % tilesize
            else:
                dst_height = tilesize

            dst_gd_1x = mem_drv.Create('', dst_width, dst_height, tilebands)
            dst_gd_2x = mem_drv.Create('', 2 * dst_width, 2 * dst_height, tilebands)

            # read lower levels
            for plus_x in range(2):
                src_x = 2 * dst_x + plus_x
                if src_x >= src_tile_count_x:
                    continue

                for plus_y in range(2):
                    src_y = 2 * dst_y + plus_y
                    if src_y >= src_tile_count_y:
                        continue

                    src_file_path, _ = gen_tile_path(subfolder, ext, src_x, src_y, src_zoom)
                    src_gd = gdal.Open(src_file_path, gdal.GA_ReadOnly)

                    data = src_gd.ReadRaster(0, 0, src_gd.RasterXSize, src_gd.RasterYSize)
                    dst_gd_2x.WriteRaster(plus_x * tilesize,
                                          plus_y * tilesize,
                                          src_gd.RasterXSize, src_gd.RasterYSize,
                                          data)

            # resample image
            dst_gd_2x.SetGeoTransform((0.0, 0.5, 0.0, 0.0, 0.0, 0.5))
            dst_gd_1x.SetGeoTransform((0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
            res = gdal.ReprojectImage(dst_gd_2x, dst_gd_1x, None, None, gdal.GRA_Lanczos)
            assert res == 0

            out_drv.CreateCopy(output_file_name, dst_gd_1x, strict=0)

            if ext == 'png':
                os.remove(output_file_name + '.aux.xml')

            # count += 1
            # print count, dst_tile_count_total


def convert_jpgs(zoom_info, subfolder, out_drv_str, jpg_quality=70):
    for level_data in zoom_info:
        zoom = level_data['zoom']
        for x in range(level_data['tile_x'] + 1):
            for y in range(level_data['tile_y'] + 1):
                bmp_file = gen_tile_path(subfolder, out_drv_str.lower(), x, y, zoom)[0]
                jpg_file = gen_tile_path(subfolder, 'jpg', x, y, zoom)[0]

                mozjpeg_cmd = u'"{mozjpeg_path}" -outfile "{dst}" -quality {jpg_quality} "{src}"'.format(
                    mozjpeg_path=mozjpeg_path, dst=jpg_file, src=bmp_file, jpg_quality=jpg_quality)

                _, e, rc = run_cmd(mozjpeg_cmd)
                if rc != 0:
                    raise ValueError(u'error with jpg compression step: {}'.format(e))

                os.remove(bmp_file)
