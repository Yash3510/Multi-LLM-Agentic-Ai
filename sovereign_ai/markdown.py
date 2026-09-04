import re


def render(text_widget, content: str) -> None:
    """Insert a small, safe Markdown subset suitable for the Tkinter transcript."""
    text_widget.tag_configure("heading", foreground="#f4b942", font=("Segoe UI", 11, "bold"))
    text_widget.tag_configure("code", background="#172631", foreground="#9fe7d1", font=("Consolas", 10))
    text_widget.tag_configure("bold", font=("Segoe UI", 10, "bold"))
    in_code = False
    for line in content.splitlines(True):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            text_widget.insert("end", line, "code")
        elif re.match(r"^#{1,3} ", line):
            text_widget.insert("end", line, "heading")
        else:
            parts = re.split(r"(\*\*.*?\*\*)", line)
            for part in parts:
                text_widget.insert("end", part, "bold" if part.startswith("**") and part.endswith("**") else "")
