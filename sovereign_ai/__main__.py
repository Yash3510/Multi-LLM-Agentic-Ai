import argparse
import threading
from .config import load_settings
from .database import Database
from .local_provider import OpenAICompatibleProvider
from .api import ApiServer
from .logging_config import configure_logging
from .ui import SovereignApp
from .knowledge import KnowledgeService


def main():
    settings = load_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    configure_logging(settings.data_dir)
    db = Database(settings.db_path)
    provider = OpenAICompatibleProvider(settings.local_model_url)
    knowledge = KnowledgeService(db, settings.storage_dir, settings.local_model_url, provider, settings.embedding_model,
                                 {"top_k": settings.knowledge_top_k, "similarity_threshold": settings.knowledge_similarity_threshold})
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", action="store_true", help="Run the local HTTP API without Tkinter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    api = ApiServer(args.host, args.port, db, provider, settings)
    if args.api:
        try: api.serve_forever()
        finally: api.shutdown(); db.close()
        return
    app = SovereignApp(db, provider, settings, knowledge)
    try: app.mainloop()
    finally: db.close()


if __name__ == "__main__": main()
