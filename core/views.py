import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from core.reindex import run_reindex


@csrf_exempt
@require_POST
def api_reindex(request):
    """
    Called by n8n (not directly by browsers) to rebuild the RAG index.

    Secured with a shared secret rather than login/session auth, since the
    caller is a server (n8n), not a logged-in user. The secret is sent as
    a header: X-Reindex-Secret: <value>

    Set REINDEX_SECRET in .env to something random; n8n's HTTP Request node
    is configured to send the same value in that header.
    """
    provided = request.headers.get("X-Reindex-Secret", "")
    expected = getattr(settings, "REINDEX_SECRET", "")

    if not expected:
        return JsonResponse(
            {"status": "error", "message": "REINDEX_SECRET is not configured on the server."},
            status=500,
        )
    if provided != expected:
        return JsonResponse({"status": "error", "message": "Invalid or missing secret."}, status=403)

    result = run_reindex()
    status_code = 200 if result.get("status") == "ok" else 500
    return JsonResponse(result, status=status_code)
