import numpy as np
import torch
import random
from src.components.objects.Logger import Logger
import datetime
from glob import glob
import shutil
import os


def set_global_configs(verbose, log_file_args, log_importance, log_format, random_seed, tile_progress_log_freq):
    Logger.set_default_logger(verbose, log_file_args, log_importance, log_format, tile_progress_log_freq)
    set_random_seed(random_seed)


def get_time():
    now = datetime.datetime.now()
    return now.strftime("%d-%m-%y_%H_%M_%S")


def set_random_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def bring_files(folder_in, file_format, folder_out):
    if not os.path.exists(folder_out):
        os.makedirs(folder_out)
    filepaths = glob(f"{folder_in}/**/{file_format}", recursive=True)
    for i, filepath in enumerate(filepaths):
        basename = os.path.basename(filepath)
        parent_dir = os.path.basename(os.path.dirname(filepath))
        shutil.copyfile(filepath, os.path.join(folder_out, f"{i}_{parent_dir}_{basename}"))


def bring_joined_log_file(folder_in, file_format, filepath_out):
    if os.path.isdir(os.path.dirname(filepath_out)) and not os.path.exists(os.path.dirname(filepath_out)):
        os.makedirs(os.path.dirname(filepath_out))
    filepaths = glob(f"{folder_in}/**/{file_format}", recursive=True)
    sep_line = f"\n{'-'*100}\n"
    with open(filepath_out, 'w') as outfile:
        for filepath in filepaths:
            with open(filepath, 'r') as infile:
                outfile.write(infile.read() + sep_line)
