# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [3.3.1] - 2018-11-01
* Added ability to have moving observations in variable tables

## [3.3.0] - 2018-10-15
* WRF coordinates are now ingested in their native lambert conformal conic coordinate
* Fixed bug where overwriting data does actually write new data
* Fixed bug that prevented surface WRF variables from be inserted

## [3.2.1] - 2018-08-24
* Fixed insert of copied WRF vars, works with 2 or 3 dimension variables

## [3.2.0] - 2018-08-23
* Python config file replaced with new JSON config

## [3.1.9] - 2018-07-13
* Small bug fix for table_exists

## [3.1.8] - 2018-07-09
* Fixed cloud fraction bug and algorithm

## [3.1.7] - 2018-07-06
* Refactored `ValidError` and `ValidStation` (renamed from `ValidGeom`) to store forecast and obs values
* Fixed bug that inserted more heights than specified in the `windb2-wrf.conf`

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
* Height-interp.nc files are now only opened and closed once when copying WRF variables

## [3.1.2] - 2018-04-12
* Fixed the slow insert problem by reading netCDF vars into numpy array

## [3.1.1] - 2018-03-21
* Bug fix for cloud fraction
* Fog is now simply the cloud fraction in the lowest layer above ground level (0 or 1)
* Vastly improved performance of array operations for cloud fraction
* WRF variables are now copied into the "WRF" group with their original name

## [3.1.0] - 2018-03-19 
* Calculates low, medium, and high clouds, in addition to fog
* Now copies WRF 3D (2D space + time) variables to the height-interp file for archiving
* Added dew point as an interpolated variable
* Fixed logging levels
* Format changes to `windb2-wrf.conf` ([example file](https://github.com/sailorsenergy/windb2/blob/master/config/windb2-wrf.conf) here)

## [3.0.0] - 2018-03-05
### Changed
* WRF model now contains initialization times
* Any WRF 3D variable can be inserted (2D space + 1D time)
* Timezone is now set to UTC for all connections
* Improved and clarified `windb2-wrf.config` variables-to-insert options
* Set 3D WRF vars (2D space plus time) to height zero
