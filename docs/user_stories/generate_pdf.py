"""
Generate PDF from user_stories_questionnaire.md using WeasyPrint.

Usage: python docs/user_stories/generate_pdf.py
Output: docs/user_stories/AHCAM_User_Stories_Questionnaire.pdf
"""

from pathlib import Path
import markdown
from weasyprint import HTML

ROOT = Path(__file__).parent
MD_PATH = ROOT / "user_stories_questionnaire.md"
PDF_PATH = ROOT / "AHCAM_User_Stories_Questionnaire.pdf"

CSS = """
@page {
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {
        content: "Ashland Hill Collection Account Management — User Stories & Questionnaire";
        font-size: 7pt;
        color: #94a3b8;
    }
    @bottom-right {
        content: counter(page);
        font-size: 8pt;
        color: #94a3b8;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #1e293b;
}

h1 {
    font-size: 22pt;
    font-weight: 700;
    color: #0066cc;
    border-bottom: 3px solid #0066cc;
    padding-bottom: 8pt;
    margin-top: 0;
}

h2 {
    font-size: 15pt;
    font-weight: 700;
    color: #1e293b;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4pt;
    margin-top: 24pt;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    font-weight: 600;
    color: #334155;
    margin-top: 18pt;
    page-break-after: avoid;
}

p { margin: 6pt 0; }

blockquote {
    border-left: 3px solid #0066cc;
    margin: 10pt 0;
    padding: 8pt 12pt;
    background: #f0f7ff;
    color: #334155;
    font-size: 9.5pt;
}

blockquote p { margin: 3pt 0; }

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10pt 0;
    font-size: 9pt;
    page-break-inside: avoid;
}

th {
    background: #f1f5f9;
    color: #475569;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 8pt;
    letter-spacing: 0.5pt;
    padding: 6pt 8pt;
    border-bottom: 2px solid #cbd5e1;
    text-align: left;
}

td {
    padding: 5pt 8pt;
    border-bottom: 1px solid #f1f5f9;
    color: #1e293b;
    vertical-align: top;
}

tr:nth-child(even) td {
    background: #f8fafc;
}

ul, ol {
    margin: 6pt 0;
    padding-left: 20pt;
}

li {
    margin: 3pt 0;
}

/* Questionnaire questions styled distinctly */
li:has(> text) {
    margin: 4pt 0;
}

strong { color: #0f172a; }

code {
    font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 8.5pt;
    background: #f1f5f9;
    padding: 1pt 4pt;
    border-radius: 3pt;
    color: #0f172a;
}

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 20pt 0;
}
"""


def main():
    md_text = MD_PATH.read_text(encoding="utf-8")

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code"],
    )

    html_doc = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{html_body}</body>
</html>"""

    HTML(string=html_doc).write_pdf(str(PDF_PATH))
    size_kb = PDF_PATH.stat().st_size / 1024
    print(f"Generated: {PDF_PATH} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
