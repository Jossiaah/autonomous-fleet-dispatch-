# simulator/vehicle.py
import asyncio
import random
import uuid
import math
from config import get_random_coordinate

class AutonomousVehicle:
    def __init__(self, vehicle_id=None):
        self.vehicle_id = vehicle_id or f"ADV-{str(uuid.uuid4())[:8].upper()}"
        
        # Start at a random location in the city
        self.lat, self.lng = get_random_coordinate()
        
        # Initialize vehicle state metrics
        self.battery_soc = random.uniform(60.0, 100.0) # State of Charge (%)
        self.status = "IDLE"                           # IDLE, DRIVING, LOW_BATTERY, EN_ROUTE_TO_CHARGE, CHARGING
        self.speed = 0.005                             # Coordinate steps per tick (~simulated speed)
        
        # Navigation targets
        self.target_lat = None
        self.target_lng = None
        self.assigned_depot_id = None

    def select_new_delivery_job(self):
        """Assigns a new random destination to the vehicle to simulate a delivery order."""
        self.target_lat, self.target_lng = get_random_coordinate()
        self.status = "DRIVING"

    def move_towards_target(self):
        """Moves the vehicle incrementally closer to its target destination."""
        if not self.target_lat or not self.target_lng:
            return

        # Calculate distance components
        d_lat = self.target_lat - self.lat
        d_lng = self.target_lng - self.lng
        distance = math.sqrt(d_lat**2 + d_lng**2)

        # If we are close enough to the target, snap to it and clear targets
        if distance < self.speed:
            self.lat = self.target_lat
            self.lng = self.target_lng
            self.target_lat = None
            self.target_lng = None
            
            if self.status == "EN_ROUTE_TO_CHARGE":
                self.status = "CHARGING"
            else:
                self.status = "IDLE"
        else:
            # Normalize vector and move at structural speed
            self.lat += (d_lat / distance) * self.speed
            self.lng += (d_lng / distance) * self.speed

        # Drain battery while driving (randomized slightly to simulate traffic/air conditioning)
        self.battery_soc -= random.uniform(0.4, 0.8)
        if self.battery_soc < 0:
            self.battery_soc = 0

        # Safety trigger: Check for low battery threshold
        if self.battery_soc <= 20.0 and self.status == "DRIVING":
            self.status = "LOW_BATTERY"

    def charge_battery(self):
        """Simulates battery replenishment when docked at a station."""
        self.battery_soc += random.uniform(4.0, 6.0) # Fast charging rate
        if self.battery_soc >= 100.0:
            self.battery_soc = 100.0
            self.status = "IDLE"
            self.assigned_depot_id = None

    async def run_lifecycle(self, on_telemetry_tick):
        """Continuous async loop executing individual vehicle actions per tick."""
        while True:
            if self.status == "IDLE":
                self.select_new_delivery_job()
            elif self.status in ["DRIVING", "EN_ROUTE_TO_CHARGE"]:
                self.move_towards_target()
            elif self.status == "CHARGING":
                self.charge_battery()

            # Construct the current telemetry payload
            telemetry = {
                "vehicle_id": self.vehicle_id,
                "lat": round(self.lat, 5),
                "lng": round(self.lng, 5),
                "battery_soc": round(self.battery_soc, 1),
                "status": self.status,
                "assigned_depot_id": self.assigned_depot_id
            }

            # Fire callback function to broadcast this payload to the pipeline
            await on_telemetry_tick(telemetry)
            
            # Wait for next clock tick
            await asyncio.sleep(1)
