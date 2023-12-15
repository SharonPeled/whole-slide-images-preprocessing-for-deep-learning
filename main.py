import argparse
from src.utils import bring_files, bring_joined_log_file, get_time, set_global_configs
from src.configs import Configs
import matplotlib
import warnings
warnings.filterwarnings("ignore")
matplotlib.use('agg')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config_filepath', type=str, required=True)
    parser.add_argument('--preprocess', action='store_true')
    parser.add_argument("--slide_uuids", nargs="+", type=str)
    parser.add_argument('--thumbnails-only', action='store_true')
    parser.add_argument('--bring-thumbnails', type=str)
    parser.add_argument('--bring-slide-logs', type=str)
    parser.add_argument('--num-processes', type=int)
    args = parser.parse_args()

    Configs.deploy_yaml_file(args.config_filepath)

    set_global_configs(verbose=Configs.get('VERBOSE'),
                       log_file_args=Configs.get('PROGRAM_LOG_FILE_ARGS'),
                       log_importance=Configs.get('LOG_IMPORTANCE'),
                       log_format=Configs.get('LOG_FORMAT'),
                       random_seed=Configs.get('RANDOM_SEED'),
                       tile_progress_log_freq=Configs.get('TILE_PROGRESS_LOG_FREQ'))

    if args.preprocess:
        from src.preprocessing.pipeline import execute_preprocessing_pipeline
        execute_preprocessing_pipeline(with_tiling=True, num_processes=args.num_processes, slide_uuids=args.slide_uuids)
    if args.thumbnails_only:
        from src.preprocessing.pipeline import execute_preprocessing_pipeline
        execute_preprocessing_pipeline(with_tiling=False, num_processes=args.num_processes, slide_uuids=args.slide_uuids)
    if args.bring_slide_logs:
        bring_joined_log_file(Configs.get('SLIDES_DIR'), Configs.get('PROGRAM_LOG_FILE_ARGS')[0], args.bring_slide_logs)
    if args.bring_thumbnails:
        bring_files(Configs.get('SLIDES_DIR'), Configs.get('THUMBNAIL_FILENAME'), args.bring_thumbnails)
    if args.bring_tumor_thumbnails:
        bring_files(Configs.get('SLIDES_DIR'), Configs.get('TUMOR_THUMBNAIL_FILENAME'), args.bring_tumor_thumbnails)
    if args.bring_semantic_seg_thumbnails:
        bring_files(Configs.get('SLIDES_DIR'), Configs.get('SS_THUMBNAIL_FILENAME'), args.bring_semantic_seg_thumbnails)


if __name__ == "__main__":
    main()


