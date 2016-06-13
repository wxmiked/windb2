-- Add Python 3 as a language
CREATE LANGUAGE plpythonu;

-- calc_dir_deg was copied directly over from windb2.util
-- Instead of calling calc_dir_deg as a pass-thru function which would require
-- several imports, this code was pasted in to improve performance so that
-- imports would not have to occur each time this function was called.
CREATE FUNCTION calc_dir_deg(u FLOAT, v FLOAT)
  RETURNS FLOAT
AS $$
    """Calculates the direction from the orthogonal wind components.
    *
    * u U wind scalar velocity.
    * v V wind scalar velocity.

    * Returns he direction that the wind is blowing from.
    """

    import math

    # Calculate the direction and round it into a integer
    try:
        direction = math.degrees(math.atan(math.fabs(v/u)))
    except ZeroDivisionError:
        # This can happen if u is zero, see what v is and return 0 i.e. arctangent
        # The sign will be sorted out below
        direction = 0

    # Division by zero case from above
    if u == 0.0 and v >= 0:
        direction = 0
    elif u == 0.0 and v < 0:
        direction = 180

    # Calculate the quadrant of the wind
    # NE quadrant
    elif u > 0 and v >= 0:
        direction = 90 - direction

    # SE quadrant
    elif u >= 0 and v < 0:
        direction += 90;

    # SW quadrant
    elif u < 0 and v <= 0:
        direction = 270 - direction

    # NW quadrant
    elif u <= 0 and v > 0:
        direction += 270;

    # Set to zero degrees if 360 to avoid ambuigity
    if direction == 360:
        direction = 0

    # Throw an exception if the wind direction is greater than 360 or negative
    if direction < 0:
        raise ValueError("You cannot have a negative wind direction here: " + direction + " degrees is invalid.")

    if direction >= 360:
        raise ValueError("You cannot have a wind direction >= 360 here: " + direction + " degrees is invalid.")

    return direction

$$ LANGUAGE plpython3u;
