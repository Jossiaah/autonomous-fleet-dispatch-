import asyncio
import httpx
from config import NUM_VEHICLES, TICK_RATE_SECONDS
from vehicle import AutonomousVehicle

BACKEND_URL = "http://localhost:8000/api/telemetry"

async def handle_telemetry_broadcast(client: httpx.AsyncClient, telemetry_payload: dict):
    """
    Callback function executed by every vehicle on every clock tick.
    Sends data asynchronously via HTTP POST to the FastAPI backend.
    """
    v_id = telemetry_payload["vehicle_id"]
    status = telemetry_payload["status"]
    soc = telemetry_payload["battery_soc"]
    
    try:
        # Send telemetry payload to the FastAPI server
        response = await client.post(BACKEND_URL, json=telemetry_payload)
        
        if response.status_code == 200:
            print(f"📡 [{v_id}] Streamed successfully (Battery: {soc}%, State: {status})")
        else:
            print(f"⚠️ [{v_id}] Server responded with status code: {response.status_code}")
            
    except httpx.RequestError as exc:
        print(f"❌ [{v_id}] Connection error while streaming data: {exc}")

async def main():
    print(f"🚀 Initializing Autonomous Fleet Simulator with {NUM_VEHICLES} vehicles...")
    
    # Instantiate 15 distinct virtual vehicles
    fleet = [AutonomousVehicle() for _ in range(NUM_VEHICLES)]
    
    # Establish a persistent, high-performance async HTTP client session
    async with httpx.AsyncClient(timeout=2.0) as client:
        tasks = []
        for vehicle in fleet:
            # Pass BOTH the network client and the payload into a lambda callback
            callback = lambda payload, c=client: handle_telemetry_broadcast(c, payload)
            tasks.append(asyncio.create_task(vehicle.run_lifecycle(callback)))
            
        print("🛰️  Fleet simulation online. Streaming live telemetry metrics to backend...")
        
        # Run the concurrent event loop indefinitely
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Fleet simulation halted by administrator. Shutting down systems safely.")