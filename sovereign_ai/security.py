import json
from .config import is_local_endpoint


def security_snapshot(db, settings):
    """Return enforceable local-only state and measured security events."""
    blocked = db.execute("SELECT COUNT(*) FROM audit_events WHERE action='security_blocked'").fetchone()[0]
    model_calls = db.execute("SELECT COUNT(*) FROM audit_events WHERE action='model_invocation'").fetchone()[0]
    return {
        "Sovereign mode": (settings.sovereign_mode, "local-only policy enforced" if settings.sovereign_mode else "disabled"),
        "External APIs": (not settings.sovereign_mode or is_local_endpoint(settings.local_model_url), "blocked" if settings.sovereign_mode else "allowed by configuration"),
        "Cloud telemetry": (True, "not configured"),
        "Security events": (True, f"{blocked} blocked request(s), {model_calls} local model call(s)"),
    }


def record_blocked(db, endpoint, reason):
    db.execute("INSERT INTO audit_events(username,action,details) VALUES(?,?,?)", ("system", "security_blocked", json.dumps({"endpoint": endpoint, "reason": reason})))
