#!/usr/bin/env python3
"""Build the weather registry only from reviewed LGD and coordinate evidence.

Use ``resolve_weather_locations.py --prepare-inputs`` to create review
templates, then pass the reviewed LGD snapshot, crosswalk, and coordinate
evidence to this command. Existing verified pilot points are preserved by
the reviewed-registry builder.
"""

from resolve_weather_locations import main


if __name__ == "__main__":
    main()
