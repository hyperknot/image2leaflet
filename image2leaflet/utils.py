import os
import shutil


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def delete_dir(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
