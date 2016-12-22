import numpy as np

def get_surrounding_merra2_nodes(long, lat):
    """Returns the four surrounding MERRA2 nodes for the given coordinate"""

    # MERRA2 specs
    deltaLong = 0.625
    deltaLat = 0.5

    # Closest points
    leftLong = int(long/deltaLong)
    rightLong = leftLong + 1
    bottonLat = int(lat/deltaLat)
    topLat = bottonLat + 1

    x, y = np.meshgrid([leftLong, rightLong], [bottonLat, topLat])