"""
DRIFTGUARD 2.0 Simulation Studio Router
Controls UPI streaming ingestion, scenario injection, and real-time WebSocket broadcasting.
"""

from fastapi import APIRouter, Body, BackgroundTasks, Response
from typing import Dict, Any, List, Optional
import asyncio
import threading
import time
from datetime import datetime, timezone
from simulation.stream_controller import StreamController, StreamState
from simulation.scenarios import ScenarioType, SCENARIO_CONFIGS
from backend.websocket import ws_manager

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])

# Global operator state machine
CONTROLLER = StreamController()
_SIM_STATE = {
    "state": StreamState.STOPPED.value,
    "current_scenario": ScenarioType.UPI_NORMAL.value,
    "events_per_second": 1.0,
    "total_generated": 0,
    "last_event_time": None,
}
_BG_THREAD: Optional[threading.Thread] = None
_STOP_EVENT = threading.Event()


def _background_worker():
    """Background continuous generation loop."""
    global _SIM_STATE
    while not _STOP_EVENT.is_set():
        if _SIM_STATE["state"] == StreamState.RUNNING.value:
            try:
                scenario_enum = ScenarioType(_SIM_STATE["current_scenario"])
                results = CONTROLLER.step(scenario=scenario_enum, count=1)
                if results:
                    _SIM_STATE["total_generated"] += len(results)
                    _SIM_STATE["last_event_time"] = datetime.now(timezone.utc).isoformat()
                    # Broadcast to connected WebSocket clients via asyncio event loop if available
                    for res in results:
                        asyncio.run(ws_manager.broadcast({"type": "NEW_TRANSACTION", "data": res}))
            except Exception as e:
                pass
        time.sleep(1.0 / max(0.2, _SIM_STATE["events_per_second"]))


@router.get("/state")
def get_simulation_state() -> Dict[str, Any]:
    """Returns current live simulation generator state."""
    return {
        "status": "success",
        "state": _SIM_STATE,
    }


@router.post("/start")
def start_simulation(
    scenario: str = Body(ScenarioType.UPI_NORMAL.value, embed=True),
    speed: float = Body(1.0, embed=True),  # events per second
) -> Dict[str, Any]:
    """Starts continuous streaming UPI simulation."""
    global _BG_THREAD, _SIM_STATE
    _SIM_STATE["state"] = StreamState.RUNNING.value
    _SIM_STATE["current_scenario"] = scenario
    _SIM_STATE["events_per_second"] = min(10.0, max(0.2, speed))
    _STOP_EVENT.clear()

    if _BG_THREAD is None or not _BG_THREAD.is_alive():
        _BG_THREAD = threading.Thread(target=_background_worker, daemon=True)
        _BG_THREAD.start()

    return {
        "status": "success",
        "message": f"Simulation streaming started ({_SIM_STATE['events_per_second']} tx/s)",
        "state": _SIM_STATE,
    }


@router.post("/pause")
def pause_simulation() -> Dict[str, Any]:
    """Pauses continuous simulation."""
    global _SIM_STATE
    _SIM_STATE["state"] = StreamState.PAUSED.value
    return {
        "status": "success",
        "message": "Simulation paused",
        "state": _SIM_STATE,
    }


@router.post("/step")
def step_simulation(
    count: int = 5,
    scenario: str = ScenarioType.UPI_NORMAL.value,
) -> Dict[str, Any]:
    """Executes a discrete step of N events and broadcasts them to all WebSocket clients."""
    global _SIM_STATE
    scenario_enum = ScenarioType(scenario) if scenario in [s.value for s in ScenarioType] else ScenarioType.UPI_NORMAL
    results = CONTROLLER.step(scenario=scenario_enum, count=count)
    _SIM_STATE["total_generated"] += len(results)
    _SIM_STATE["last_event_time"] = datetime.now(timezone.utc).isoformat()

    # Safely broadcast to active WebSockets if loop running
    if ws_manager.active_connections:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                for r in results:
                    asyncio.create_task(ws_manager.broadcast({"type": "NEW_TRANSACTION", "data": r}))
        except Exception:
            pass

    return {
        "status": "success",
        "count": len(results),
        "results": results,
    }


@router.post("/inject")
async def inject_scenario_attack(
    scenario: str = Body(ScenarioType.UPI_AMOUNT_SPIKE.value, embed=True),
    tamper: bool = Body(False, embed=True),
) -> Dict[str, Any]:
    """Instantly injects an attack or anomaly scenario for live demonstration."""
    global _SIM_STATE
    scenario_enum = ScenarioType(scenario) if scenario in [s.value for s in ScenarioType] else ScenarioType.UPI_AMOUNT_SPIKE
    res = CONTROLLER.trigger_single_scenario(scenario=scenario_enum, tamper=tamper)
    _SIM_STATE["total_generated"] += 1
    _SIM_STATE["last_event_time"] = datetime.now(timezone.utc).isoformat()

    # Broadcast to WebSocket
    await ws_manager.broadcast({"type": "NEW_TRANSACTION", "data": res})

    return {
        "status": "success",
        "scenario": scenario,
        "result": res,
    }


@router.post("/reset")
def reset_simulation() -> Dict[str, Any]:
    """Stops simulation generator and resets session counters."""
    global _SIM_STATE
    _SIM_STATE["state"] = StreamState.STOPPED.value
    _STOP_EVENT.set()
    return {
        "status": "success",
        "message": "Simulation reset and stopped",
        "state": _SIM_STATE,
    }


@router.get("/scenarios")
def list_available_scenarios() -> Dict[str, Any]:
    """Retrieves all pre-configured normal, drift, and threat attack scenarios."""
    scenarios = []
    threat_map = {
        ScenarioType.UPI_NORMAL.value: "BENIGN",
        ScenarioType.NORMAL.value: "BENIGN",
        ScenarioType.REAL_DATA_REPLAY.value: "BENIGN",
        ScenarioType.UPI_AMOUNT_SPIKE.value: "HIGH",
        ScenarioType.AMOUNT_SPIKE.value: "HIGH",
        ScenarioType.UPI_VELOCITY_BURST.value: "CRITICAL",
        ScenarioType.VELOCITY_BURST.value: "CRITICAL",
        ScenarioType.UPI_NEW_PAYEE.value: "MEDIUM",
        ScenarioType.UPI_DEVICE_CHANGE.value: "HIGH",
        ScenarioType.DEVICE_SWITCH.value: "HIGH",
        ScenarioType.UPI_LOCATION_JUMP.value: "CRITICAL",
        ScenarioType.NETWORK_HOP.value: "HIGH",
        ScenarioType.UPI_MULE_RING.value: "CRITICAL",
        ScenarioType.UPI_REPLAY_ATTACK.value: "CRITICAL",
        ScenarioType.REPLAY_ATTACK.value: "CRITICAL",
        ScenarioType.UPI_TAMPERED.value: "CRITICAL",
        ScenarioType.TAMPERED_SIGNATURE.value: "CRITICAL",
        ScenarioType.FRAUD_PATTERN_SHIFT.value: "HIGH",
    }

    for sc_type in ScenarioType:
        cfg = SCENARIO_CONFIGS.get(sc_type, {})
        scenarios.append({
            "id": sc_type.value,
            "name": sc_type.name.replace("_", " ").title(),
            "description": cfg.get("description", "Deterministic simulation scenario."),
            "threat_level": threat_map.get(sc_type.value, "MEDIUM"),
            "mean_amount": cfg.get("mean_amount", 100.0),
            "is_anomaly": cfg.get("is_anomaly", False),
        })

    return {
        "status": "success",
        "total": len(scenarios),
        "scenarios": scenarios,
    }


@router.get("/export")
def export_transactions_csv(limit: int = 500):
    """Exports recent transaction records as a downloadable CSV."""
    csv_data = CONTROLLER.export_csv(limit=limit)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=driftguard_export_{int(time.time())}.csv"},
    )
