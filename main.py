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
    parser.add_argument('--full-preprocess', action='store_true')
    parser.add_argument('--delete-after-tiling', action='store_true')
    parser.add_argument("--slide_uuids", nargs="+", type=str)
    parser.add_argument('--thumbnails-only', action='store_true')
    parser.add_argument('--bring-thumbnails', type=str)
    parser.add_argument('--bring-slide-logs', type=str)
    parser.add_argument('--num-tiling-subprocesses', type=int)
    parser.add_argument('--num-full-processes', type=int)
    # requires AWS camelyon toolkit
    parser.add_argument('--manifest_path', type=str, default='Camelyon16_manifest_updated.csv')  # for camelyon, simply put the slide ids in a csv
    parser.add_argument('--num-slides-per-full-process', type=int)
    parser.add_argument('--Camelyon', default=True)
    parser.add_argument('--aws_path', type=str, default='aws')  # for camelyon, simply put the slide ids in a csv
    # for internal use only!
    parser.add_argument('--full-preprocess-batch', action='store_true')
    parser.add_argument('--full_batch_ind', type=int)

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
        execute_preprocessing_pipeline(with_tiling=True, num_processes=args.num_tiling_subprocesses,
                                       slide_uuids=args.slide_uuids)
    if args.full_preprocess:
        if not args.manifest_path:
            parser.error(f"--full-preprocess requires --manifest-path in order to download the slides.")
        from src.full_preprocessing.preprocess_parallel_batches import full_preprocess
        full_preprocess(args.config_filepath,
                        args.num_full_processes if args.num_full_processes else 1,
                        args.num_slides_per_full_process if args.num_slides_per_full_process else -1,
                        args.num_tiling_subprocesses if args.num_tiling_subprocesses else 1,
                        args.manifest_path,
                        args.delete_after_tiling)
    if args.full_preprocess_batch:
        from src.full_preprocessing.preprocess_batch import full_batch_preprocess
        full_batch_preprocess(args.slide_uuids, args.num_tiling_subprocesses, args.full_batch_ind,
                              args.config_filepath, args.delete_after_tiling)
    if args.thumbnails_only:
        from src.preprocessing.pipeline import execute_preprocessing_pipeline
        execute_preprocessing_pipeline(with_tiling=False, num_processes=args.num_tiling_subprocesses,
                                       slide_uuids=args.slide_uuids)
    if args.bring_slide_logs:
        bring_joined_log_file(Configs.get('SLIDES_DIR'), Configs.get('PROGRAM_LOG_FILE_ARGS')[0], args.bring_slide_logs)
    if args.bring_thumbnails:
        bring_files(Configs.get('SLIDES_DIR'), Configs.get('THUMBNAIL_FILENAME'), args.bring_thumbnails)


if __name__ == "__main__":
    main()


