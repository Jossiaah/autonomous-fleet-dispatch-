from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import json

# Import our optimization function and configurations
from ml.optimizer import find_optimal_depot, CHARGING_DEPOTS

app = FastAPI(title="Autonomous Fleet Optimization API")

# Allow our upcoming Next.js frontend to communicate with the API without CORS blockers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage to keep track of the latest state of all vehicles
active_fleet_state: Dict[str, dict] = {}


# --- WEBSOCKET CONNECTION MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send a JSON payload to every connected browser client in real time."""
        # Iterate over a shallow copy to prevent modification errors during iteration
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                # Handle dead/stale connections safely
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

# THIS IS THE MISSING LINE THAT FIXES THE RED UNDERLINES:
manager = ConnectionManager()


# --- DATA MODELS (Pydantic Validation) ---
class TelemetryPayload(BaseModel):
    vehicle_id: str
    lat: float
    lng: float
    battery_soc: float
    status: str
    assigned_depot_id: Optional[str] = None


# --- HTTP ENDPOINTS ---
@app.get("/")
def read_root():
    return {"status": "online", "service": "Fleet Optimization Hub"}

@app.post("/api/telemetry")
async def receive_telemetry(payload: TelemetryPayload):
    """
    Endpoint for the simulator to push live vehicle metrics.
    Updates central state and streams the data out over WebSockets.
    """
    data = payload.model_dump()
    
    # --- OPTIMIZATION LOGIC ---
    # If the vehicle is low on battery and hasn't been assigned a station yet, compute the best one!
    if data["status"] == "LOW_BATTERY" and not data["assigned_depot_id"]:
        optimal_depot = find_optimal_depot(data["lat"], data["lng"], active_fleet_state)
        
        if optimal_depot:
            data["assigned_depot_id"] = optimal_depot["id"]
            data["status"] = "EN_ROUTE_TO_CHARGE"
            print(f"🤖 [OPTIMIZER] Routed {data['vehicle_id']} to {optimal_depot['id']} due to optimal resource cost.")
    
    # Save state and broadcast over WebSockets
    active_fleet_state[payload.vehicle_id] = data
    await manager.broadcast({"type": "VEHICLE_UPDATE", "data": data})
    
    # Return the data state back to the simulator so the vehicle knows its new destination targets
    return {
        "success": True, 
        "assigned_depot_id": data["assigned_depot_id"],
        "status": data["status"],
        "depots": CHARGING_DEPOTS
    }

@app.get("/api/fleet")
def get_current_fleet():
    """Returns the current real-time snapshot of all vehicles."""
    return list(active_fleet_state.values())


# --- WEBSOCKET ROUTE ---
@app.websocket("/ws/fleet")
async def websocket_endpoint(websocket: WebSocket):
    """Persistent connection endpoint for the browser UI dashboard."""
    await manager.connect(websocket)
    try:
        # Immediately feed the connecting client the current snapshot of the entire fleet
        await websocket.send_json({"type": "FLEET_SNAPSHOT", "data": list(active_fleet_state.values())})
        
        while True:
            # Keep the connection alive; listen for any client-side commands
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
