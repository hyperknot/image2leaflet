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

        zoom_data = {
            'zoom': zoom,
            'coverage': coverage,
            'meta_size': meta_size,
            'tile_x': int(math.ceil(width / float(meta_size))) - 1,
            'tile_y': int(math.ceil(height / float(meta_size))) - 1,
        }

        zoom_info.append(zoom_data)

    return zoom_info


def process_max_level(zoom_info, subfolder, gd_orig, width, height, tilebands, mem_drv, out_drv, ext):
    level = -1
    zoom = zoom_info[level]['zoom']
    tile_count_x = zoom_info[level]['tile_x'] + 1
    tile_count_y = zoom_info[level]['tile_y'] + 1
    # tile_count_total = tile_count_x * tile_count_y

    # count = 0

    for x in range(tile_count_x):
        # calculate rx, rxsize
        rx = x * tilesize
        if x == tile_count_x - 1:
            rxsize = width % tilesize
        else:
            rxsize = tilesize

        for y in range(tile_count_y):
            output_file_name, output_folder_name = gen_tile_path(subfolder, ext, x, y, zoom)
            ensure_dir(output_folder_name)

            # calculate ry, rysize
            ry = y * tilesize
            if y == tile_count_y - 1:
                rysize = height % tilesize
            else:
                rysize = tilesize

            dstile = mem_drv.Create('', tilesize, tilesize, tilebands)
            data = gd_orig.ReadRaster(rx, ry, rxsize, rysize, rxsize, rysize)

            dstile.WriteRaster(0, 0, rxsize, rysize, data)
            out_drv.CreateCopy(output_file_name, dstile, strict=0)

            # count += 1
            # print count, tile_count_total


def process_lower_levels(dst_level, zoom_info, subfolder, tilebands, mem_drv, out_drv, ext):
    dst_zoom = zoom_info[dst_level]['zoom']
    assert dst_zoom == dst_level

    dst_tile_count_x = zoom_info[dst_level]['tile_x'] + 1
    dst_tile_count_y = zoom_info[dst_level]['tile_y'] + 1
    # dst_tile_count_total = dst_tile_count_x * dst_tile_count_y

    src_level = dst_level + 1
    src_zoom = zoom_info[src_level]['zoom']
    src_tile_count_x = zoom_info[src_level]['tile_x'] + 1
    src_tile_count_y = zoom_info[src_level]['tile_y'] + 1

    # count = 0

    for dst_x in range(dst_tile_count_x):
        for dst_y in range(dst_tile_count_y):
            output_file_name, output_folder_name = gen_tile_path(subfolder, ext, dst_x, dst_y, dst_zoom)
            ensure_dir(output_folder_name)

            dsquery = mem_drv.Create('', 2 * tilesize, 2 * tilesize, tilebands)
            dstile = mem_drv.Create('', tilesize, tilesize, tilebands)

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

                    dsquerytile = gdal.Open(src_file_path, gdal.GA_ReadOnly)
                    dsquery.WriteRaster(plus_x * tilesize, plus_y * tilesize, tilesize, tilesize,
                                        dsquerytile.ReadRaster(0, 0, tilesize, tilesize))

            # resample image
            dsquery.SetGeoTransform((0.0, 0.5, 0.0, 0.0, 0.0, 0.5))
            dstile.SetGeoTransform((0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
            res = gdal.ReprojectImage(dsquery, dstile, None, None, gdal.GRA_Lanczos)
            assert res == 0

            out_drv.CreateCopy(output_file_name, dstile, strict=0)

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
