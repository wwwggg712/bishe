from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..services.simulation_service import SimulationService

bp = Blueprint("simulation", __name__, url_prefix="/api/simulation")
simulation_service = SimulationService()


@bp.post("/generate-once")
@jwt_required()
def generate_once():
    logs = simulation_service.generate_once_from_db(batch_size=50)
    return jsonify({"generated_count": len(logs), "preview": logs[:5]})


@bp.post("/generate-bulk")
@jwt_required()
def generate_bulk():
    logs = simulation_service.generate_bulk_from_db(batch_size=2000)
    return jsonify({"generated_count": len(logs), "preview": logs[:5]})


@bp.post("/start")
@jwt_required()
def start():
    return jsonify(simulation_service.start_simulation())


@bp.post("/stop")
@jwt_required()
def stop():
    return jsonify(simulation_service.stop_simulation())


@bp.get("/tasks")
@jwt_required()
def tasks():
    return jsonify({"tasks": simulation_service.list_tasks()})
