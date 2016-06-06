import click
import sys

from .process import process_image


@click.command()
@click.argument('input_file')
@click.option('--output', '-o', help='output directory')
@click.option('--format', '-f', default='jpg', help='output format (JPG/PNG)')
def main(input_file, output, format):
    """Converts an image file to a Leaflet map."""

    try:
        process_image(input_file, subfolder=output, ext=format)
    except Exception as e:
        sys.exit(e)
