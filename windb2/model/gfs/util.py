import numpy

def center_coords_on_prime_meridian(longitude):
    """Takes a numpy array of longitude from 0 to 360 degrees and makes it from -180 to 180 degrees"""
    longitude[longitude > 180] = 180 - longitude[longitude > 180]

    return longitude
