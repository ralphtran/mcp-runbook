import pytest
from pathlib import Path
from src.parser import Parser
from src.models import ConfigFile


TEST_DATA = Path(__file__).parent / "data"


def test_valid_config():
    config = Parser.parse_config(TEST_DATA / "valid.yaml")
    assert isinstance(config, ConfigFile)
    assert config.version == "1.0"
    assert len(config.runbooks) == 1


def test_invalid_config():
    with pytest.raises(Exception):
        Parser.parse_config(TEST_DATA / "invalid.yaml")
