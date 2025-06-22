import subprocess
import sys
from pathlib import Path

TEST_DATA = Path(__file__).parent / "data"


def test_valid_config_file():
    python = sys.executable
    result = subprocess.run(
        [python, "-m", "src.main", "-f", str(TEST_DATA / "valid.yaml")],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Successfully parsed config" in result.stdout


def test_sample_runbook_config_file():
    """Test the sample runbook configuration file is valid."""
    python = sys.executable
    config_path = TEST_DATA / "sample-runbook.yaml"
    result = subprocess.run(
        [python, "-m", "src.main", "-f", str(config_path)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert result.returncode == 0
    assert "Successfully parsed config" in result.stdout


def test_missing_config_file():
    python = sys.executable
    result = subprocess.run(
        [python, "-m", "src.main", "-f", "missing.yaml"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0
