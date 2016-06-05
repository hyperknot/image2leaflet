#!/usr/bin/env python

import sys
import os
import math
import shutil

from osgeo import gdal


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def gen_tile_path(subfolder, ext, x, y, zoom):
    output_folder_name = os.path.join(subfolder, str(zoom), str(x))
    output_file_path = os.path.join(output_folder_name, '{}.{}'.format(y, ext.lower()))
    return output_file_path, output_folder_name


def delete_dir(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)


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


def process_max_level(zoom_info, subfolder, gd_orig, width, height, tilebands, mem_drv, out_drv):
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
            output_file_name, output_folder_name = gen_tile_path(subfolder, 'png', x, y, zoom)
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


def process_lower_levels(dst_level, zoom_info, subfolder, tilebands, mem_drv, out_drv):
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
            output_file_name, output_folder_name = gen_tile_path(subfolder, 'png', dst_x, dst_y, dst_zoom)
            ensure_dir(output_folder_name)

            dsquery = mem_drv.Create('', 2 * tilesize, 2 * tilesize, tilebands)
            dstile = mem_drv.Create('', tilesize, tilesize, tilebands)

            # read lower levels
            for plus_x in range(2):
                src_x = dst_x + plus_x
                if src_x >= src_tile_count_x:
                    continue

                for plus_y in range(2):
                    src_y = dst_y + plus_y
                    if src_y >= src_tile_count_y:
                        continue

                    src_file_path, _ = gen_tile_path(subfolder, 'png', src_x, src_y, src_zoom)

                    dsquerytile = gdal.Open(src_file_path, gdal.GA_ReadOnly)
                    dsquery.WriteRaster(plus_x * tilesize, plus_y * tilesize, tilesize, tilesize,
                                        dsquerytile.ReadRaster(0, 0, tilesize, tilesize))

            # resample image
            dsquery.SetGeoTransform((0.0, 0.5, 0.0, 0.0, 0.0, 0.5))
            dstile.SetGeoTransform((0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
            res = gdal.ReprojectImage(dsquery, dstile, None, None, gdal.GRA_Lanczos)
            assert res == 0

            out_drv.CreateCopy(output_file_name, dstile, strict=0)
            os.remove(output_file_name + '.aux.xml')

            # count += 1
            # print count, dst_tile_count_total


def process_image(input_file_path, subfolder=None):
    input_file_path = os.path.abspath(input_file_path)

    if not subfolder:
        basename = os.path.splitext(os.path.basename(input_file_path))[0]
        subfolder = os.path.join(os.path.dirname(input_file_path), basename)

    subfolder = os.path.abspath(subfolder)

    gdal.AllRegister()
    out_drv = gdal.GetDriverByName('PNG')
    mem_drv = gdal.GetDriverByName('MEM')

    if not out_drv or not mem_drv:
        sys.exit('driver not found')

    gd_orig = gdal.Open(input_file_path, gdal.GA_ReadOnly)

    if not gd_orig:
        sys.exit('cannot open input file')

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



tilesize = 256
input_file_path = 'P5167614.JPG'

process_image(input_file_path)
