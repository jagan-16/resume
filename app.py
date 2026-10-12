#!/usr/bin/env python3
"""
Resume Builder – Streamlit UI
==============================
A front-end for the existing Node.js resume generator (generate.js +
template.hbs + styles.css). This app lets you build/edit the resume JSON
through a form, saves it to resumes/<name>.json, then shells out to
`node generate.js <name>` to produce output/<name>.html (+ .pdf if
Puppeteer/Chrome is available), and lets you preview/download the result.

SETUP
-----
1. Drop this file (app.py) into the SAME directory as generate.js,
   template.hbs, styles.css, and the resumes/ folder.
2. pip install streamlit
3. streamlit run app.py

The Node side (generate.js, npm install for handlebars / puppeteer) must
already be set up — this UI only edits JSON and invokes that script.

STATE
-----
Every edit is autosaved to disk as you type, and the app remembers which
resume you had open (in a small local marker file) so a browser refresh
reloads your last state instead of resetting to a blank form.
"""

import json
import subprocess
from pathlib import Path

import streamlit as st

# ─── Paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
RESUMES_DIR = ROOT / "resumes"
OUTPUT_DIR = ROOT / "output"
GENERATE_SCRIPT = ROOT / "generate.js"
LAST_OPEN_MARKER = ROOT / ".resume_builder_last_open"

RESUMES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Resume Builder", page_icon="📄", layout="wide")

# ─── Data model ──────────────────────────────────────────────────────────
DEFAULT_DATA = {
    "name": "",
    "contact": {"phone": "", "email": "", "linkedin": "", "github": "", "portfolio": ""},
    "summary": "",
    "education": [],
    "skills": [],
    "experience": [],
    "projects": [],
    "achievements": [],
    "certifications": [],
    "additionalInfo": {"languages": [], "volunteer": [], "interests": []},
}


def new_state():
    return json.loads(json.dumps(DEFAULT_DATA))


def list_saved_resumes():
    return sorted(p.stem for p in RESUMES_DIR.glob("*.json"))


def read_resume_file(slug: str):
    path = RESUMES_DIR / f"{slug}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    merged = new_state()
    for k, v in loaded.items():
        merged[k] = v
    return merged


def slugify(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in name).strip("-") or "resume"


def remember_last_open(slug: str):
    LAST_OPEN_MARKER.write_text(slug, encoding="utf-8")


def forget_last_open():
    if LAST_OPEN_MARKER.exists():
        LAST_OPEN_MARKER.unlink()


def persist_current(slug: str, data: dict):
    """Autosave the current form state to disk so a refresh can recover it."""
    if not slug:
        return
    path = RESUMES_DIR / f"{slug}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    remember_last_open(slug)


# ─── First load: recover state from disk instead of starting blank ────────
if "data" not in st.session_state:
    recovered_slug = LAST_OPEN_MARKER.read_text(encoding="utf-8").strip() if LAST_OPEN_MARKER.exists() else ""
    recovered_data = read_resume_file(recovered_slug) if recovered_slug else None
    if recovered_data is not None:
        st.session_state.data = recovered_data
        st.session_state.slug = recovered_slug
    else:
        st.session_state.data = new_state()
        st.session_state.slug = ""

# ─── Sidebar: load / new / rename ──────────────────────────────────────────
with st.sidebar:
    st.header("📁 Resumes")

    existing = list_saved_resumes()
    choice = st.selectbox("Load existing", ["— new resume —"] + existing)
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Load", use_container_width=True, disabled=(choice == "— new resume —")):
            st.session_state.data = read_resume_file(choice) or new_state()
            st.session_state.slug = choice
            remember_last_open(choice)
            st.rerun()
    with col_b:
        if st.button("New", use_container_width=True):
            st.session_state.data = new_state()
            st.session_state.slug = ""
            forget_last_open()
            st.rerun()

    st.divider()
    slug_input = st.text_input(
        "Resume name",
        value=st.session_state.slug or slugify(st.session_state.data.get("name") or ""),
        help="Used to name this resume's saved and exported files.",
    )

    st.divider()
    generate_clicked = st.button("⚙️ Generate Resume", use_container_width=True)


data = st.session_state.data

st.title("📄 Resume Builder")
st.caption("Your edits are saved automatically as you go.")

tabs = st.tabs(
    [
        "Basics",
        "Education",
        "Skills",
        "Experience",
        "Projects",
        "Achievements",
        "Certifications",
        "Additional Info",
        "Generate & Preview",
    ]
)

# ─── Basics ──────────────────────────────────────────────────────────────
with tabs[0]:
    st.subheader("Name & Contact")
    data["name"] = st.text_input("Full name", data.get("name", ""))
    c1, c2, c3 = st.columns(3)
    with c1:
        data["contact"]["phone"] = st.text_input("Phone", data["contact"].get("phone", ""))
        data["contact"]["email"] = st.text_input("Email", data["contact"].get("email", ""))
    with c2:
        data["contact"]["linkedin"] = st.text_input("LinkedIn", data["contact"].get("linkedin", ""))
        data["contact"]["github"] = st.text_input("GitHub", data["contact"].get("github", ""))
    with c3:
        data["contact"]["portfolio"] = st.text_input("Portfolio", data["contact"].get("portfolio", ""))

    st.subheader("Summary")
    data["summary"] = st.text_area("Professional summary", data.get("summary", ""), height=100)

# ─── Education ───────────────────────────────────────────────────────────
with tabs[1]:
    st.subheader("Education")
    for i, edu in enumerate(data["education"]):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            edu["degree"] = c1.text_input("Degree", edu.get("degree", ""), key=f"edu_degree_{i}")
            edu["date"] = c2.text_input("Date", edu.get("date", ""), key=f"edu_date_{i}")
            edu["institution"] = st.text_input("Institution", edu.get("institution", ""), key=f"edu_inst_{i}")
            edu["cgpa"] = st.text_input("CGPA / Grade", edu.get("cgpa", ""), key=f"edu_cgpa_{i}")
            if st.button("🗑️ Remove", key=f"edu_remove_{i}"):
                data["education"].pop(i)
                st.rerun()
    if st.button("➕ Add education"):
        data["education"].append({"degree": "", "date": "", "institution": "", "cgpa": ""})
        st.rerun()

# ─── Skills ──────────────────────────────────────────────────────────────
with tabs[2]:
    st.subheader("Technical Skills")
    for i, sk in enumerate(data["skills"]):
        with st.container(border=True):
            sk["category"] = st.text_input("Category", sk.get("category", ""), key=f"sk_cat_{i}")
            items_str = st.text_input(
                "Items (comma separated)",
                ", ".join(sk.get("items", [])),
                key=f"sk_items_{i}",
            )
            sk["items"] = [x.strip() for x in items_str.split(",") if x.strip()]
            if st.button("🗑️ Remove", key=f"sk_remove_{i}"):
                data["skills"].pop(i)
                st.rerun()
    if st.button("➕ Add skill category"):
        data["skills"].append({"category": "", "items": []})
        st.rerun()

# ─── Experience ──────────────────────────────────────────────────────────
with tabs[3]:
    st.subheader("Internship / Work Experience")
    for i, exp in enumerate(data["experience"]):
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            exp["company"] = c1.text_input("Company", exp.get("company", ""), key=f"exp_company_{i}")
            exp["role"] = c2.text_input("Role", exp.get("role", ""), key=f"exp_role_{i}")
            exp["date"] = c3.text_input("Date", exp.get("date", ""), key=f"exp_date_{i}")
            points_str = st.text_area(
                "Bullet points (one per line)",
                "\n".join(exp.get("points", [])),
                key=f"exp_points_{i}",
                height=100,
            )
            exp["points"] = [x.strip() for x in points_str.split("\n") if x.strip()]
            if st.button("🗑️ Remove", key=f"exp_remove_{i}"):
                data["experience"].pop(i)
                st.rerun()
    if st.button("➕ Add experience"):
        data["experience"].append({"company": "", "role": "", "date": "", "points": []})
        st.rerun()

# ─── Projects ────────────────────────────────────────────────────────────
with tabs[4]:
    st.subheader("Projects")
    for i, proj in enumerate(data["projects"]):
        with st.container(border=True):
            proj["name"] = st.text_input("Project name", proj.get("name", ""), key=f"proj_name_{i}")
            tech_str = st.text_input(
                "Tech stack (comma separated)",
                ", ".join(proj.get("tech", [])),
                key=f"proj_tech_{i}",
            )
            proj["tech"] = [x.strip() for x in tech_str.split(",") if x.strip()]
            points_str = st.text_area(
                "Bullet points (one per line)",
                "\n".join(proj.get("points", [])),
                key=f"proj_points_{i}",
                height=100,
            )
            proj["points"] = [x.strip() for x in points_str.split("\n") if x.strip()]
            if st.button("🗑️ Remove", key=f"proj_remove_{i}"):
                data["projects"].pop(i)
                st.rerun()
    if st.button("➕ Add project"):
        data["projects"].append({"name": "", "tech": [], "points": []})
        st.rerun()

# ─── Achievements ────────────────────────────────────────────────────────
with tabs[5]:
    st.subheader("Achievements")
    for i, ach in enumerate(data["achievements"]):
        with st.container(border=True):
            ach["title"] = st.text_input("Title", ach.get("title", ""), key=f"ach_title_{i}")
            points_str = st.text_area(
                "Details (one per line, optional)",
                "\n".join(ach.get("points", [])),
                key=f"ach_points_{i}",
                height=80,
            )
            ach["points"] = [x.strip() for x in points_str.split("\n") if x.strip()]
            if st.button("🗑️ Remove", key=f"ach_remove_{i}"):
                data["achievements"].pop(i)
                st.rerun()
    if st.button("➕ Add achievement"):
        data["achievements"].append({"title": "", "points": []})
        st.rerun()

# ─── Certifications ──────────────────────────────────────────────────────
with tabs[6]:
    st.subheader("Certifications")
    certs_str = st.text_area(
        "One certification per line",
        "\n".join(data.get("certifications", [])),
        height=120,
    )
    data["certifications"] = [x.strip() for x in certs_str.split("\n") if x.strip()]

# ─── Additional Info ─────────────────────────────────────────────────────
with tabs[7]:
    st.subheader("Additional Information")
    lang_str = st.text_input(
        "Languages (comma separated)",
        ", ".join(data["additionalInfo"].get("languages", [])),
    )
    data["additionalInfo"]["languages"] = [x.strip() for x in lang_str.split(",") if x.strip()]

    vol_str = st.text_area(
        "Volunteer experience (comma separated)",
        ", ".join(data["additionalInfo"].get("volunteer", [])),
    )
    data["additionalInfo"]["volunteer"] = [x.strip() for x in vol_str.split(",") if x.strip()]

    interests_str = st.text_input(
        "Interests (comma separated)",
        ", ".join(data["additionalInfo"].get("interests", [])),
    )
    data["additionalInfo"]["interests"] = [x.strip() for x in interests_str.split(",") if x.strip()]

# ─── Generate & Preview ──────────────────────────────────────────────────
with tabs[8]:
    st.subheader("Generate & Preview")

    if not GENERATE_SCRIPT.exists():
        st.error("generate.js not found next to app.py. Place this file in the same folder as your generator.")

    slug = slug_input or slugify(data.get("name") or "")
    st.write(f"Current resume: **{slug or '(unnamed)'}**")

    if generate_clicked:
        st.session_state.slug = slug
        persist_current(slug, data)

        with st.spinner("Generating your resume..."):
            try:
                result = subprocess.run(
                    ["node", str(GENERATE_SCRIPT), slug],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    st.success("Generation finished.")
                else:
                    st.error("Something went wrong while generating.")
                if result.stdout:
                    st.code(result.stdout, language="bash")
                if result.stderr:
                    st.code(result.stderr, language="bash")
            except FileNotFoundError:
                st.error("Node.js not found. Install Node.js to generate resumes.")
            except subprocess.TimeoutExpired:
                st.error("Generation timed out after 120s.")

    html_path = OUTPUT_DIR / f"{slug}.html"
    pdf_path = OUTPUT_DIR / f"{slug}.pdf"

    col1, col2 = st.columns(2)
    with col1:
        if html_path.exists():
            st.download_button(
                "⬇️ Download HTML",
                data=html_path.read_bytes(),
                file_name=html_path.name,
                mime="text/html",
                use_container_width=True,
            )
        else:
            st.info("No HTML output yet — click Generate Resume in the sidebar.")
    with col2:
        if pdf_path.exists():
            st.download_button(
                "⬇️ Download PDF",
                data=pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.info("No PDF output (needs Chrome/Chromium on the generator side).")

    if html_path.exists():
        st.divider()
        st.subheader("Live Preview")
        st.components.v1.html(html_path.read_text(encoding="utf-8"), height=900, scrolling=True)

# ─── Autosave every rerun so a refresh can recover this exact state ───────
persist_current(slug_input or slugify(data.get("name") or ""), data)
