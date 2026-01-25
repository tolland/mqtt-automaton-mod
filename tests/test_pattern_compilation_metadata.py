import pytest
from mqttbot.config.model.pattern.pattern_config import PatternsConfig
from mqttbot.config.model.pattern.pattern import Pattern
from mqttbot.core.tasks.task_compiler import TaskCompiler
from mqttbot.core.tasks.concrete.pattern_task import PatternTask

def test_pattern_string_vs_full_compilation():
    # 1. Define a pattern with both string and full step
    config_data = {
        "patterns": [
            {
                "pattern_id": "test_pattern",
                "steps": [
                    "~10 ~ 100",  # String pattern
                    {             # Full pattern step
                        "type": "pattern",
                        "coords": {
                            "x": {"frame": "relative", "value": 10.0},
                            "y": {"frame": "relative", "value": 0.0},
                            "z": {"frame": "absolute", "value": 100.0}
                        },
                        "metadata": {}
                    }
                ]
            }
        ]
    }

    patterns_config = PatternsConfig.model_validate(config_data)
    compiler = TaskCompiler(patterns_config)

    # 2. Compile the pattern
    tasks = list(compiler.compile_pattern("test_pattern", (0, 0, 0)))

    assert len(tasks) == 2
    task1, task2 = tasks

    assert isinstance(task1, PatternTask)
    assert isinstance(task2, PatternTask)

    # 3. Verify they are equivalent
    # Coords check
    assert task1.target == (10.0, 0.0, 100.0)
    assert task2.target == (20.0, 0.0, 100.0) # Relative X was 10, so 10+10=20

    # Metadata check
    # Pydantic might return full default dict even if initialized with {}
    assert task1.metadata == {"fail_me": None, "note": None, "tags": None, "pattern": None}
    assert task2.metadata == {"fail_me": None, "note": None, "tags": None, "pattern": None}

def test_pattern_with_metadata_compilation():
    # 1. Define a pattern with metadata in full step
    config_data = {
        "patterns": [
            {
                "pattern_id": "test_metadata",
                "steps": [
                    {
                        "type": "pattern",
                        "coords": {
                            "x": {"frame": "relative", "value": 0},
                            "y": {"frame": "relative", "value": 0},
                            "z": {"frame": "relative", "value": 0}
                        },
                        "metadata": {"note": "special step", "tags": ["tag1"]}
                    }
                ]
            }
        ]
    }

    patterns_config = PatternsConfig.model_validate(config_data)
    compiler = TaskCompiler(patterns_config)

    tasks = list(compiler.compile_pattern("test_metadata", (0, 0, 0)))
    assert len(tasks) == 1
    assert tasks[0].metadata == {"note": "special step", "tags": ["tag1"], "fail_me": None, "pattern": None}
