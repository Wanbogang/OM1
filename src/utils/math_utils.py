"""
Simple math utilities for OM1.
"""

import math
from typing import List


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max.

    Parameters
    ----------
    value : float
        The value to clamp.
    min_val : float
        Minimum allowed value.
    max_val : float
        Maximum allowed value.

    Returns
    -------
    float
        The clamped value.

    Examples
    --------
    >>> clamp(5, 0, 10)
    5
    >>> clamp(-5, 0, 10)
    0
    >>> clamp(15, 0, 10)
    10
    """
    return max(min_val, min(value, max_val))


def normalize_angle(angle: float) -> float:
    """
    Normalize angle to range [0, 2π).

    Parameters
    ----------
    angle : float
        Angle in radians.

    Returns
    -------
    float
        Angle normalized to [0, 2π).

    Examples
    --------
    >>> normalize_angle(3 * math.pi)
    3.141592653589793
    >>> normalize_angle(-math.pi / 2)
    4.71238898038469
    """
    return angle % (2 * math.pi)


def radians_to_degrees(radians: float) -> float:
    """
    Convert radians to degrees.

    Parameters
    ----------
    radians : float
        Angle in radians.

    Returns
    -------
    float
        Angle in degrees.
    """
    return radians * 180.0 / math.pi


def degrees_to_radians(degrees: float) -> float:
    """
    Convert degrees to radians.

    Parameters
    ----------
    degrees : float
        Angle in degrees.

    Returns
    -------
    float
        Angle in radians.
    """
    return degrees * math.pi / 180.0


def average(values: List[float]) -> float:
    """
    Calculate average of a list of values.

    Parameters
    ----------
    values : List[float]
        List of values.

    Returns
    -------
    float
        Average value.

    Raises
    ------
    ValueError
        If values list is empty.
    """
    if not values:
        raise ValueError("Cannot calculate average of empty list")
    return sum(values) / len(values)


def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation between a and b.

    Parameters
    ----------
    a : float
        Start value.
    b : float
        End value.
    t : float
        Interpolation factor [0, 1].

    Returns
    -------
    float
        Interpolated value.
    """
    return a + (b - a) * clamp(t, 0.0, 1.0)
