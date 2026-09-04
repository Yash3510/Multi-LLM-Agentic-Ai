from concurrent.futures import ThreadPoolExecutor


class BackgroundTaskManager:
    """Single-server worker pool for non-blocking API task execution."""

    def __init__(self, engine, workers=2, on_complete=None):
        self.engine = engine
        self.on_complete = on_complete
        self.executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="agent-task")

    def submit(self, request, user_name="local-user", model=None, conversation_id=None):
        task_id = self.engine.create_task(request, user_name, model, conversation_id)
        self.executor.submit(self._run, request, conversation_id, user_name, model, task_id)
        return task_id

    def _run(self, request, conversation_id, user_name, model, task_id):
        result = self.engine.run(request, conversation_id, user_name, model, None, task_id)
        if self.on_complete:
            self.on_complete(request, conversation_id, result)
        return result

    def shutdown(self):
        self.executor.shutdown(wait=False, cancel_futures=True)
