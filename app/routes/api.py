from flask import Blueprint, jsonify, request

from app.services import HealthService, CheckService

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return jsonify(HealthService.get_status())


@api_bp.route("/check/<int:link_id>")
def check(link_id):
    result = CheckService.check_link_async(link_id)

    if result.get("task_id"):
        return jsonify(result)
    elif result.get("success"):
        return jsonify(result)
    else:
        return jsonify(result), 400


@api_bp.route("/check/status/<task_id>")
def check_status(task_id):
    from app.celery_config import celery_app

    task = celery_app.AsyncResult(task_id)

    if task.ready():
        if task.successful():
            return jsonify({"status": "completed", "result": task.result})
        else:
            return jsonify({"status": "failed", "error": str(task.info)})
    else:
        return jsonify({"status": "pending"})
