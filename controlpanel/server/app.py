from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import RestrictedPython

app = FastAPI()

ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT / "static"
UPLOAD_DIR = ROOT / "uploaded_scripts"
UPLOAD_DIR.mkdir(exist_ok=True)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def analyze_python_code(code: str) -> tuple[bool, str | None]:
    try:
        RestrictedPython.compile_restricted(code, mode="exec")
        return True, None
    except SyntaxError as e:
        return False, f"Syntax Error{"s" if len(e.msg) > 1 else ""}:\n{"\n".join(e.msg)}"


def render_page(message: str = "", message_class: str = "") -> str:
    message = message.replace("\n", "<br>")
    return """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>PY UPLOAD</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>

<div class="crt-overlay"></div>

<div class="container">
    <h1>PY UPLOAD</h1>

    <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">

        <label class="upload-btn">
            SELECT .PY FILE
            <input type="file" id="fileInput" name="file" accept=".py">
        </label>

        <div class="filename-display" id="filenameDisplay">No file selected</div>

        <div id="addonRow" class="addon-row hidden">
            <label class="left-label">Addon name:</label>
            <input type="text" id="filenameField" name="filename" class="filename-input">
        </div>

        <button id="submitBtn" class="submit-btn disabled" type="submit" disabled>UPLOAD</button>
    </form>

    <!-- message goes here -->
    <div id="msgContainer" class="msg """ + message_class + """">""" + message + """</div>

</div>

<script>
    const fileInput = document.getElementById("fileInput");
    const fileDisplay = document.getElementById("filenameDisplay");
    const addonRow = document.getElementById("addonRow");
    const nameField = document.getElementById("filenameField");
    const submitBtn = document.getElementById("submitBtn");

    function updateState() {
        const hasFile = fileInput.files.length > 0;
        const hasName = nameField.value.trim().length > 0;

        if (hasFile) {
            addonRow.classList.remove("hidden");
        } else {
            addonRow.classList.add("hidden");
        }

        submitBtn.disabled = !(hasFile && hasName);

        if (submitBtn.disabled) {
            submitBtn.classList.add("disabled");
        } else {
            submitBtn.classList.remove("disabled");
        }
    }

    // When selecting a file → update filename + nameField automatically
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            let name = fileInput.files[0].name;

            fileDisplay.textContent = name;

            if (name.toLowerCase().endsWith(".py")) {
                name = name.slice(0, -3);
            }

            nameField.value = name;
        } else {
            fileDisplay.textContent = "No file selected";
            nameField.value = "";
        }

        updateState();
    });

    nameField.addEventListener("input", updateState);

    // After a message was displayed → reset fields on load
    window.addEventListener("load", () => {
        const msg = document.getElementById("msgContainer").textContent.trim();
        if (msg.length > 0) {
            fileInput.value = "";
            fileDisplay.textContent = "No file selected";
            nameField.value = "";
            addonRow.classList.add("hidden");
            updateState();
        }
    });
</script>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    msg = request.cookies.get("upload_msg", "")
    cls = request.cookies.get("upload_class", "")
    html = render_page(message=msg, message_class=cls)

    response = HTMLResponse(html)

    if msg:
        response.delete_cookie("upload_msg")
        response.delete_cookie("upload_class")

    return response


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    filename: str = Form(...)
):
    base = Path(filename).stem
    final_name = base + ".py"

    raw_bytes = await file.read()
    code = raw_bytes.decode("utf-8", errors="replace")

    ok, status_message = analyze_python_code(code)
    response = RedirectResponse("/", status_code=303)

    if ok:
        (UPLOAD_DIR / final_name).write_bytes(raw_bytes)
        response.set_cookie("upload_msg", f"Saved as {final_name}", max_age=5)
        response.set_cookie("upload_class", "success", max_age=5)
    else:
        response.set_cookie("upload_msg", status_message, max_age=5)
        response.set_cookie("upload_class", "error", max_age=5)

    return response
