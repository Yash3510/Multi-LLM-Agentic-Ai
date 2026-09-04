from .database import Database


def check(db: Database, provider, storage_dir):
    model_ok, model_message = provider.health_check()
    db_ok = db.connection.execute("SELECT 1").fetchone() is not None
    return {
        "Backend": (True, "Application ready"),
        "Database": (db_ok, "SQLite connected" if db_ok else "SQLite unavailable"),
        "Model backend": (model_ok, model_message),
        "Storage": (storage_dir.exists(), "Secure local storage ready" if storage_dir.exists() else "Storage unavailable"),
    }
