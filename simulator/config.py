# simulator/config.py
import random

# Simulation settings
NUM_VEHICLES = 15
TICK_RATE_SECONDS = 1.0  # How often vehicles update and broadcast telemetry (1 second)

# Simulated geographical boundaries (e.g., a downtown grid area)
LAT_MIN, LAT_MAX = 34.0000, 34.1000
LNG_MIN, LNG_MAX = -118.3000, -118.2000

# Fixed charging depots in the city
CHARGING_DEPOTS = {
    "DEPOT_NORTH": {
        "id": "DEPOT_NORTH",
        "name": "Northside Fast-Charge Hub",
        "lat": 34.0900,
        "lng": -118.2500,
        "total_plugs": 4,
    },
    "DEPOT_DOWNTOWN": {
        "id": "DEPOT_DOWNTOWN",
        "name": "Downtown Central Station",
        "lat": 34.0400,
        "lng": -118.2200,
        "total_plugs": 6,
    },
    "DEPOT_WEST": {
        "id": "DEPOT_WEST",
        "name": "Westside Eco-Plugs",
        "lat": 34.0200,
        "lng": -118.2900,
        "total_plugs": 3,
    }
}

def get_random_coordinate():
    """Generates a random coordinate within our defined city boundaries."""
    return random.uniform(LAT_MIN, LAT_MAX), random.uniform(LNG_MIN, LNG_MAX)
