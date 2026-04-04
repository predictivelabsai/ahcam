"""
Documents module - View and manage documents with PDF viewer + highlighting.

Serves PDFs from doc-data/ and uploaded files. Uses PDF.js for in-browser viewing
with text search highlighting.
"""

import uuid
import hashlib
from pathlib import Path

from fasthtml.common import *
from starlette.responses import FileResponse as _FileResponse, Response as _RawResponse
from sqlalchemy import text
from utils.db import get_pool

DOC_DIR = Path(__file__).parent.parent / "doc-data"

# In-memory store for uploaded files
uploaded_files: dict = {}


# ---------------------------------------------------------------------------
# PDF serving
# ---------------------------------------------------------------------------

def _serve_pdf(file_path: Path):
    """Serve a PDF file with inline disposition."""
    if not file_path.exists():
        return _RawResponse("File not found", status_code=404)
    return _FileResponse(
        str(file_path),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename=\"{file_path.name}\"",
            "Cache-Control": "public, max-age=86400",
        },
    )


# ---------------------------------------------------------------------------
# AI Agent Tool
# ---------------------------------------------------------------------------

def search_documents(query: str = "") -> str:
    """Search available documents in doc-data/. Returns markdown table."""
    try:
        files = sorted(DOC_DIR.glob("*.pdf"))
        if query:
            q = query.lower()
            files = [f for f in files if q in f.name.lower()]
        if not files:
            return "No documents found."
        header = "| Document | Type | Size |\n|----------|------|------|\n"
        lines = []
        for f in files[:20]:
            dtype = f.name.split("_")[0]
            size = f"{f.stat().st_size / 1024:.0f} KB"
            lines.append(f"| {f.name} | {dtype} | {size} |")
        return f"## Documents\n\n{header}" + "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Module Routes
# ---------------------------------------------------------------------------

def register_routes(rt):

    @rt("/doc-pdf")
    def serve_doc_pdf(name: str = ""):
        """Serve a PDF from doc-data/ directory. Usage: /doc-pdf?name=filename.pdf"""
        if not name:
            return _RawResponse("Missing name parameter", status_code=400)
        safe = Path(name).name
        return _serve_pdf(DOC_DIR / safe)

    @rt("/uploaded-pdf/{file_id}")
    def serve_uploaded_pdf(file_id: str):
        """Serve an uploaded PDF from memory."""
        file_info = uploaded_files.get(file_id)
        if not file_info:
            return _RawResponse("File not found", status_code=404)
        return _RawResponse(
            content=file_info["bytes"],
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=\"{file_info['filename']}\""},
        )

    @rt("/upload-doc", methods=["POST"])
    async def upload_doc(req):
        """Upload a PDF file."""
        form = await req.form()
        file = form.get("file")
        if not file:
            return {"error": "No file provided"}
        content = await file.read()
        file_id = str(uuid.uuid4())
        uploaded_files[file_id] = {"bytes": content, "filename": file.filename}
        return {"file_id": file_id, "filename": file.filename}

    @rt("/module/documents")
    def module_documents(session, q: str = ""):
        """Document library with PDF viewer."""
        files = sorted(DOC_DIR.glob("*.pdf"))
        if q:
            ql = q.lower()
            files = [f for f in files if ql in f.name.lower()]

        # Group by type
        groups = {}
        for f in files:
            dtype = f.name.split("_")[0]
            groups.setdefault(dtype, []).append(f)

        type_labels = {"CAMA": "CAMA Contracts", "STMT": "Collection Statements",
                       "DIST": "Distribution Agreements", "IPA": "Interparty Agreements"}

        doc_sections = []
        for dtype, type_files in groups.items():
            cards = []
            for f in type_files:
                size = f"{f.stat().st_size / 1024:.0f} KB"
                # Extract production name from filename
                parts = f.stem.split("_")
                prod_name = " ".join(parts[1:-1]) if len(parts) > 2 else f.stem
                cards.append(Div(
                    Div(
                        Span(prod_name[:35], cls="deal-card-title"),
                        Span(size, cls="badge-blue"),
                        style="display:flex;justify-content:space-between;align-items:center;",
                    ),
                    Div(f.name, cls="deal-card-meta"),
                    cls="deal-card",
                    onclick=f"openDocViewer('{f.name}', '')",
                ))
            doc_sections.append(Div(
                H4(type_labels.get(dtype, dtype), style="margin-bottom:0.5rem;"),
                *cards,
                style="margin-bottom:1.5rem;",
            ))

        return Div(
            Div(
                Div(Div(str(len(files)), cls="stat-value"), Div("Total Documents", cls="stat-label"), cls="stat-card"),
                Div(Div(str(len(groups.get("CAMA", []))), cls="stat-value"), Div("CAMA Contracts", cls="stat-label"), cls="stat-card"),
                Div(Div(str(len(groups.get("STMT", []))), cls="stat-value"), Div("Statements", cls="stat-label"), cls="stat-card"),
                Div(Div(str(len(groups.get("DIST", []))+len(groups.get("IPA", []))), cls="stat-value"), Div("Other Agreements", cls="stat-label"), cls="stat-card"),
                cls="stat-grid",
            ),
            Div(
                Div(
                    H3("Document Library"),
                    Div(
                        Input(type="text", placeholder="Filter documents...", value=q or "",
                              hx_get="/module/documents", hx_target="#center-content", hx_swap="innerHTML",
                              hx_trigger="keyup changed delay:300ms", name="q",
                              style="padding:0.3rem 0.6rem;border:1px solid #e2e8f0;border-radius:6px;font-size:0.8rem;width:200px;"),
                        style="display:flex;gap:0.5rem;",
                    ),
                    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;",
                ),
                *doc_sections,
                cls="module-list",
            ),
            # PDF viewer overlay (slides in from right)
            Div(
                Div(
                    Div(
                        H3("Document Viewer", style="margin:0;"),
                        Span("", id="doc-viewer-filename", cls="deal-card-meta"),
                        style="flex:1;",
                    ),
                    Div(
                        Input(type="text", id="doc-search-input", placeholder="Search in PDF...",
                              onkeydown="if(event.key==='Enter'){searchInDoc();event.preventDefault();}",
                              style="padding:0.3rem 0.5rem;border:1px solid #e2e8f0;border-radius:6px;font-size:0.75rem;width:180px;"),
                        Button("Find", onclick="searchInDoc()", cls="module-action-btn", style="padding:0.3rem 0.5rem;font-size:0.75rem;"),
                        Button("X", onclick="closeDocViewer()", cls="header-btn"),
                        style="display:flex;gap:0.4rem;align-items:center;",
                    ),
                    cls="doc-viewer-header",
                ),
                Iframe(id="doc-viewer-frame", src="about:blank", cls="doc-viewer-iframe"),
                id="doc-viewer-pane",
                cls="doc-viewer-pane",
            ),
            Script("""
                function openDocViewer(filename, searchText) {
                    var pane = document.getElementById('doc-viewer-pane');
                    var frame = document.getElementById('doc-viewer-frame');
                    var nameEl = document.getElementById('doc-viewer-filename');
                    if (!pane || !frame) return;

                    var pdfUrl = '/doc-pdf?name=' + encodeURIComponent(filename);
                    if (searchText) {
                        // Use PDF.js viewer with search highlighting
                        var fullPdfUrl = window.location.origin + pdfUrl;
                        var viewerUrl = 'https://mozilla.github.io/pdf.js/web/viewer.html'
                            + '?file=' + encodeURIComponent(fullPdfUrl)
                            + '#search=' + encodeURIComponent(searchText.substring(0, 80))
                            + '&phrase=true';
                        frame.src = viewerUrl;
                    } else {
                        // Direct PDF embed (browser native)
                        frame.src = pdfUrl;
                    }

                    if (nameEl) nameEl.textContent = filename;
                    pane.classList.add('open');
                }

                function closeDocViewer() {
                    var pane = document.getElementById('doc-viewer-pane');
                    var frame = document.getElementById('doc-viewer-frame');
                    if (pane) pane.classList.remove('open');
                    if (frame) frame.src = 'about:blank';
                }

                function searchInDoc() {
                    var input = document.getElementById('doc-search-input');
                    var nameEl = document.getElementById('doc-viewer-filename');
                    if (!input || !input.value.trim()) return;
                    var filename = nameEl ? nameEl.textContent : '';
                    if (filename) openDocViewer(filename, input.value.trim());
                }

                function highlightInDoc(filename, searchText) {
                    openDocViewer(filename, searchText);
                }
            """),
            cls="module-content",
        )
