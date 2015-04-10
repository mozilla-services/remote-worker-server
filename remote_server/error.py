def build_message(message_type, status, reason, worker_id=None, **kwargs):
    result = {
        "messageType": "progress",
        "workerId": worker_id,
        "status": "terminated",
        "reason": reason
    }
    result.update(kwargs)
    return result


def error(message, worker_id=None):
    return build_message("progress", "terminated", message, worker_id)
