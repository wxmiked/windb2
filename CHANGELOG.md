# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [3.1.6] - 2018-07-05
* Added in `ValidError` and `ValidGeom` tables to allow the insertion of MADIS data
* Minor bug fixes
* Removed some logging that was not consistent 

## [3.1.5] - 2018-05-11
* Minor updates of logging code from Python 2 to 3

## [3.1.4] - 2018-05-02
* Repurposed GeoVariable code to insert all kinds of observations
* Fixed a few things to enable inserting MADIS data

## [3.1.3] - 2018-04-13
* height-interp.nc files are now only opened and closed once when copying WRF variables

## [3.1.2] - 2018-04-12
* fixed the slow insert problem by reading netCDF vars into numpy array

## [3.1.1] - 2018-03-21
* bug fix for cloud fraction
* fog is now simply the cloud fraction in the lowest layer above ground level (0 or 1)
* vastly improved performance of array operations for cloud fraction
* WRF variables are now copied into the "WRF" group with their original name

## [3.1.0] - 2018-03-19 
* calculates low, medium, and high clouds, in addition to fog
* now copies WRF 3D (2D space + time) variables to the height-interp file for archiving
* added dew point as an interpolated variable
* fixed logging levels
* format changes to `windb2-wrf.conf` ([example file](https://github.com/sailorsenergy/windb2/blob/master/config/windb2-wrf.conf) here)

## [3.0.0] - 2018-03-05
### Changed
* WRF model now contains initialization times
* any WRF 3D variable can be inserted (2D space + 1D time)
* timezone is now set to UTC for all connections
* improved and clarified `windb2-wrf.config` variables-to-insert options
* set 3D WRF vars (2D space plus time) to height zero
