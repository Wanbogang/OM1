"""
Unit tests for angle utility functions.
"""

from utils.angle_utils import calculate_angle_gap


class TestCalculateAngleGap:
    """Test cases for calculate_angle_gap function."""

    def test_basic_positive_gap(self):
        """Test basic case with positive angle gap."""
        assert calculate_angle_gap(10.0, 5.0) == 5.0

    def test_basic_negative_gap(self):
        """Test basic case with negative angle gap."""
        assert calculate_angle_gap(5.0, 10.0) == -5.0

    def test_wraparound_positive(self):
        """Test wraparound from small to large angle."""
        assert calculate_angle_gap(10.0, 350.0) == 20.0

    def test_wraparound_negative(self):
        """Test wraparound from large to small angle."""
        assert calculate_angle_gap(350.0, 10.0) == -20.0

    def test_180_degree_gap(self):
        """Test exactly 180 degree gap."""
        assert calculate_angle_gap(180.0, 0.0) == 180.0
        assert calculate_angle_gap(0.0, 180.0) == -180.0

    def test_zero_gap(self):
        """Test when current and target are the same."""
        assert calculate_angle_gap(45.0, 45.0) == 0.0

    def test_full_rotation(self):
        """Test angles that differ by full rotation."""
        assert calculate_angle_gap(370.0, 10.0) == 0.0

    def test_negative_angles(self):
        """Test with negative angle values."""
        assert calculate_angle_gap(-10.0, -20.0) == 10.0
        assert calculate_angle_gap(-350.0, 10.0) == 0.0

    def test_large_angles(self):
        """Test with angles larger than 360."""
        assert calculate_angle_gap(400.0, 50.0) == -10.0

    def test_rounding(self):
        """Test that result is rounded to 2 decimal places."""
        result = calculate_angle_gap(10.12345, 5.67890)
        assert result == 4.44
        assert isinstance(result, float)
