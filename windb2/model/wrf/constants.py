#!/usr/bin/python
#
#
# Mike Dvorak
# Sail Tactics
# mike@sailtactics.com
#
# Created: 2015-08-28
# Modified:
#
#
# Description: This uses constants found in a WRFV3.2 output file that
# could potentially change at a different domain location.  Use at
# your own risk.
#

# Constants
R_CONST = 287.04 # Gas constant for dry air (Pa/kg-K)
G_CONST = 9.80665 # Gravity constant in m/s^2
REF_PRES = 100000. # Reference pressure in WRF is 1E5 Pa (1000 hPa), according to WRF Tech Descritpion, Skamarock, 2008. p. 8
KAPPA = 0.28571 # Kappa constant used for potential temperature (R_D/C_P) (p. 46, Stull, 2000)

# Base state variables from a WRFV3.2 output file
baseSeaLevelPressure = 1.e5 # base state sea-level pressure in Pa (P00 variable)
baseSeaLevelTemperature = 290. # base state sea-level temperature (K) (T00 variable)
baseLapseRate = 50. # base state lapse rate d(T)/d(lnp) (TLP variable)
topPressure = 5.e3 # top pressure (Pa) (P_TOP variable)
