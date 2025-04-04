import subprocess
import os
from src.utils import get_time
import shutil
from src.configs import Configs
from src.components.objects.Logger import Logger


def download_slides_camelyon(slides_dir, slides_str, full_batch_ind):
    Logger.log('Start Downloading Camelyon..', log_importance=1)

    aws_camelyon_download_cmd = f"""{Configs.get('aws_path')} s3 cp s3://camelyon-dataset/CAMELYON16/background_tissue/{{slide_filename}} {{slide_dir_path}}/{{slide_filename}} --no-sign-request >> {full_batch_ind}_download_log_{{slide_id}}_{get_time()}.txt 2>&1"""
    slide_ids = slides_str.split(' ')
    for slide_id in slide_ids:
        try:
            slide_dir_path = os.path.join(slides_dir, slide_id)
            os.mkdir(slide_dir_path)

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
        return download_slides_camelyon(slides_dir, slides_str, full_batch_ind)
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
        shutil.rmtree(dir_path)
    print(f"Finished Delete {len(slide_ids)} slides.")


def get_bash_str_preprocess(slide_ids, num_subprocesses, full_batch_ind, config_filepath):
    slides_str = ' '.join(slide_ids)
    bash_str = f"""
    conda run -n WSI_pp python -u main.py --preprocess --Camelyon {Configs.get('Camelyon')} --aws_path {Configs.get('aws_path')} --num-tiling-subprocesses {num_subprocesses} --config_filepath {config_filepath} --slide_uuids {slides_str} >> batch_{full_batch_ind}_preprocess_{get_time()}.txt 2>&1
    """
    return bash_str


def full_batch_preprocess(slide_ids, num_subprocesses, full_batch_ind, config_filepath, delete_after_tiling):
    slide_ids = [slide_id.strip("'") for slide_id in slide_ids]
    Logger.log(f'Starting processing slides: {slide_ids}', log_importance=1)
    try:
        download_slides(slides_dir=Configs.get('SLIDES_DIR'), slides_str=' '.join(slide_ids),
                        full_batch_ind=full_batch_ind)

        bash_str = get_bash_str_preprocess(slide_ids, num_subprocesses, full_batch_ind, config_filepath)
        proc1 = subprocess.Popen([bash_str, ], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True, shell=True)
        Logger.log(bash_str, log_importance=1)
        proc1.wait()

        # print(proc1.stderr.readlines())
        Logger.log(f'Finished {full_batch_ind} batch tiling process.', log_importance=1)
        if delete_after_tiling:
            delete_slides(slide_ids, Configs.get('SLIDES_DIR'))
    except Exception as e:
        Logger.log(f"Main program received {e}", log_importance=2)
        Logger.log('Stopping subprocesses...', log_importance=2)
        proc1.terminate()
        proc1.wait()
        Logger.log("Subprocesses terminated.", log_importance=2)

