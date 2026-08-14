from flask import Flask, request, redirect, url_for, render_template_string
from pathlib import Path
import os
import shutil
import uuid
import json
import string
from datetime import datetime

# ============================================================
# DIGITAL FORENSIC FILE RECOVERY SYSTEM
# Multi-source version
# Everything is contained in this single Python file.
# ============================================================

app = Flask(__name__)

# ============================================================
# APPLICATION DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

RECOVERY_DIR = BASE_DIR / "recovery_vault"
METADATA_FILE = RECOVERY_DIR / "metadata.json"

RECOVERY_DIR.mkdir(exist_ok=True)


# ============================================================
# COMMON WINDOWS SOURCES
# ============================================================

HOME = Path.home()

SOURCES = {
    "Desktop": HOME / "Desktop",
    "Downloads": HOME / "Downloads",
    "Documents": HOME / "Documents",
    "Pictures": HOME / "Pictures",
    "Videos": HOME / "Videos",
    "Music": HOME / "Music",
}

# Add OneDrive if it exists
ONEDRIVE = HOME / "OneDrive"

if ONEDRIVE.exists():
    SOURCES["OneDrive"] = ONEDRIVE


# ============================================================
# METADATA FUNCTIONS
# ============================================================

def load_metadata():

    if not METADATA_FILE.exists():
        return {}

    try:

        with open(
            METADATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, dict):
                return data

    except Exception:
        pass

    return {}


def save_metadata(data):

    temporary = METADATA_FILE.with_suffix(".tmp")

    with open(
        temporary,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )

    temporary.replace(METADATA_FILE)


# ============================================================
# SAFE PATH FUNCTION
# ============================================================

def is_inside(child, parent):

    try:

        child.resolve().relative_to(
            parent.resolve()
        )

        return True

    except ValueError:

        return False


# ============================================================
# GET SOURCE FILES
# ============================================================

def scan_source(source_name):

    if source_name not in SOURCES:
        return []

    root = SOURCES[source_name]

    if not root.exists():
        return []

    files = []

    try:

        for current_root, directories, filenames in os.walk(
            root,
            topdown=True
        ):

            # Ignore the application recovery vault
            directories[:] = [
                directory
                for directory in directories
                if directory != "recovery_vault"
            ]

            for filename in filenames:

                full_path = Path(current_root) / filename

                try:

                    if full_path.is_file():

                        relative_path = full_path.relative_to(root)

                        size = full_path.stat().st_size

                        files.append({
                            "name": filename,
                            "relative": str(relative_path),
                            "size": size,
                            "location": source_name
                        })

                except (
                    PermissionError,
                    FileNotFoundError,
                    OSError
                ):

                    continue

    except (
        PermissionError,
        FileNotFoundError,
        OSError
    ):

        pass

    return files


# ============================================================
# HUMAN READABLE FILE SIZE
# ============================================================

def format_size(size):

    try:

        size = float(size)

    except Exception:

        return "Unknown"


    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ]

    for unit in units:

        if size < 1024:

            if unit == "B":
                return f"{int(size)} B"

            return f"{size:.1f} {unit}"

        size /= 1024

    return f"{size:.1f} PB"


# ============================================================
# ALL SOURCES
# ============================================================

def get_all_files(selected_source):

    if selected_source == "ALL":

        combined = []

        for source_name in SOURCES:

            files = scan_source(source_name)

            combined.extend(files)

        return combined

    return scan_source(selected_source)


# ============================================================
# HTML
# ============================================================

HTML = """

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Forensic Recovery</title>


<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}


body {

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;

    background: #f6f7f9;

    color: #202124;

    min-height: 100vh;
}


/* ============================================================
   HEADER
============================================================ */

.header {

    height: 68px;

    background: white;

    border-bottom: 1px solid #e5e7eb;

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 0 6%;
}


.brand {

    display: flex;

    align-items: center;

    gap: 11px;
}


.logo {

    width: 38px;

    height: 38px;

    background: #111827;

    color: white;

    border-radius: 9px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 17px;
}


.brand-name {

    font-size: 16px;

    font-weight: 600;
}


.brand-subtitle {

    color: #9ca3af;

    font-size: 11px;

    margin-top: 2px;
}


.online {

    color: #16a34a;

    font-size: 12px;
}


/* ============================================================
   CONTAINER
============================================================ */

.container {

    width: 90%;

    max-width: 1250px;

    margin: 35px auto;
}


/* ============================================================
   HERO
============================================================ */

.hero {

    margin-bottom: 25px;
}


.hero h1 {

    font-size: 30px;

    font-weight: 600;

    margin-bottom: 7px;
}


.hero p {

    color: #6b7280;

    font-size: 14px;
}


/* ============================================================
   WARNING
============================================================ */

.warning {

    background: #fff7ed;

    border: 1px solid #fed7aa;

    color: #c2410c;

    padding: 13px 16px;

    border-radius: 9px;

    font-size: 12px;

    margin-bottom: 20px;
}


/* ============================================================
   SOURCE BAR
============================================================ */

.source-card {

    background: white;

    border: 1px solid #e5e7eb;

    border-radius: 11px;

    padding: 18px;

    margin-bottom: 20px;
}


.source-title {

    font-size: 13px;

    font-weight: 600;

    margin-bottom: 12px;
}


.source-form {

    display: flex;

    gap: 10px;

    flex-wrap: wrap;
}


select {

    flex: 1;

    min-width: 200px;

    border: 1px solid #d1d5db;

    background: #fafafa;

    border-radius: 7px;

    padding: 9px;

    font-size: 12px;
}


.scan-button {

    background: #111827;

    color: white;

    border: none;

    border-radius: 7px;

    padding: 0 18px;

    height: 38px;

    cursor: pointer;

    font-size: 12px;
}


.scan-button:hover {

    background: #374151;
}


/* ============================================================
   STATS
============================================================ */

.stats {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 14px;

    margin-bottom: 20px;
}


.stat {

    background: white;

    border: 1px solid #e5e7eb;

    border-radius: 10px;

    padding: 17px;
}


.stat-label {

    color: #6b7280;

    font-size: 11px;

    margin-bottom: 6px;
}


.stat-value {

    font-size: 23px;

    font-weight: 600;
}


.green {

    color: #16a34a;
}


/* ============================================================
   SECTION
============================================================ */

.section {

    background: white;

    border: 1px solid #e5e7eb;

    border-radius: 11px;

    overflow: hidden;

    margin-bottom: 22px;
}


.section-header {

    padding: 16px 19px;

    border-bottom: 1px solid #e5e7eb;

    display: flex;

    justify-content: space-between;

    align-items: center;
}


.section-title {

    font-size: 14px;

    font-weight: 600;
}


.badge {

    background: #f3f4f6;

    color: #6b7280;

    padding: 5px 10px;

    border-radius: 20px;

    font-size: 10px;
}


/* ============================================================
   TABLE
============================================================ */

.table-container {

    overflow-x: auto;
}


table {

    width: 100%;

    border-collapse: collapse;

    min-width: 850px;
}


th {

    text-align: left;

    padding: 11px 18px;

    background: #fafafa;

    border-bottom: 1px solid #e5e7eb;

    color: #6b7280;

    font-size: 10px;

    font-weight: 500;
}


td {

    padding: 13px 18px;

    border-bottom: 1px solid #f1f1f1;

    font-size: 12px;

    vertical-align: middle;
}


tr:last-child td {

    border-bottom: none;
}


tr:hover {

    background: #fafafa;
}


/* ============================================================
   FILE
============================================================ */

.file {

    display: flex;

    align-items: center;

    gap: 10px;
}


.file-icon {

    width: 31px;

    height: 31px;

    background: #f3f4f6;

    border-radius: 7px;

    display: flex;

    align-items: center;

    justify-content: center;
}


.file-name {

    font-weight: 500;
}


.location {

    color: #6b7280;

    font-size: 11px;
}


.status {

    color: #16a34a;

    font-size: 11px;
}


.recoverable {

    color: #d97706;

    font-size: 11px;
}


/* ============================================================
   BUTTONS
============================================================ */

.button {

    display: inline-block;

    text-decoration: none;

    border-radius: 6px;

    padding: 7px 10px;

    font-size: 10px;

    margin-right: 4px;
}


.delete {

    color: #dc2626;

    background: #fff1f2;

    border: 1px solid #fecdd3;
}


.delete:hover {

    background: #fee2e2;
}


.recover {

    color: #15803d;

    background: #f0fdf4;

    border: 1px solid #bbf7d0;
}


.recover:hover {

    background: #dcfce7;
}


.permanent {

    color: #4b5563;

    background: #f3f4f6;

    border: 1px solid #d1d5db;
}


.permanent:hover {

    background: #e5e7eb;
}


/* ============================================================
   EMPTY
============================================================ */

.empty {

    padding: 38px;

    text-align: center;

    color: #9ca3af;

    font-size: 12px;
}


/* ============================================================
   FOOTER
============================================================ */

.footer {

    text-align: center;

    color: #9ca3af;

    font-size: 10px;

    padding: 25px;
}


/* ============================================================
   RESPONSIVE
============================================================ */

@media(max-width: 700px) {

    .container {

        width: 94%;
    }

    .header {

        padding: 0 4%;
    }

    .online {

        display: none;
    }

    .stats {

        grid-template-columns: 1fr;
    }

    .hero h1 {

        font-size: 24px;
    }

}

</style>

</head>


<body>


<!-- ========================================================
     HEADER
========================================================= -->

<header class="header">

    <div class="brand">

        <div class="logo">
            🔐
        </div>

        <div>

            <div class="brand-name">
                File Recovery
            </div>

            <div class="brand-subtitle">
                Digital Forensic System
            </div>

        </div>

    </div>


    <div class="online">
        ● System Online
    </div>

</header>


<!-- ========================================================
     MAIN
========================================================= -->

<main class="container">


    <div class="hero">

        <h1>
            Digital Evidence Recovery
        </h1>

        <p>
            Scan multiple storage locations and manage recoverable evidence.
        </p>

    </div>


    <div class="warning">

        ⚠️
        <strong>Forensic workspace:</strong>
        Delete moves a file into the Recovery Vault.
        Recover restores it to its original location.
        Permanent Delete removes the vault copy.

    </div>


    <!-- ====================================================
         SOURCE SELECTOR
    ===================================================== -->

    <div class="source-card">

        <div class="source-title">
            Select Evidence Source
        </div>


        <form
            method="GET"
            action="/"
            class="source-form">


            <select name="source">

                <option
                    value="ALL"
                    {% if selected_source == "ALL" %}
                    selected
                    {% endif %}>

                    All Sources

                </option>


                {% for source_name in source_names %}

                <option
                    value="{{ source_name }}"
                    {% if selected_source == source_name %}
                    selected
                    {% endif %}>

                    {{ source_name }}

                </option>

                {% endfor %}

            </select>


            <button
                type="submit"
                class="scan-button">

                Scan Source

            </button>


        </form>

    </div>


    <!-- ====================================================
         STATS
    ===================================================== -->

    <div class="stats">


        <div class="stat">

            <div class="stat-label">
                Scanned Files
            </div>

            <div class="stat-value">
                {{ files|length }}
            </div>

        </div>


        <div class="stat">

            <div class="stat-label">
                Recovery Vault
            </div>

            <div class="stat-value">
                {{ recovery|length }}
            </div>

        </div>


        <div class="stat">

            <div class="stat-label">
                System
            </div>

            <div class="stat-value green">
                Operational
            </div>

        </div>


    </div>


    <!-- ====================================================
         SCANNED FILES
    ===================================================== -->

    <section class="section">


        <div class="section-header">

            <div class="section-title">
                Scanned Evidence
            </div>

            <div class="badge">
                {{ files|length }} files
            </div>

        </div>


        {% if files %}


        <div class="table-container">

        <table>

            <thead>

                <tr>

                    <th>
                        FILE
                    </th>

                    <th>
                        SOURCE
                    </th>

                    <th>
                        LOCATION
                    </th>

                    <th>
                        SIZE
                    </th>

                    <th>
                        STATUS
                    </th>

                    <th>
                        ACTION
                    </th>

                </tr>

            </thead>


            <tbody>


            {% for file in files %}


                <tr>


                    <td>

                        <div class="file">

                            <div class="file-icon">
                                📄
                            </div>

                            <div>

                                <div class="file-name">
                                    {{ file.name }}
                                </div>

                            </div>

                        </div>

                    </td>


                    <td>

                        {{ file.location }}

                    </td>


                    <td>

                        <span class="location">
                            {{ file.relative }}
                        </span>

                    </td>


                    <td>

                        {{ file.size }}

                    </td>


                    <td>

                        <span class="status">
                            ● Available
                        </span>

                    </td>


                    <td>


                        <form
                            method="POST"
                            action="/delete"
                            style="display:inline;">

                            <input
                                type="hidden"
                                name="source"
                                value="{{ file.location }}">


                            <input
                                type="hidden"
                                name="relative"
                                value="{{ file.relative }}">


                            <button
                                type="submit"
                                class="button delete"
                                onclick="return confirm('Move this REAL file to the Recovery Vault?');">

                                Delete

                            </button>

                        </form>


                    </td>


                </tr>


            {% endfor %}


            </tbody>

        </table>

        </div>


        {% else %}


        <div class="empty">

            No files found in this source.

        </div>


        {% endif %}


    </section>


    <!-- ====================================================
         RECOVERY VAULT
    ===================================================== -->

    <section class="section">


        <div class="section-header">

            <div class="section-title">
                Recovery Vault
            </div>

            <div class="badge">
                {{ recovery|length }} files
            </div>

        </div>


        {% if recovery %}


        <div class="table-container">

        <table>

            <thead>

                <tr>

                    <th>
                        FILE
                    </th>

                    <th>
                        ORIGINAL SOURCE
                    </th>

                    <th>
                        ORIGINAL LOCATION
                    </th>

                    <th>
                        DELETED AT
                    </th>

                    <th>
                        ACTION
                    </th>

                </tr>

            </thead>


            <tbody>


            {% for item in recovery %}


                <tr>


                    <td>

                        <div class="file">

                            <div class="file-icon">
                                🗑
                            </div>

                            <div class="file-name">
                                {{ item.name }}
                            </div>

                        </div>

                    </td>


                    <td>

                        {{ item.source }}

                    </td>


                    <td>

                        <span class="location">
                            {{ item.original_relative }}
                        </span>

                    </td>


                    <td>

                        {{ item.deleted_at }}

                    </td>


                    <td>


                        <form
                            method="POST"
                            action="/recover"
                            style="display:inline;">

                            <input
                                type="hidden"
                                name="id"
                                value="{{ item.id }}">


                            <button
                                type="submit"
                                class="button recover"
                                onclick="return confirm('Restore this file to its original location?');">

                                Recover

                            </button>

                        </form>


                        <form
                            method="POST"
                            action="/permanent_delete"
                            style="display:inline;">

                            <input
                                type="hidden"
                                name="id"
                                value="{{ item.id }}">


                            <button
                                type="submit"
                                class="button permanent"
                                onclick="return confirm('Permanently remove this recovery copy? This cannot be undone.');">

                                Permanent Delete

                            </button>

                        </form>


                    </td>


                </tr>


            {% endfor %}


            </tbody>

        </table>

        </div>


        {% else %}


        <div class="empty">

            No files are currently in the Recovery Vault.

        </div>


        {% endif %}


    </section>


</main>


<footer class="footer">

    Digital Forensic Recovery System
    ·
    Multi-Source Local Mode

</footer>


</body>

</html>

"""


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    selected_source = request.args.get(
        "source",
        "ALL"
    )

    if selected_source not in SOURCES and selected_source != "ALL":

        selected_source = "ALL"


    files = get_all_files(
        selected_source
    )


    # Convert file sizes
    # into readable format.

    for file in files:

        file["size"] = format_size(
            file["size"]
        )


    metadata = load_metadata()


    recovery = []

    for item_id, item in metadata.items():

        recovery.append({
            "id": item_id,
            **item
        })


    # Newest deleted first

    recovery.sort(
        key=lambda x: x.get(
            "deleted_at",
            ""
        ),
        reverse=True
    )


    return render_template_string(

        HTML,

        files=files,

        recovery=recovery,

        selected_source=selected_source,

        source_names=list(SOURCES.keys())

    )


# ============================================================
# DELETE FILE INTO RECOVERY VAULT
# ============================================================

@app.route(
    "/delete",
    methods=["POST"]
)
def delete_file():

    source_name = request.form.get(
        "source",
        ""
    )

    relative = request.form.get(
        "relative",
        ""
    )


    if source_name not in SOURCES:

        return redirect(
            url_for("home")
        )


    source_root = SOURCES[
        source_name
    ]


    original = (
        source_root /
        Path(relative)
    )


    # --------------------------------------------------------
    # SECURITY CHECK
    # --------------------------------------------------------

    if not is_inside(
        original,
        source_root
    ):

        return redirect(
            url_for("home")
        )


    if not original.is_file():

        return redirect(
            url_for("home")
        )


    # --------------------------------------------------------
    # CREATE UNIQUE RECOVERY ID
    # --------------------------------------------------------

    item_id = uuid.uuid4().hex


    recovery_filename = (
        item_id +
        "_" +
        original.name
    )


    recovery_path = (
        RECOVERY_DIR /
        recovery_filename
    )


    # --------------------------------------------------------
    # MOVE ACTUAL FILE
    # --------------------------------------------------------

    try:

        shutil.move(
            str(original),
            str(recovery_path)
        )

    except Exception as error:

        print(
            "Delete error:",
            error
        )

        return redirect(
            url_for("home")
        )


    # --------------------------------------------------------
    # SAVE ORIGINAL LOCATION
    # --------------------------------------------------------

    metadata = load_metadata()


    metadata[item_id] = {

        "name":
            original.name,

        "source":
            source_name,

        "original_relative":
            str(relative),

        "original_path":
            str(original),

        "vault_path":
            str(recovery_path),

        "deleted_at":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    }


    save_metadata(
        metadata
    )


    return redirect(
        url_for(
            "home",
            source=source_name
        )
    )


# ============================================================
# RECOVER FILE
# ============================================================

@app.route(
    "/recover",
    methods=["POST"]
)
def recover_file():

    item_id = request.form.get(
        "id",
        ""
    )


    metadata = load_metadata()


    if item_id not in metadata:

        return redirect(
            url_for("home")
        )


    item = metadata[item_id]


    vault_path = Path(
        item["vault_path"]
    )


    source_name = item["source"]


    if source_name not in SOURCES:

        return redirect(
            url_for("home")
        )


    source_root = SOURCES[
        source_name
    ]


    destination = (
        source_root /
        Path(
            item["original_relative"]
        )
    )


    # --------------------------------------------------------
    # SECURITY CHECK
    # --------------------------------------------------------

    if not is_inside(
        destination,
        source_root
    ):

        return redirect(
            url_for("home")
        )


    if not vault_path.is_file():

        metadata.pop(
            item_id,
            None
        )

        save_metadata(
            metadata
        )

        return redirect(
            url_for("home")
        )


    try:

        # Re-create original folder
        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        # If a file with same name exists,
        # don't overwrite it.

        if destination.exists():

            stem = destination.stem

            suffix = destination.suffix

            counter = 1


            new_destination = (
                destination.parent /
                f"{stem}_recovered{suffix}"
            )


            while new_destination.exists():

                new_destination = (
                    destination.parent /
                    f"{stem}_recovered_{counter}{suffix}"
                )

                counter += 1


            destination = new_destination


        shutil.move(
            str(vault_path),
            str(destination)
        )


        metadata.pop(
            item_id,
            None
        )


        save_metadata(
            metadata
        )


    except Exception as error:

        print(
            "Recovery error:",
            error
        )


    return redirect(
        url_for("home")
    )


# ============================================================
# PERMANENT DELETE FROM RECOVERY VAULT
# ============================================================

@app.route(
    "/permanent_delete",
    methods=["POST"]
)
def permanent_delete():

    item_id = request.form.get(
        "id",
        ""
    )


    metadata = load_metadata()


    if item_id not in metadata:

        return redirect(
            url_for("home")
        )


    item = metadata[item_id]


    vault_path = Path(
        item["vault_path"]
    )


    try:

        if vault_path.is_file():

            vault_path.unlink()


        metadata.pop(
            item_id,
            None
        )


        save_metadata(
            metadata
        )


    except Exception as error:

        print(
            "Permanent delete error:",
            error
        )


    return redirect(
        url_for("home")
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 65)
    print("          DIGITAL FORENSIC RECOVERY SYSTEM")
    print("=" * 65)
    print()

    print("Available sources:")

    for name, path in SOURCES.items():

        print(
            f"  {name}: {path}"
        )

    print()

    print("Recovery Vault:")
    print(RECOVERY_DIR)

    print()

    print("Open in browser:")
    print("http://127.0.0.1:5000")

    print()

    print("Press CTRL+C to stop.")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
