"""
Test cases for math_utils.py
"""

import math

import pytest

from src.utils.math_utils import (
    average,
    clamp,
    degrees_to_radians,
    lerp,
    normalize_angle,
    radians_to_degrees,
)


class TestMathUtils:
    """Test cases for math utilities."""

    def test_clamp_basic(self):
        """Test basic clamping functionality."""
        assert clamp(5, 0, 10) == 5
        assert clamp(-5, 0, 10) == 0
        assert clamp(15, 0, 10) == 10

    def test_clamp_edge_cases(self):
        """Test clamping edge cases."""
        # Equal to bounds
        assert clamp(0, 0, 10) == 0
        assert clamp(10, 0, 10) == 10

        # Negative ranges
        assert clamp(-5, -10, 0) == -5
        assert clamp(-15, -10, 0) == -10
        assert clamp(5, -10, 0) == 0

    def test_clamp_float(self):
        """Test clamping with float values."""
        assert clamp(3.14, 0.0, 5.0) == 3.14
        assert clamp(-1.5, 0.0, 5.0) == 0.0
        assert clamp(6.28, 0.0, 5.0) == 5.0

    def test_normalize_angle(self):
        """Test angle normalization."""
        # Test within range
        assert normalize_angle(math.pi) == math.pi
        assert normalize_angle(0) == 0

        # Test above 2π
        assert abs(normalize_angle(3 * math.pi) - math.pi) < 1e-10
        assert abs(normalize_angle(4 * math.pi) - 0) < 1e-10

        # Test negative
        assert abs(normalize_angle(-math.pi / 2) - (3 * math.pi / 2)) < 1e-10
        assert abs(normalize_angle(-2 * math.pi) - 0) < 1e-10

    def test_radians_to_degrees(self):
        """Test radians to degrees conversion."""
        assert radians_to_degrees(0) == 0
        assert abs(radians_to_degrees(math.pi) - 180.0) < 1e-10
        assert abs(radians_to_degrees(math.pi / 2) - 90.0) < 1e-10
        assert abs(radians_to_degrees(math.pi / 4) - 45.0) < 1e-10

    def test_degrees_to_radians(self):
        """Test degrees to radians conversion."""
        assert degrees_to_radians(0) == 0
        assert abs(degrees_to_radians(180.0) - math.pi) < 1e-10
        assert abs(degrees_to_radians(90.0) - math.pi / 2) < 1e-10
        assert abs(degrees_to_radians(45.0) - math.pi / 4) < 1e-10

    def test_conversion_round_trip(self):
        """Test that conversions are inverses."""
        test_angles = [0, 30, 45, 90, 180, 270, 360]

        for deg in test_angles:
            rad = degrees_to_radians(deg)
            deg2 = radians_to_degrees(rad)
            assert abs(deg2 - deg) < 1e-10

    def test_average_basic(self):
        """Test basic average calculation."""
        assert average([1, 2, 3, 4, 5]) == 3
        assert average([10]) == 10
        assert average([-1, 0, 1]) == 0

    def test_average_empty_list(self):
        """Test average with empty list raises error."""
        with pytest.raises(ValueError, match="Cannot calculate average of empty list"):
            average([])

    def test_average_float(self):
        """Test average with float values."""
        assert average([1.5, 2.5, 3.5]) == 2.5
        assert abs(average([0.1, 0.2, 0.3]) - 0.2) < 1e-10

    def test_lerp_basic(self):
        """Test basic linear interpolation."""
        assert lerp(0, 10, 0) == 0
        assert lerp(0, 10, 0.5) == 5
        assert lerp(0, 10, 1) == 10
        assert lerp(10, 20, 0.5) == 15

    def test_lerp_clamped(self):
        """Test lerp with out-of-bounds t values."""
        # t < 0
        assert lerp(0, 10, -0.5) == 0
        # t > 1
        assert lerp(0, 10, 1.5) == 10

    def test_lerp_negative(self):
        """Test lerp with negative values."""
        assert lerp(-10, 10, 0.5) == 0
        assert lerp(10, -10, 0.5) == 0

    def test_lerp_float(self):
        """Test lerp with float values."""
        assert abs(lerp(0.0, 1.0, 0.3) - 0.3) < 1e-10
        assert abs(lerp(1.0, 0.0, 0.7) - 0.3) < 1e-10
