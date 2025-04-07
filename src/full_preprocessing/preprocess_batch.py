import subprocess
import os
from src.utils import get_time
import shutil
from src.configs import Configs
from src.components.objects.Logger import Logger
import json


def download_slides_camelyon(slides_dir, slides_str, full_batch_ind, camelyon_vesrion):
    Logger.log('Start Downloading Camelyon..', log_importance=1)

    aws_camelyon_download_cmd = f"""{Configs.get('aws_path')} s3 cp s3://camelyon-dataset/CAMELYON{camelyon_vesrion}/images/{{slide_filename}} {{slide_dir_path}}/{{slide_filename}} --no-sign-request >> {full_batch_ind}_download_log_{{slide_id}}_{get_time()}.txt 2>&1"""
    slide_ids = slides_str.split(' ')
    for slide_id in slide_ids:
        try:
            slide_dir_path = os.path.join(slides_dir, slide_id)
            os.makedirs(slide_dir_path, exist_ok=True)

            download_slide_bash_str = aws_camelyon_download_cmd.format(slide_filename=slide_id+'.tif', slide_dir_path=slide_dir_path, slide_id=slide_id)
            proc = subprocess.Popen([download_slide_bash_str], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    shell=True)
            Logger.log(download_slide_bash_str, log_importance=1)

        except Exception as e:
            Logger.log(f"Main program received {e}", log_importance=2)
            Logger.log(f"Download failed with slide: {slide_id}", log_importance=2)
            Logger.log('Stopping subprocesses...', log_importance=2)
            proc.terminate()
            proc.wait()
            Logger.log("Subprocesses terminated.", log_importance=2)
        proc.wait()
        Logger.log(f"Finished Download {len(slides_str.split(' '))} slides.", log_importance=1)


def download_slides(slides_dir, slides_str, full_batch_ind):
    if Configs.get('Camelyon'):
        return download_slides_camelyon(slides_dir, slides_str, full_batch_ind, Configs.get('Camelyon'))
    try:
        Logger.log('Start Downloading ..', log_importance=1)
        os.makedirs(slides_dir, exist_ok=True)
        bash_str = f""" 
        cd {slides_dir}
        conda run -n gdc gdc-client download {slides_str} >> {full_batch_ind}_download_log_{get_time()}.txt 2>&1
        """
        proc = subprocess.Popen([bash_str], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                shell=True)
        Logger.log(bash_str, log_importance=1)
        proc.wait()
        Logger.log(f"Finished Download {len(slides_str.split(' '))} slides.", log_importance=1)
    except Exception as e:
        Logger.log(f"Main program received {e}", log_importance=2)
        Logger.log('Stopping subprocesses...', log_importance=2)
        proc.terminate()
        proc.wait()
        Logger.log("Subprocesses terminated.", log_importance=2)


def delete_slides(slide_ids, slides_dir):
    print('Start Delete ..')
    for slide_id in slide_ids:
        dir_path = os.path.join(slides_dir, slide_id)
        if os.path.exists(dir_path):
            for file_name in os.listdir(dir_path):
                if file_name.endswith(('.svs', '.tif')):
                    file_path = os.path.join(dir_path, file_name)
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
    print(f"Finished Delete {len(slide_ids)} slides.")


def get_bash_str_preprocess(slide_ids, num_subprocesses, full_batch_ind, config_filepath):
    slides_str = ' '.join(slide_ids)
    bash_str = f"""
    conda run -n WSI_pp python -u main.py --preprocess --Camelyon {Configs.get('Camelyon')} --aws_path {Configs.get('aws_path')} --num-tiling-subprocesses {num_subprocesses} --config_filepath {config_filepath} --slide_uuids {slides_str} >> batch_{full_batch_ind}_preprocess_{get_time()}.txt 2>&1
    """
    return bash_str


def get_already_processed_slides(slide_ids, slides_dir, metadata_filename):
    processed_slides = []
    for slide_id in slide_ids:
        metadata_path = os.path.join(slides_dir, slide_id, metadata_filename)
        if not os.path.exists(metadata_path):
            continue
        with open(metadata_path, 'r') as file:
            loaded_metadata = json.load(file)
            if loaded_metadata.get('Done preprocessing'):
                processed_slides.append(slide_id)
    return processed_slides


def full_batch_preprocess(slide_ids, num_subprocesses, full_batch_ind, config_filepath, delete_slides_after_tiling,
                          metadata_filename):
    slide_ids = [slide_id.strip("'") for slide_id in slide_ids]
    Logger.log(f'Starting processing slides: {slide_ids}', log_importance=1)
    processed_slides = get_already_processed_slides(slide_ids, Configs.get('SLIDES_DIR'), metadata_filename)
    not_processed_slides = [slide_id for slide_id in slide_ids if slide_id not in processed_slides]
    Logger.log(f'Slides: {processed_slides}, already processed.', log_importance=1)
    Logger.log(f'Continuing processing {not_processed_slides} slides.', log_importance=1)
    if len(not_processed_slides) == 0:
        Logger.log(f'All slides are already processed!', log_importance=1)
        Logger.log(f'Finished batch {full_batch_ind} tiling process.', log_importance=1)
        return
    try:
        download_slides(slides_dir=Configs.get('SLIDES_DIR'), slides_str=' '.join(not_processed_slides),
                        full_batch_ind=full_batch_ind)

        bash_str = get_bash_str_preprocess(not_processed_slides, num_subprocesses, full_batch_ind, config_filepath)
        proc1 = subprocess.Popen([bash_str, ], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True, shell=True)
        Logger.log(bash_str, log_importance=1)
        proc1.wait()

        # print(proc1.stderr.readlines())
        Logger.log(f'Finished batch {full_batch_ind} tiling process.', log_importance=1)
        if delete_slides_after_tiling:
            delete_slides(not_processed_slides, Configs.get('SLIDES_DIR'))
    except Exception as e:
        Logger.log(f"Main program received {e}", log_importance=2)
        Logger.log('Stopping subprocesses...', log_importance=2)
        proc1.terminate()
        proc1.wait()
        Logger.log("Subprocesses terminated.", log_importance=2)

