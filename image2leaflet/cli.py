import click

from .process import process_image


@click.command()
@click.argument('input_file')
@click.option('--output', '-o', help='output directory')
def main(input_file, output):
    """Converts an image file to a Leaflet map."""

    process_image(input_file, output)
