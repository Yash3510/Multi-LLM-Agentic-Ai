from .database import Database


def check(db: Database, provider, storage_dir, settings=None):
    model_ok, model_message = provider.health_check()
    db_ok = db.connection.execute("SELECT 1").fetchone() is not None
    result = {
        "Backend": (True, "Application ready"),
        "Database": (db_ok, "SQLite connected" if db_ok else "SQLite unavailable"),
        "Model backend": (model_ok, model_message),
        "Storage": (storage_dir.exists(), "Secure local storage ready" if storage_dir.exists() else "Storage unavailable"),
    }
    if settings:
        from .security import security_snapshot
        result.update(security_snapshot(db, settings))
    return result
