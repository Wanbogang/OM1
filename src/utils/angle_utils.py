"""
Utility functions for angle calculations.
"""


def calculate_angle_gap(current: float, target: float) -> float:
    """
    Calculate shortest angular distance between two angles.

    Parameters:
    -----------
    current : float
        Current angle in degrees.
    target : float
        Target angle in degrees.

    Returns:
    --------
    float
        Shortest angular distance in degrees, rounded to 2 decimal places.
    """
    gap = current - target
    if gap > 180.0:
        gap -= 360.0
    elif gap < -180.0:
        gap += 360.0
    return round(gap, 2)
