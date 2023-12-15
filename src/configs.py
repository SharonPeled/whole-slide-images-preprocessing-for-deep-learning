from dataclasses import dataclass
from src.preprocessing.pen_filter import get_pen_color_palette
from src.utils import get_time
import yaml


@dataclass
class ConfigsSingletonClass:
    def __init__(self):
        self.config_dict = {}

    def deploy_yaml_file(self, config_filepath):
        with open(config_filepath, 'r') as yaml_file:
            yaml_content = yaml.load(yaml_file, Loader=yaml.FullLoader)
        for sub_config_dict in yaml_content.values():
            self.config_dict.update(sub_config_dict)
        self.add_computed_configs()

    def add_computed_configs(self):
        PREPROCESS_RUN_NAME = self.config_dict['PREPROCESS_RUN_NAME']
        self.config_dict['METADATA_JSON_FILENAME'] = f'metadata_{PREPROCESS_RUN_NAME}.json'
        self.config_dict['SUMMARY_DF_FILENAME'] = f'summary_df_{PREPROCESS_RUN_NAME}.csv'
        self.config_dict['THUMBNAIL_FILENAME'] = f'thumbnail_{PREPROCESS_RUN_NAME}.png'
        if self.config_dict['PEN_FILTER']['color_palette'] is None:
            self.config_dict['PEN_FILTER']['color_palette'] = get_pen_color_palette()

    def paste_current_time(self):
        time_str = get_time()
        for key, val in self.config_dict.items():
            if isinstance(val, str) and '{time}' in val:
                self.config_dict[key] = val.format(time=time_str)
            elif isinstance(val, list):
                for i, sub_val in enumerate(val):
                    if isinstance(sub_val, str) and '{time}' in sub_val:
                        self.config_dict[key][i] = sub_val.format(time=time_str)

    def get(self, key, default=None):
        return self.config_dict.get(key, default)

    def set(self, key, val):
        self.config_dict[key] = val


Configs = ConfigsSingletonClass()
