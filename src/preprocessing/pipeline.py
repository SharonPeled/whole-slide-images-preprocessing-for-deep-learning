from sklearn.pipeline import Pipeline
from src.components.datasets.SlideDataset import SlideDataset
from src.components.objects.LoggingFunctionTransformer import LoggingFunctionTransformer
from src.preprocessing.function_transformers import *
from src.configs import Configs
from src.components.objects.ParallelProcessingManager import ParallelProcessingManager


def execute_preprocessing_pipeline(with_tiling, num_processes, slide_uuids):
    Logger.log('Starting preprocessing ..', log_importance=1)

    process_manager = ParallelProcessingManager(num_processes=num_processes,
                                                verbose=Configs.get('VERBOSE'),
                                                log_importance=Configs.get('LOG_IMPORTANCE'),
                                                log_format=Configs.get('LOG_FORMAT'),
                                                random_seed=Configs.get('RANDOM_SEED'),
                                                tile_progress_log_freq=Configs.get('TILE_PROGRESS_LOG_FREQ'))

    slide_dataset = SlideDataset(Configs.get('SLIDES_DIR'), load_metadata=Configs.get('LOAD_METADATA'),
                                 device=Configs.get('PREPROCESSING_DEVICE'),
                                 slide_log_file_args=Configs.get('PROGRAM_LOG_FILE_ARGS'),
                                 sample=Configs.get('SAMPLE_PROCESSED_TILES'),
                                 slide_uuids=slide_uuids)

    pipeline_list = [
        ('slide', Pipeline([
            ('load_slide', LoggingFunctionTransformer(load_slide)),
            ('scale_mpp', LoggingFunctionTransformer(resize, kw_args={'target_mag_power': Configs.get('TARGET_MAG_POWER'),
                                                                      'mag_attr': Configs.get('MAG_ATTR')})),
            ('load_reduced_image_to_memory', LoggingFunctionTransformer(load_reduced_image_to_memory,
                                                                        kw_args={'load_level': Configs.get('REDUCED_LEVEL_TO_MEMORY'),
                                                                                 'tile_size': Configs.get('TILE_SIZE')})),
            ('center_crop_reduced_image', LoggingFunctionTransformer(center_crop_reduced_image,
                                                                     kw_args={'tile_size': Configs.get('TILE_SIZE'),
                                                                              'tissue_attr': Configs.get('TISSUE_ATTR')})),
            ('filter_non_tissue_tiles',
             LoggingFunctionTransformer(filter_non_tissue_tiles,
                                        kw_args={'non_tissue_threshold': Configs.get('TILE_NON_TISSUE_THRESHOLD'),
                                                 'otsu_filter': Configs.get('OTSU_FILTER'),
                                                 'black_filter': Configs.get('BLACK_FILTER'),
                                                 'pen_filter': Configs.get('PEN_FILTER')})),
            ('generate_slide_color_grid', LoggingFunctionTransformer(generate_slide_color_grid,
                                                                     kw_args={'attrs_to_colors_map': Configs.get('ATTRS_TO_COLOR_MAP'),
                                                                              'thumbnail_filename': Configs.get('THUMBNAIL_FILENAME')})),
            ('unload_reduced_image', LoggingFunctionTransformer(unload_reduced_image)),
            ('center_crop', LoggingFunctionTransformer(center_crop))
        ]))]

    if with_tiling:
        transforms = []
        transforms.append(('save_processed_tile', LoggingFunctionTransformer(save_processed_tile,
                                                                             kw_args={'processed_tiles_dir': Configs.get('PROCESSED_TILES_DIR')})))
        pipeline_list.append(('tile', Pipeline(transforms)))
    slide_dataset.apply_pipeline(pipeline_list, process_manager, Configs.get('METADATA_JSON_FILENAME'), Configs.get('SUMMARY_DF_FILENAME'))
