"""Tests for PatternExpander - pattern parsing and coordinate expansion"""

import pytest

from mqttbot.core.patterns.pattern_expander import PatternExpander


class TestPatternExpanderParsing:
    """Test pattern step parsing"""

    def test_parse_relative_coords(self):
        """Test parsing relative coordinate strings"""
        step = PatternExpander.parse_pattern_step("~ ~ ~-5")
        assert step.type == "goto"
        assert step.relative_coords == (0, 0, -5)

    def test_parse_relative_coords_positive(self):
        """Test parsing positive relative coords"""
        step = PatternExpander.parse_pattern_step("~5 ~3 ~10")
        assert step.type == "goto"
        assert step.relative_coords == (5, 3, 10)

    def test_parse_relative_coords_mixed(self):
        """Test parsing mixed relative coords"""
        step = PatternExpander.parse_pattern_step("~-2 ~ ~15")
        assert step.type == "goto"
        assert step.relative_coords == (-2, 0, 15)

    def test_parse_dwell(self):
        """Test parsing dwell steps"""
        step = PatternExpander.parse_pattern_step({"type": "dwell", "period": "4s"})
        assert step.type == "dwell"
        assert step.dwell_seconds == 4.0

    def test_parse_dwell_milliseconds(self):
        """Test parsing dwell with milliseconds"""
        step = PatternExpander.parse_pattern_step({"type": "dwell", "period": "500ms"})
        assert step.type == "dwell"
        assert step.dwell_seconds == 0.5

    def test_parse_tilde_no_offset(self):
        """Test parsing ~ with no offset"""
        step = PatternExpander.parse_pattern_step("~ ~ ~")
        assert step.relative_coords == (0, 0, 0)

    def test_parse_tilde_zero(self):
        """Test parsing ~0"""
        step = PatternExpander.parse_pattern_step("~0 ~0 ~0")
        assert step.relative_coords == (0, 0, 0)

    def test_parse_invalid_format(self):
        """Test that invalid formats raise errors"""
        with pytest.raises(ValueError):
            PatternExpander.parse_pattern_step("invalid")


class TestPatternExpanderExpansion:
    """Test pattern expansion into absolute coordinates"""

    def test_expand_simple_pattern(self):
        """Test expanding a simple pattern"""
        pattern = ["~ ~ ~-5", "~ ~ ~-5"]
        result = PatternExpander.expand_pattern(pattern, (100, 64, 100))

        assert len(result) == 2
        assert result[0] == ("goto", (100, 64, 95))
        assert result[1] == ("goto", (100, 64, 90))

    def test_expand_pattern_with_dwell(self):
        """Test expanding pattern with dwell steps"""
        pattern = ["~ ~ ~-5", {"type": "dwell", "period": "2s"}, "~ ~ ~-5"]
        result = PatternExpander.expand_pattern(pattern, (100, 64, 100))

        assert len(result) == 3
        assert result[0] == ("goto", (100, 64, 95))
        assert result[1] == ("dwell", 2.0)
        assert result[2] == ("goto", (100, 64, 90))

    def test_expand_pattern_position_tracking(self):
        """Test that position is tracked correctly through pattern"""
        pattern = ["~ ~ ~-5", "~ ~ ~-10", "~ ~ ~15"]
        result = PatternExpander.expand_pattern(pattern, (100, 64, 100))

        # Position should accumulate through the pattern
        assert result[0] == ("goto", (100, 64, 95))  # -5 from base
        assert result[1] == ("goto", (100, 64, 85))  # -10 from prev
        assert result[2] == ("goto", (100, 64, 100))  # +15 back to base

    def test_expand_3d_pattern(self):
        """Test pattern expansion in 3D"""
        pattern = ["~5 ~ ~", "~ ~2 ~", "~ ~ ~-10"]
        result = PatternExpander.expand_pattern(pattern, (100, 64, 100))

        assert result[0] == ("goto", (105, 64, 100))
        assert result[1] == ("goto", (105, 66, 100))
        assert result[2] == ("goto", (105, 66, 90))

    def test_expand_empty_pattern(self):
        """Test expanding empty pattern"""
        result = PatternExpander.expand_pattern([], (100, 64, 100))
        assert result == []

    def test_expand_pattern_returns_correct_types(self):
        """Test that expansion returns correct task type tuples"""
        pattern = ["~ ~ ~5", {"type": "dwell", "period": "1s"}]
        result = PatternExpander.expand_pattern(pattern, (0, 0, 0))

        # Check tuple structure
        goto_task = result[0]
        dwell_task = result[1]

        assert isinstance(goto_task, tuple)
        assert len(goto_task) == 2
        assert goto_task[0] == "goto"
        assert isinstance(goto_task[1], tuple)
        assert len(goto_task[1]) == 3

        assert isinstance(dwell_task, tuple)
        assert len(dwell_task) == 2
        assert dwell_task[0] == "dwell"
        assert isinstance(dwell_task[1], float)

    def test_expand_complex_pattern(self):
        """Test expanding a realistic farming pattern"""
        pattern = [
            "~ ~ ~-5",
            "~ ~ ~-5",
            {"type": "dwell", "period": "3s"},
            "~ ~ ~-5",
            "~ ~ ~10",
        ]
        result = PatternExpander.expand_pattern(pattern, (50, 65, 50))

        # Verify the sequence
        assert result[0] == ("goto", (50, 65, 45))
        assert result[1] == ("goto", (50, 65, 40))
        assert result[2] == ("dwell", 3.0)
        assert result[3] == ("goto", (50, 65, 35))
        assert result[4] == ("goto", (50, 65, 45))  # Back to start


class TestPatternExpanderEdgeCases:
    """Test edge cases and error handling"""

    def test_pattern_with_large_coordinates(self):
        """Test with large coordinate values"""
        pattern = ["~1000 ~ ~"]
        result = PatternExpander.expand_pattern(pattern, (0, 0, 0))
        assert result[0] == ("goto", (1000, 0, 0))

    def test_pattern_with_negative_base(self):
        """Test with negative base coordinates"""
        pattern = ["~ ~ ~5"]
        result = PatternExpander.expand_pattern(pattern, (-100, 64, -100))
        assert result[0] == ("goto", (-100, 64, -95))

    def test_parse_axis_edge_cases(self):
        """Test axis parsing edge cases"""
        assert PatternExpander._parse_axis("~") == 0
        assert PatternExpander._parse_axis("~0") == 0
        assert PatternExpander._parse_axis("~-1") == -1
        assert PatternExpander._parse_axis("~+5") == 5  # + prefix should work
        assert PatternExpander._parse_axis("0") == 0
        assert PatternExpander._parse_axis("100") == 100
