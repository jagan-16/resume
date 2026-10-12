# Resume Builder

Dynamic, ATS-friendly resume generator using **Handlebars** for templating and **Puppeteer** for PDF export. Preserves the exact visual structure, print layout, and ATS compatibility of the original HTML resume.

---

## Folder Structure

```
resume-builder/
├── generate.js       ← Main CLI entry point
├── template.hbs      ← Handlebars template (do NOT hardcode data here)
├── styles.css        ← Extracted CSS (single source of truth)
├── package.json
├── README.md
│
├── resumes/          ← One JSON file per person
│   ├── jagan.json
│   ├── sample.json
│   └── yourname.json
│
└── output/           ← Auto-generated; do not edit manually
    ├── jagan.html
    ├── jagan.pdf
    └── ...
```

---

## Setup

### 1. Install Node dependencies
```bash
npm install
```

### 2. Install Chromium (for PDF export)
```bash
# Ubuntu / Debian
sudo apt-get install -y chromium-browser

# macOS (Homebrew)
brew install --cask chromium

# Or set CHROME_PATH to your existing Chrome installation
export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

> **PDF export is optional.** If Chromium is not found, the generator still produces a fully functional HTML file.

---

## Usage

```bash
# Generate Jagan's resume
node generate.js jagan

# Generate the sample resume
node generate.js sample

# Generate any resume (just drop a JSON in resumes/)
node generate.js yourname

# Using npm scripts
npm run jagan
npm run sample
```

### Output
```
✅  HTML generated: output/jagan.html
✅  PDF generated:  output/jagan.pdf
```

---

## Adding a New Resume

1. Copy `resumes/sample.json` → `resumes/yourname.json`
2. Fill in your data (see schema below)
3. Run `node generate.js yourname`

---

## JSON Schema

```jsonc
{
  "name": "Full Name",                    // Required
  "contact": {
    "phone": "+91 ...",
    "email": "you@email.com",
    "linkedin": "linkedin.com/in/...",
    "github": "github.com/...",           // Optional – leave "" to hide
    "portfolio": ""                       // Optional – leave "" to hide
  },
  "summary": "One paragraph summary...", // Optional – omit section if empty

  "education": [                          // Array – supports multiple degrees
    {
      "degree": "B.E. Computer Science",
      "institution": "University Name",
      "date": "Oct 2022 - Jul 2026",
      "cgpa": "8.0"                       // or "gpa", "grade" – any one
    }
  ],

  "skills": [                             // Array of skill categories
    {
      "category": "Programming Languages",
      "items": ["Java", "Python"]
    }
  ],

  "experience": [                         // Internships / work experience
    {
      "company": "Company Name",
      "role": "Role Title",
      "date": "May 2025 – Jun 2025",
      "points": ["Bullet 1", "Bullet 2"]
    }
  ],

  "projects": [
    {
      "name": "Project Name",
      "tech": ["Java", "Spring Boot"],    // Shown in parentheses
      "points": ["Bullet 1"]
    }
  ],

  "achievements": [
    {
      "title": "Achievement Title",
      "points": ["Sub-bullet"]            // Optional nested bullets
    }
  ],

  "certifications": [                     // Plain strings
    "Certification Name (Issuer)."
  ],

  "additionalInfo": {
    "languages": ["English (Intermediate)", "Tamil (Native)"],
    "volunteer": ["NSS", "YRC"],
    "interests": []                       // Leave empty array to hide
  }
}
```

---

## Handlebars Helpers

| Helper | Usage | Description |
|--------|-------|-------------|
| `join` | `{{join items ", "}}` | Joins an array into a string |
| `if_any` | `{{#if_any a b}}` | Renders if any arg is truthy |
| `unless_empty` | `{{#unless_empty arr}}` | Renders if array has items |
| `formatDate` | `{{formatDate "2025-05" "MMM YYYY"}}` | Formats ISO date string |

---

## ATS Notes

- All text is selectable (no canvas/image rendering)
- Semantic HTML tags: `h1`, `h2`, `h3`, `ul`, `li`, `p`
- Proper heading hierarchy maintained
- PDF is text-based (not a screenshot)
- No JavaScript in output HTML – pure static markup
- Print margins preserved via `@media print` CSS

---

## PDF Troubleshooting

| Issue | Fix |
|-------|-----|
| Chrome not found | Install `chromium-browser` or set `CHROME_PATH` |
| PDF layout broken | Ensure `styles.css` has not been modified |
| Sandbox error in CI | Add `--no-sandbox` (already in generate.js) |
| Content cut off | Reduce content or adjust `@page margin` in styles.css |