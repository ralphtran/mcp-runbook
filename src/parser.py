from pathlib import Path
import yaml
from src.models import ConfigFile


class Parser:
    @staticmethod
    def parse_config(file_path: Path) -> ConfigFile:
        # Read file and parse with Pydantic validation
        with open(file_path, "r") as f:
            config_data = yaml.safe_load(f)
        return ConfigFile(**config_data)
