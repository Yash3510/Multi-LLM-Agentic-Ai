// Server-side functions (admin F133 to F168). This build shows them only: saving, enabling and
// running wait for the 4CE server, as the owner chose. The starters are written for 4CE (the
// running app's sample is not carried over).

export const NOT_YET =
  'Functions are saved by the 4CE server, which is not connected in this build. Nothing was changed.';

export const STARTERS = {
  filter: `"""
title: My Filter
version: 0.1.0
"""


class Filter:
    def __init__(self):
        pass

    def inlet(self, body: dict) -> dict:
        """
        Runs before the request reaches the model: tidy or check the messages here.
        """
        for message in body.get("messages", []):
            if isinstance(message.get("content"), str):
                message["content"] = message["content"].strip()
        return body

    def outlet(self, body: dict) -> dict:
        """
        Runs after the model answers: adjust the reply before it is shown.
        """
        return body
`,
  event: `"""
title: My Event
version: 0.1.0
"""


class Event:
    def __init__(self):
        pass

    async def on_event(self, event: dict) -> None:
        """
        Called for each event the server sends, such as a chat finishing.
        """
        kind = event.get("type", "unknown")
        print(f"event received: {kind}")
`,
} as const;
