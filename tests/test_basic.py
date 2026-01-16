from pathlib import Path


def test_pytest_setup():
    """Test that pytest is working correctly."""
    assert True


def test_temp_dir_fixture(temp_dir: Path):
    """Test that the temp_dir fixture works."""
    assert temp_dir.exists()
    assert temp_dir.is_dir()


def test_sample_data_dir_fixture(sample_data_dir: Path):
    """Test that the sample_data_dir fixture works."""
    assert sample_data_dir.exists()
    assert sample_data_dir.is_dir()
