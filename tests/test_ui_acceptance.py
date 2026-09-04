import threading
import time
import unittest


class TkinterAcceptanceTests(unittest.TestCase):
    def test_tkinter_launch_and_event_loop_stay_responsive(self):
        import tkinter as tk
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"Tkinter display unavailable: {exc}")
        root.withdraw()
        completed = threading.Event()
        started = time.monotonic()

        def worker():
            time.sleep(0.15)
            root.after(0, completed.set)

        threading.Thread(target=worker, daemon=True).start()
        root.after(500, root.quit)
        root.mainloop()
        elapsed = time.monotonic() - started
        root.destroy()
        self.assertTrue(completed.is_set(), "Tkinter event loop did not process background completion")
        self.assertLess(elapsed, 1.0)
