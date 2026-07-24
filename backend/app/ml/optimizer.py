import math
from typing import Optional, Dict, Any

# Replicating the depot coordinates from the simulator config so the backend knows where they are
CHARGING_DEPOTS = {
    "DEPOT_NORTH": {"id": "DEPOT_NORTH", "lat": 34.0900, "lng": -118.2500, "total_plugs": 4},
    "DEPOT_DOWNTOWN": {"id": "DEPOT_DOWNTOWN", "lat": 34.0400, "lng": -118.2200, "total_plugs": 6},
    "DEPOT_WEST": {"id": "DEPOT_WEST", "lat": 34.0200, "lng": -118.2900, "total_plugs": 3}
}

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculates straight-line Euclidean distance between two points on the grid."""
    return math.sqrt((lat1 - lat2)**2 + (lng1 - lng2)**2)

def calculate_depot_queues(active_fleet_state: dict) -> Dict[str, int]:
    """
    Counts how many vehicles are currently headed to or charging at each depot.
    Returns a dictionary mapping depot_id -> count.
    """
    counts = {depot_id: 0 for depot_id in CHARGING_DEPOTS.keys()}
    
    for vehicle in active_fleet_state.values():
        assigned = vehicle.get("assigned_depot_id")
        if assigned in counts:
            counts[assigned] += 1
            
    return counts

def find_optimal_depot(vehicle_lat: float, vehicle_lng: float, active_fleet_state: dict) -> Optional[Dict[str, Any]]:
    """
    Optimization Engine: Evaluates all depots using a cost function that considers
    both travel distance and current station congestion.
    """
    depot_queues = calculate_depot_queues(active_fleet_state)
    best_depot: Optional[Dict[str, Any]] = None
    lowest_cost = float('inf')

    for depot_id, depot_info in CHARGING_DEPOTS.items():
        # 1. Calculate structural distance cost
        distance = calculate_distance(vehicle_lat, vehicle_lng, depot_info["lat"], depot_info["lng"])
        
        # 2. Calculate congestion penalty
        # If the number of assigned vehicles exceeds total available plugs, create a heavy wait-time penalty
        current_load = depot_queues[depot_id]
        capacity_delta = current_load - depot_info["total_plugs"]
        congestion_penalty = max(0, capacity_delta) * 0.05  # Scale factor for wait-time weight
        
        # Total cost equation
        total_cost = distance + congestion_penalty

        if total_cost < lowest_cost:
            lowest_cost = total_cost
            best_depot = depot_info

    return best_depot
