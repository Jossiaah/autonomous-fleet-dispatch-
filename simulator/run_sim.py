import asyncio
from config import NUM_VEHICLES, TICK_RATE_SECONDS
from vehicle import AutonomousVehicle

async def handle_telemetry_broadcast(telemetry_payload):
    """
    Callback function executed by every vehicle on every clock tick.
    Currently prints to terminal; will stream to the backend in Phase 2.
    """
    v_id = telemetry_payload["vehicle_id"]
    status = telemetry_payload["status"]
    soc = telemetry_payload["battery_soc"]
    lat, lng = telemetry_payload["lat"], telemetry_payload["lng"]
    
    # Format a clean, scannable dashboard print to the console
    print(f"[{v_id}] State: {status:<18} | Battery: {soc:>5}% | Position: ({lat}, {lng})")

async def main():
    print(f"🚀 Initializing Autonomous Fleet Simulator with {NUM_VEHICLES} vehicles...")
    
    # Instantiate 15 distinct virtual vehicles
    fleet = [AutonomousVehicle() for _ in range(NUM_VEHICLES)]
    
    # Schedule all vehicle lifecycles to run concurrently
    tasks = []
    for vehicle in fleet:
        tasks.append(asyncio.create_task(vehicle.run_lifecycle(handle_telemetry_broadcast)))
        
    print("🛰️  Fleet simulation online. Streaming live telemetry metrics...")
    
    # Run the concurrent event loop indefinitely
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Fleet simulation halted by administrator. Shutting down systems safely.")