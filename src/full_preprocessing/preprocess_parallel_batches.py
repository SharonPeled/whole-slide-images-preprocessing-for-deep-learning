import subprocess
import os
from src.configs import Configs
from src.utils import get_time
import pandas as pd
import numpy as np
from time import sleep
from src.components.objects.Logger import Logger


def generate_slide_paths_from_manifest(manifest_path, slides_dir):
    slide_paths = []
    df_m = pd.read_csv(manifest_path, sep='\t')
    for i, row in df_m.iterrows():
        slide_uuid = row['id']
        filename = row['filename']
        path = os.path.join(slides_dir, slide_uuid, filename)
        slide_paths.append(path)
    df_m['slide_path'] = slide_paths
    return df_m


def get_bash_str_preprocess(config_filepath, slide_ids, num_processes, full_batch_ind, delete_after_tiling):
    slides_str = ' '.join(slide_ids)
    delete_after_tiling_str = '--delete-after-tiling' if delete_after_tiling else ''
    bash_str = f"conda run -n WSI_pp python -u main.py --config_filepath {config_filepath} --full-preprocess-batch --num-tiling-subprocesses {num_processes} --slide_uuids {slides_str} --full_batch_ind {full_batch_ind} {delete_after_tiling_str} >> batch_{full_batch_ind}_full_preprocess_{get_time()}.txt 2>&1"
    return bash_str


def full_preprocess(config_filepath, num_full_processes, num_slides_per_process, num_subprocesses_per_process,
                    manifest_path, delete_after_tiling):
    df_m = generate_slide_paths_from_manifest(manifest_path=manifest_path,
                                              slides_dir=Configs.get('SLIDES_DIR'))
    Logger.log(f'Manifest length: {len(df_m)}.', log_importance=2)
    if num_slides_per_process == -1:
        manifest_fullprocess_batches = [df_m, ]
    else:
        manifest_fullprocess_batches = np.array_split(df_m, np.ceil(len(df_m) / num_slides_per_process))
    full_batch_ind = 0
    processes = []
    try:
        while True:
            num_running_full_processes = sum([proc.poll() is None for proc in processes])
            if full_batch_ind == len(manifest_fullprocess_batches) and num_running_full_processes == 0:
                # finished preprocessing everything
                break
            if num_running_full_processes < num_full_processes and \
                    full_batch_ind < len(manifest_fullprocess_batches):
                # launch new full process
                df_batch = manifest_fullprocess_batches[full_batch_ind]
                slide_ids = list(df_batch['id'])
                full_batch_ind += 1
                bash_str = get_bash_str_preprocess(config_filepath, slide_ids, num_subprocesses_per_process,
                                                   full_batch_ind, delete_after_tiling)
                proc = subprocess.Popen([bash_str,],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      text=True, shell=True)
                processes.append(proc)
                Logger.log(bash_str, log_importance=2)
                Logger.log(f'New Process created with slides: {slide_ids}', log_importance=2)
                continue
            sleep(30)
        Logger.log('Finished Preprocessing All!', log_importance=2)
    except Exception as e:
        Logger.log(f"Main program received {e}", log_importance=2)
        Logger.log('Stopping subprocesses...', log_importance=2)
        for subproc in processes:
            subproc.terminate()
            subproc.wait()
        Logger.log("Subprocesses terminated.", log_importance=2)