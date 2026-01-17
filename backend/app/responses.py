from rest_framework.response import Response

def ok(data: dict, status=200):
    return Response({"ok": True, **data}, status=status)

def ng(*, state: str, code: str, message: str, status=400, prompt: str | None = None):
    body = {
        "ok": False,
        "state": state,
        "error": {"code": code, "message": message},
    }
    if prompt is not None:
        body["prompt"] = prompt
    return Response(body, status=status)
