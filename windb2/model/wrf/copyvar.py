from netCDF4 import Dataset
import logging

__author__ = 'Mike Dvorak'

logger = logging.getLogger('windb2')

def copyvar(wrf_vars, nc_infile, nc_outfile):
    """Copies 3D (2D space, 1D time) WRF variables to the WinDB2 height interpolated file and adjust DIMENSIONS to CF compliant names (not the WRF 
    variable names however).

    wrf_vars - List of WRF variable names to copy
    nc_infile - wrfout file to copy from, can be a string or a netCDF4 Dataset
    nc_infile - wrfout file to copy to, can be a string or a netCDF4 Dataset
    """

    # Open the input and output netCDF file if necessary
    close_nc_infile = False
    if type(nc_infile) != Dataset:
        close_nc_infile = True
        nc_infile = Dataset(nc_infile, 'r')
    close_nc_outfile = False
    if type(nc_outfile) != Dataset:
        close_nc_outfile = True
        nc_outfile = Dataset(nc_outfile, 'a')

    # Copy the WRF vars
    for wrf_var in wrf_vars:
        print('Copying WRF variable {}'.format(wrf_var))

        # Get the variable to copy
        in_var = nc_infile[wrf_var]
        out_var = nc_outfile.createVariable(wrf_var.lower(), in_var.datatype,
                                            ('Time', 'y', 'x'))

        # Add in all of the attributes
        for a in nc_infile[wrf_var].ncattrs():
            if a == 'description' or a == 'units':
                out_var.setncattr(a, getattr(nc_infile[wrf_var], a))

        # Copy the array
        out_var[:] = in_var[:]

    # Close the netCDF files if necessary
    if close_nc_infile:
        nc_infile.close()
    if close_nc_outfile:
        nc_outfile.close()
