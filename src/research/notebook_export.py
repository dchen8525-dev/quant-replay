from __future__ import annotations

import io

import pandas as pd


def markdown_to_html(markdown: str) -> str:
    body = markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = []
    for line in body.splitlines():
        if line.startswith("# "):
            lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("- "):
            lines.append(f"<li>{line[2:]}</li>")
        elif line.strip() == "":
            lines.append("")
        else:
            lines.append(f"<p>{line}</p>")
    return "<html><body>\n" + "\n".join(lines) + "\n</body></html>"


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8-sig")


def text_bytes(text: str) -> bytes:
    return text.encode("utf-8")
