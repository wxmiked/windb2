from windb2.model.wrf import heightinterp

__author__ = 'Mike Dvorak'

"""Vertically interpolates a WRF netCDF output file to eta-half levels."""

import numpy
from netCDF4 import Dataset
from windb2.model.wrf import config
import windb2.model.wrf.constants as constants
import logging

wrf_config = config.Windb2WrfConfigParser()
wrf_config.read('windb2-wrf.conf')

logger = logging.getLogger('windb2')

class HeightInterpFile:
    """Vertically interpolates a WRF output files.
    """

    outfile_extension = "-height-interp.nc"

    # Cloud fraction ranges in meters
    # Using mid-latitude low, medium, and high cloud heights from Galvin, An Intro. to the Met. and Climate of the Tropics, 2016: http://bit.ly/2tTPJxE
    # High: 5k-13k m, Middle: 2k-7k m, Low: 0-2k m
    # We are arbitrarily defining Fog as 0-30 m
    CLOUD_HEIGHTS = {}
    CLOUD_HEIGHTS['high'] = {'top': 13000, 'bottom': 5000}
    CLOUD_HEIGHTS['mid'] = {'top': 7000, 'bottom': 2000}
    CLOUD_HEIGHTS['low'] = {'top': 2000, 'bottom': 0}
    CLOUD_HEIGHTS['fog'] = {'top': 30, 'bottom': 0}

    eta_height_w = None
    eta_height_mass = None
    heights_to_interp = None
    vars_to_interp = None

    def __init__(self, windb2_config):
        self.windb2_config = windb2_config
        self.heights_to_interp = self.windb2_config.get_float_list('INTERP', 'heights')
        self.vars_to_interp = self.windb2_config.get_str_list('INTERP', 'vars')

    @staticmethod
    def copy_empty_var(varname, nc_infile, nc_outfile):
        # Get the old variable details
        var_type = nc_infile.variables[varname].datatype
        nc_var = nc_infile.variables[varname]
        nc_dims = nc_infile.dimensions

        # Create the new dimensions that are the exact same as the input
        for dim in nc_dims:
            nc_outfile.createDimension(dim, size=len(nc_dims[dim]))

        # Create the new variable and copy
        nc_outfile.createVariable(varname, var_type, nc_var.dimensions)

    @staticmethod
    def copy_netcdf_var(varname, nc_infile, nc_outfile, new_varname=None):
        # Copy the dimensions
        for dimname in nc_infile.variables[varname].dimensions:
            dim = nc_infile.dimensions[dimname]

            # It's possible that these dimensions have already been added, so just move on if that's the case
            try:
                nc_outfile.createDimension(dimname, len(dim) if not dim.isunlimited() else None)
            except RuntimeError as e:
                if r'NetCDF: String match to name in use' in str(e):
                    logger.debug('Dimension was already in new netCDF file:' + dimname)
                else:
                    raise e

        # Copy the variable
        old_var = nc_infile.variables[varname]
        new_var = nc_outfile.createVariable(varname if new_varname is None else new_varname,
                                            old_var.datatype, old_var.dimensions)
        new_var.setncatts({i: old_var.getncattr(i) for i in old_var.ncattrs()})
        new_var[:] = old_var[:]

        return new_var

    """Calculates the mean temperature between two layers from potential temperature (theta in units of K) and pressure
    (in units of Pa)>"""

    @staticmethod
    def calc_mean_temperature_across_layer(theta_lower, pressure_lower, theta_upper, pressure_upper):
        # Convert potential temperature to temperature
        t1 = theta_lower / numpy.power(constants.REF_PRES / pressure_lower, constants.KAPPA)
        t2 = theta_upper / numpy.power(constants.REF_PRES / pressure_upper, constants.KAPPA)

        # Return the average
        return (t1 + t2) / 2.

    def calc_eta_heights(self, nc_infile):
        """Calculates the eta heights inclusive of the highest desired vertical interpolation height.

        Returns:
            scipy.io.netcdf.variable with the interpolated heights of the dimensions Time, south_north,
            x"""

        # Pressure at mass point
        pressure = nc_infile.variables['P'][:] + nc_infile.variables['PB'][:]

        # Calculate height of the first eta half level, nearest the surface
        # WRF potential temperature is shifted by 300 K: http://www2.mmm.ucar.edu/wrf/users/docs/user_guide_V3/users_guide_chap5.htm#special_fields
        pressure_surface = nc_infile.variables['PSFC'][:]
        temperature_bottom_layer = self.calc_mean_temperature_across_layer(nc_infile.variables['T2'][:],
                                                                           pressure_surface,
                                                                           nc_infile.variables['T'][:, 0, :, :] + 300.,
                                                                           pressure[:, 0, :, :])
        height_first_eta_half = constants.R_CONST / constants.G_CONST * temperature_bottom_layer * \
                                numpy.log(pressure_surface / pressure[:, 0, :, :])

        # Calculate regular temperature at the mass point by averaging temperature above and below w point
        pressure_below = pressure[:, :-1, :, :]
        pressure_above = pressure[:, 1:, :, :]
        temperature_at_mass = self.calc_mean_temperature_across_layer(nc_infile.variables['T'][:, :-1, :, :] + 300.,
                                                                      pressure_below,
                                                                      nc_infile.variables['T'][:, 1:, :, :] + 300.,
                                                                      pressure_above)

        # Hypsometric equation
        heightDiffs = constants.R_CONST / constants.G_CONST * temperature_at_mass * \
                      numpy.log(pressure_below / pressure_above)

        # Add in the first level half eta layer height
        height_at_eta_half_level = numpy.insert(heightDiffs, 0, height_first_eta_half[:, numpy.newaxis, :, :], axis=1)

        # Sum up all of the heights from the ground up to get the height above ground level
        height_eta_half_above_ground = numpy.cumsum(height_at_eta_half_level, axis=1)

        return height_eta_half_above_ground

    @staticmethod
    def _set_metadata_uv(ncvar_u, ncvar_v):
        ncvar_u.description = 'eastward wind'
        ncvar_u.longdesc = '"Eastward" indicates a vector component which is positive when directed eastward (negative westward). Wind is defined as a two-dimensional (horizontal) air velocity vector, with no vertical component. (Vertical motion in the atmosphere has the standard name upward_air_velocity.)'
        ncvar_v.description = 'northward wind'
        ncvar_v.longdesc = '"Northward" indicates a vector component which is positive when directed northward (negative southward). Wind is defined as a two-dimensional (horizontal) air velocity vector, with no vertical component. (Vertical motion in the atmosphere has the standard name upward_air_velocity.)'
        ncvar_u.units = 'm s-1'
        ncvar_v.units = 'm s-1'

    @staticmethod
    def _set_metadata_theta(ncvar_theta):
        ncvar_theta.description = 'potential temperature'
        ncvar_theta.longdescription = 'Potential temperature is the temperature a parcel of air or sea water would have if moved adiabatically to sea level pressure.'
        ncvar_theta.units = 'K'

    @staticmethod
    def _set_metadata_pres(ncvar_pres):
        ncvar_pres.description = 'air pressure'
        ncvar_pres.longdescription = 'No help available.'
        ncvar_pres.units = 'Pa'

    @staticmethod
    def _set_metadata_rho(ncvar_theta):
        ncvar_theta.description = 'air density'
        ncvar_theta.longdescription = 'No help available.'
        ncvar_theta.units = 'kg m-3'

    @staticmethod
    def _set_metadata_dpt(ncvar_dpt):
        ncvar_dpt.description = 'Dew point temperature',
        ncvar_dpt.longdescription = 'Dew point temperature is the temperature at which a parcel of air reaches saturation upon being cooled at constant pressure and specific humidity.'
        ncvar_dpt.units = 'K'

    @staticmethod
    def _set_metadata_cld(ncvar_cld_dict, cloud_heights):
        for height in cloud_heights.keys():
            ncvar_cld_dict[height].description = 'Cloud fraction {}'.format(height),
            ncvar_cld_dict[height].longdescription = 'Cloud fraction is the fraction of the layer that is covered in clouds from {} to {} m.'\
                .format(cloud_heights[height]['bottom'], cloud_heights[height]['top'])
            ncvar_cld_dict[height].units = '1'
            ncvar_cld_dict[height].cloud_fraction_bottom_m = cloud_heights[height]['bottom']
            ncvar_cld_dict[height].cloud_fraction_top_m = cloud_heights[height]['top']

    # @profile
    def interp_file(self, wrf_filename):
        # Open the netCDF file
        nc_infile = Dataset(wrf_filename, mode='r')
        nc_outfile = Dataset(wrf_filename + self.outfile_extension, mode='w', format='NETCDF4')

        # Copy the WRF attributes to a subgroup
        wrfgroup = nc_outfile.createGroup('WRF')
        for attr in nc_infile.ncattrs():
            wrfgroup.setncattr(attr, getattr(nc_infile, attr))

        # Copy the XLONG and XLAT WRF vars to use for the mapping projection
        self.copy_netcdf_var('XLONG', nc_infile, wrfgroup)
        self.copy_netcdf_var('XLAT', nc_infile, wrfgroup)

        # Copy Times but rename it to a COARDS compliant name
        self.copy_netcdf_var('Times', nc_infile, nc_outfile, 'Time')

        # New dimensions in the netCDF file (Time was already copied over above)
        nc_outfile.createDimension('y', len(nc_infile.dimensions['south_north']))
        nc_outfile.createDimension('x', len(nc_infile.dimensions['west_east']))
        nc_outfile.createDimension('atmosphere_sigma_coordinate', len(nc_infile.dimensions['bottom_top']))
        nc_outfile.createDimension('height', len(self.heights_to_interp))


        new_eta_height_coord_var = nc_outfile.createVariable('atmosphere_hybrid_height_coordinate', 'f',
                                                             dimensions=('Time', 'atmosphere_sigma_coordinate', 'y', 'x'))
        new_height_agl_coord_var = nc_outfile.createVariable('height', 'f', dimensions=('height',))
        new_height_agl_coord_var.units = 'm'
        new_height_agl_coord_var.positive = 'true'
        new_height_agl_coord_var[:] = numpy.array(self.heights_to_interp, numpy.float)

        # New variables in the netCDF file
        # Names according to the Climate and Forecast (CF) Convention v29:
        # http://cfconventions.org/Data/cf-standard-names/29/build/cf-standard-name-table.html
        if self.windb2_config.contains_interp_var('WIND'):
            new_u = nc_outfile.createVariable('eastward_wind', 'f', dimensions=('Time', 'height', 'y', 'x'))
            new_v = nc_outfile.createVariable('northward_wind', 'f', dimensions=('Time', 'height', 'y', 'x'))
            HeightInterpFile._set_metadata_uv(new_u, new_v)
        if self.windb2_config.contains_interp_var('THETA'):
            new_theta = nc_outfile.createVariable('air_potential_temperature', 'f',
                                                  dimensions=('Time', 'height', 'y', 'x'))
            HeightInterpFile._set_metadata_theta(new_theta)
        if self.windb2_config.contains_interp_var('PRES'):
            new_pres = nc_outfile.createVariable('air_pressure', 'f', dimensions=('Time', 'height', 'y', 'x'))
            HeightInterpFile._set_metadata_pres(new_pres)
        if self.windb2_config.contains_interp_var('RHO'):
            new_rho = nc_outfile.createVariable('air_density', 'f', dimensions=('Time', 'height', 'y', 'x'))
            HeightInterpFile._set_metadata_rho(new_rho)
        if self.windb2_config.contains_interp_var('DPT'):
            new_dpt = nc_outfile.createVariable('dew_point_temperature', 'f', dimensions=('Time', 'height', 'y', 'x'))
            HeightInterpFile. _set_metadata_dpt(new_dpt)
        if self.windb2_config.contains_interp_var('CLD'):
            new_cloud_fraction = {}
            for height in self.CLOUD_HEIGHTS.keys():
                new_cloud_fraction[height] = nc_outfile.createVariable('cloud_fraction_{}'.format(height), 'f', dimensions=('Time', 'y', 'x'))
            self._set_metadata_cld(new_cloud_fraction, self.CLOUD_HEIGHTS)

        # Calculate the eta half-heights
        height_eta_half_above_ground = self.calc_eta_heights(nc_infile)
        new_eta_height_coord_var[:, :, :, :] = height_eta_half_above_ground[:, :, :, :]

        # Get the wind vars from WRF
        u_var = nc_infile.variables['U'][:, :, :, :]
        v_var = nc_infile.variables['V'][:, :, :, :]

        # Try and get ZNT which will be used for diagnosing winds below the lowest model level
        if self.windb2_config.contains_interp_var('WIND'):
            try:
                znt_var = nc_infile.variables['ZNT'][:, :, :]
                lower_pbl_interp = 'log-law'
            except KeyError:
                lower_pbl_interp = 'log-linear'

            # Add the interpolation method for the lowest level
            new_u.lower_pbl_interp = lower_pbl_interp
            new_v.lower_pbl_interp = lower_pbl_interp

        # Interpolate each variable from eta-mass coordinates to height coordinates
        u_mass = (u_var[:, :, :, 1:] + u_var[:, :, :, :-1]) / 2.
        v_mass = (v_var[:, :, 1:, :] + v_var[:, :, :-1, :]) / 2.
        u_grid_rotated = numpy.ndarray(
            (u_mass.shape[0], len(self.heights_to_interp), u_mass.shape[2], u_mass.shape[3]), numpy.float64)
        v_grid_rotated = numpy.ndarray(u_grid_rotated.shape, numpy.float64)
        for t in range(height_eta_half_above_ground.shape[0]):

            # Calculate the pressure on the eta-levels for this time
            pressure_3d_at_time_t = numpy.concatenate(([nc_infile['PSFC'][t, :, :]],
                                                       nc_infile['P'][t, :, :, :] +
                                                       nc_infile['PB'][t, :, :, :]))

            # Calculate the cloud fractions
            if self.windb2_config.contains_interp_var('CLD'):
                self.calc_cloud_fraction(height_eta_half_above_ground, nc_infile, new_cloud_fraction, t)

            for y in range(height_eta_half_above_ground[t].shape[1]):
                for x in range(height_eta_half_above_ground[t].shape[2]):

                    # Interpolate the wind fields
                    if self.windb2_config.contains_interp_var('WIND'):

                        # Select interpolation for lower PBL
                        if lower_pbl_interp=='log-law':
                            z_o = znt_var[t, y, x]
                        else:
                            z_o = None

                        u_grid_rotated[t, :, y, x], v_grid_rotated[t, :, y, x] = \
                            heightinterp.uv_column_interp(u_mass[t, :, y, x], v_mass[t, :, y, x],
                                                          height_eta_half_above_ground[t, :, y, x],
                                                          self.heights_to_interp, z_o)

                    # Interpolate potential temperature
                    # Return the 2 m potential temperature if below the lowest height in the model
                    if self.windb2_config.contains_interp_var('THETA'):
                        new_theta[t, :, y, x] = numpy.interp(self.heights_to_interp,
                                                             numpy.concatenate(([2],
                                                                                height_eta_half_above_ground[t, :, y,
                                                                                x])),
                                                             numpy.concatenate(([nc_infile['TH2'][t, y, x]],
                                                                                nc_infile['T'][t, :, y, x] + 300.)),
                                                             nc_infile['TH2'][t, y, x])

                    # Interpolate pressure
                    # Use surface pressure at the surface at height zero
                    if self.windb2_config.contains_interp_var('PRES'):
                        new_pres[t, :, y, x] = numpy.interp(self.heights_to_interp,
                                                            numpy.concatenate(([0],
                                                                               height_eta_half_above_ground[t, :, y, x])),
                                                            pressure_3d_at_time_t[y, x])

                    # Interpolate dew point
                    # Use surface pressure at t he surface at height zero
                    if self.windb2_config.contains_interp_var('DPT'):

                        # Combine 2 m and 3D water
                        qvapor = numpy.concatenate(([nc_infile['Q2'][t, y, x]], nc_infile['QVAPOR'][t, :, y, x]))

                        # Calculate the dew point using the equation found in this post: http://forum.wrfforum.com/viewtopic.php?f=7&t=1862
                        A = 2.53e11 # Pa
                        B = 5.42e3 # K
                        E = 0.622 # (approximated from R'/Rv)
                        p = pressure_3d_at_time_t[:, y, x] # pressure in Pa

                        new_dpt[t, :, y, x] = numpy.interp(self.heights_to_interp,
                                                             numpy.concatenate(([0],
                                                                                height_eta_half_above_ground[t, :, y, x])),
                                                             B / numpy.log(A*E/(qvapor*p)))

                    # Interpolate density if inverse density was written out in WRF or if the theta and P were
                    # calculated above
                    #TODO implement check for WRF inverse-air density variable
                    if self.windb2_config.contains_interp_var('RHO') and self.windb2_config.contains_interp_var('THETA')\
                            and self.windb2_config.contains_interp_var('PRES'):

                        # Use the equation of state to calculate the density
                        # TODO this has to convert to actual temperature rather than potential temperature
                        new_rho[:, :, :, :] = new_pres / (numpy.asarray(new_theta)*constants.R_CONST)

        # Rotate the wind to the earth grid
        u_earth_rotated, v_earth_rotated = self._rotate_winds(nc_infile, u_grid_rotated, v_grid_rotated)

        # Write the netCDF vars
        if self.windb2_config.contains_interp_var('WIND'):
            new_eta_height_coord_var[:, :, :, :] = height_eta_half_above_ground
            new_height_agl_coord_var[:] = numpy.array(self.windb2_config.get_float_list('INTERP', 'HEIGHTS'))
            new_u[:, :, :, :] = u_earth_rotated
            new_v[:, :, :, :] = v_earth_rotated

        # Close the file
        nc_outfile.close()

    def _calc_pres(self, height_eta_half_above_ground, nc_infile, t, y, x):
        """Interpolates the pressure at different heights above ground level"""
        return numpy.concatenate(([nc_infile['PSFC'][t, y, x]],
                                  nc_infile['P'][t, :, y, x] +
                                  nc_infile['PB'][t, :, y, x]))

    def _rotate_winds(self, nc_infile, u_grid_rotated, v_grid_rotated):
        """Rotates the coordinates from grid-relative to earth-relative."""

        # Details about this rotation here: http://forum.wrfforum.com/viewtopic.php?f=8&t=3225
        u_earth_rotated = u_grid_rotated * numpy.asarray(nc_infile['COSALPHA'])[:, numpy.newaxis, :, :] - \
                          v_grid_rotated * numpy.asarray(nc_infile['SINALPHA'])[:, numpy.newaxis, :, :]
        v_earth_rotated = v_grid_rotated * numpy.asarray(nc_infile['COSALPHA'])[:, numpy.newaxis, :, :] + \
                          u_grid_rotated * numpy.asarray(nc_infile['SINALPHA'])[:, numpy.newaxis, :, :]
        return u_earth_rotated, v_earth_rotated


    def calc_cloud_fraction(self, height_eta_half_above_ground, nc_infile, new_cloud_fraction, t):

        # Interpolate cloud fraction every 100 m to make the averaging easy
        yx_shape = height_eta_half_above_ground[t, :, :, :].shape[-2:]
        sample_heights = numpy.arange(0, self.CLOUD_HEIGHTS['high']['top'], 100)
        cloudfra_interp_heights = numpy.repeat(sample_heights, numpy.product(yx_shape))\
            .reshape(sample_heights.shape + height_eta_half_above_ground[t, :, :, :].shape[-2:])
        cloudfra_interp = numpy.zeros((1,) + (sample_heights.shape + yx_shape))
        for j in range(yx_shape[0]):
            for i in range(yx_shape[1]):
                cloudfra_interp[t, :, j, i] = numpy.interp(sample_heights,
                                                       numpy.concatenate((numpy.zeros((1,)),
                                                                          height_eta_half_above_ground[t, :, j, i])),
                                                       numpy.concatenate((numpy.zeros((1,)),
                                                                          nc_infile['CLDFRA'][t, :, j, i])))

        # Sum the total cloud cover at each height bin
        cloud_indices = {}
        for height in self.CLOUD_HEIGHTS.keys():
            cloud_indices = numpy.logical_and(cloudfra_interp_heights >= self.CLOUD_HEIGHTS[height]['bottom'],
                                              cloudfra_interp_heights <= self.CLOUD_HEIGHTS[height]['top'])
            for j in range(yx_shape[0]):
                for i in range(yx_shape[1]):
                    new_cloud_fraction[height][t, j, i] = numpy.average((cloudfra_interp[t, :, j, i])[cloud_indices[:, j, i]])