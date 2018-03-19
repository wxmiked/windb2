# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2018-03-19 
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
