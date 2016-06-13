import numpy

__author__ = 'dvorak'

import netCDF4

def write_test_wrf_file():
    """Writes out an idealized atmosphere for testing the interpolation.
    """

    # File to write out
    rootgrp = netCDF4.Dataset('wrfout_test_file', 'w')

    # Required dimensions
    dim_time = rootgrp.createDimension('Time', 0) # Unlimited
    dim_datestrlen = rootgrp.createDimension('DateStrLen', 19)
    dim_bottom_top = rootgrp.createDimension('bottom_top', 2)
    dim_bottom_top_stag = rootgrp.createDimension('bottom_top_stag', 3)
    dim_south_north = rootgrp.createDimension('south_north', 2)
    dim_south_north_stag = rootgrp.createDimension('south_north_stag', 3)
    dim_west_east = rootgrp.createDimension('west_east', 2)
    dim_west_east_stag = rootgrp.createDimension('west_east_stag', 3)

    # Times variable
    var_times = rootgrp.createVariable('Times', 'S1', ('Time', 'DateStrLen'))
    var_times = netCDF4.stringtoarr('2014-01-01_01:00:00', 19)

    # Requried 4D variables
    var_znu = rootgrp.createVariable('ZNU', 'f4', ('Time', 'bottom_top'))
    var_znu[0] = [0.99715, 0.99010] # 23 and 80 m AGL from calculate-eta-height.py
    var_znw = rootgrp.createVariable('ZNW', 'f4', ('Time', 'bottom_top_stag'))
    var_znw[0] = [1.0000, 0.99443, 0.98577]
    var_p = rootgrp.createVariable('P', 'f4', ('Time', 'bottom_top', 'south_north', 'west_east'))
    var_p[0] = [[101049, 101049], [101049, 101049],
                [100368, 100368], [100368, 100368]]
    var_pb = rootgrp.createVariable('PB', 'f4', ('Time', 'bottom_top', 'south_north', 'west_east'))
    var_pb[0] = [[0, 0], [0, 0],
                 [0, 0], [0, 0]]
    var_psfc = rootgrp.createVariable('PSFC', 'f4', ('Time', 'south_north', 'west_east'))
    var_psfc[0] = [[101325, 101325],
                   [101325, 101325]]
    var_t = rootgrp.createVariable('T', 'f4', ('Time', 'bottom_top', 'south_north', 'west_east'))
    var_t[0] = numpy.array([[[288.000, 288.000], [288.000, 288.000]],
                            [[287.630, 287.630], [287.630, 287.630]]]) - 300
    var_t2 = rootgrp.createVariable('T2', 'f4', ('Time', 'south_north', 'west_east'))
    var_t2[0] = [[288.000, 288.000], [288.000, 288.000]]
    var_th2 = rootgrp.createVariable('TH2', 'f4', ('Time', 'south_north', 'west_east'))
    var_th2[0] = [[288.000, 288.000], [288.000, 288.000]]
    var_u = rootgrp.createVariable('U', 'f4', ('Time', 'bottom_top', 'south_north','west_east_stag'))
    var_u[0] = [[[5, 5, 5], [5, 5, 5]],
                [[5.535, 5.535, 5.535], [5.535, 5.535, 5.535]]] # Log-law profile for 23 and 80 m (wind speed of u and v)
    var_v = rootgrp.createVariable('V', 'f4', ('Time', 'bottom_top', 'south_north_stag', 'west_east'))
    var_v[0] = [[[0, 0], [0, 0], [0, 0]],
                [[0, 0], [0, 0], [0, 0]]]
    var_p_top = rootgrp.createVariable('P_TOP', 'f4', ('Time', ))
    var_p_top[0] = 0

    # Map projection variables
    var_cosalpha = rootgrp.createVariable('COSALPHA', 'f4', ('Time', 'south_north', 'west_east'))
    var_cosalpha[0] = [[0.99, 0.99], [0.99, 0.99]]
    var_sinalpha = rootgrp.createVariable('SINALPHA', 'f4', ('Time', 'south_north', 'west_east'))
    var_sinalpha[0] = [[0.99, 0.99], [0.99, 0.99]]

    # Map coordinates
    var_xlong = rootgrp.createVariable('XLONG', 'f4', ('Time', 'south_north', 'west_east'))
    var_xlong[0] = [[0, 5000], [0, 5000]]
    var_xlat = rootgrp.createVariable('XLAT', 'f4', ('Time', 'south_north', 'west_east'))
    var_xlat[0] = [[0, 5000], [0, 5000]]

    # Close the file
    rootgrp.close()

if __name__ == '__main__':
    write_test_wrf_file()
