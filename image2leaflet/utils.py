import os
import shutil
import subprocess
import codecs


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def delete_dir(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)


def run_cmd(cmd):
    process = subprocess.Popen(cmd, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()
    returncode = process.returncode
    return stdout, stderr, returncode


def get_path_by_which(progname):
    if not progname:
        raise ValueError

    o, _, rc = run_cmd(u'which {}'.format(progname))
    if rc == 0:
        return o.strip()
    else:
        raise ValueError(u'Program not found by which: {}'.format(progname))


def get_path_by_list(progname, path_list):
    try:
        path = get_path_by_which(progname)
        return path

    except Exception:
        for item in path_list:
            if os.path.exists(item):
                return item

        raise ValueError(u'Program not found by list: {}'.format(progname))



def read_file_contents(path, encoding=True):
    if os.path.exists(path):
        if encoding:
            with codecs.open(path, encoding='utf-8') as infile:
                return infile.read().strip()
        else:
            with open(path) as infile:
                return infile.read().strip()


def write_file_contents(path, data, encoding=True):
    if encoding:
        with codecs.open(path, 'w', encoding='utf-8') as outfile:
            outfile.write(data)
    else:
        with open(path, 'w') as outfile:
            outfile.write(data)

