#!/usr/bin/env node
/**
 * Resume Builder – generate.js
 * Usage: node generate.js <resume-name>
 * Example: node generate.js jagan
 *
 * Reads:  resumes/<name>.json
 * Writes: output/<name>.html
 *         output/<name>.pdf  (if Chrome/Chromium is available)
 */

"use strict";

const fs   = require("fs");
const path = require("path");
const Handlebars = require("handlebars");

// ─── Paths ───────────────────────────────────────────────────────────────────
const ROOT      = __dirname;
const TEMPLATE  = path.join(ROOT, "template.hbs");
const STYLES    = path.join(ROOT, "styles.css");
const RESUMES   = path.join(ROOT, "resumes");
const OUTPUT    = path.join(ROOT, "output");

// ─── CLI arg ─────────────────────────────────────────────────────────────────
const arg = process.argv[2];
if (!arg) {
  console.error("❌  Usage: node generate.js <resume-name>");
  console.error("    Example: node generate.js jagan");
  process.exit(1);
}

const resumeName = arg.replace(/\.json$/i, ""); // strip extension if provided
const jsonPath   = path.join(RESUMES, `${resumeName}.json`);

if (!fs.existsSync(jsonPath)) {
  console.error(`❌  Resume file not found: ${jsonPath}`);
  process.exit(1);
}

// ─── Handlebars Helpers ───────────────────────────────────────────────────────

/**
 * {{join items ", "}}
 * Joins an array into a delimited string.
 */
Handlebars.registerHelper("join", function (arr, separator) {
  if (!Array.isArray(arr)) return "";
  return arr.join(typeof separator === "string" ? separator : ", ");
});

/**
 * {{#if_any a b c}}…{{/if_any}}
 * Renders block if ANY argument is truthy.
 */
Handlebars.registerHelper("if_any", function (...args) {
  const options = args.pop();
  return args.some(Boolean) ? options.fn(this) : options.inverse(this);
});

/**
 * {{#unless_empty arr}}…{{/unless_empty}}
 * Renders block if array is non-empty.
 */
Handlebars.registerHelper("unless_empty", function (arr, options) {
  if (Array.isArray(arr) && arr.length > 0) return options.fn(this);
  return options.inverse(this);
});

/**
 * {{formatDate "2025-05" "MMM YYYY"}}  →  "May 2025"
 * Simple date formatter for ISO date strings.
 */
Handlebars.registerHelper("formatDate", function (dateStr, format) {
  if (!dateStr) return "";
  const d = new Date(dateStr + "-01"); // ensure parseable
  if (isNaN(d)) return dateStr;       // return raw if unparseable
  const months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"];
  return `${months[d.getMonth()]} ${d.getFullYear()}`;
});

// ─── Load & Compile ───────────────────────────────────────────────────────────
const templateSrc = fs.readFileSync(TEMPLATE, "utf-8");
const compiledTpl  = Handlebars.compile(templateSrc);
const resumeData   = JSON.parse(fs.readFileSync(jsonPath, "utf-8"));
const inlineCSS    = fs.readFileSync(STYLES, "utf-8");

// Inject inline CSS so the HTML is fully self-contained (important for PDF)
const html = compiledTpl({ ...resumeData, inlineCSS });

// ─── Write HTML ───────────────────────────────────────────────────────────────
if (!fs.existsSync(OUTPUT)) fs.mkdirSync(OUTPUT, { recursive: true });

const htmlOut = path.join(OUTPUT, `${resumeName}.html`);
fs.writeFileSync(htmlOut, html, "utf-8");
console.log(`✅  HTML generated: ${htmlOut}`);

// ─── PDF Export ───────────────────────────────────────────────────────────────
(async () => {
  let puppeteer;
  try {
    puppeteer = require("puppeteer");
  } catch {
    console.warn("⚠️  Puppeteer not installed – skipping PDF export.");
    return;
  }

  // Resolve Chrome/Chromium executable
  const possiblePaths = [
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    process.env.CHROME_PATH,
  ].filter(Boolean);

  let executablePath = null;
  for (const p of possiblePaths) {
    if (fs.existsSync(p)) { executablePath = p; break; }
  }

  if (!executablePath) {
    console.warn("⚠️  Chrome/Chromium not found – skipping PDF export.");
    console.warn("    Install Chromium or set CHROME_PATH env variable.");
    console.warn(`    Your HTML is ready at: ${htmlOut}`);
    return;
  }

  console.log(`🖨️  Launching browser from: ${executablePath}`);

  let browser;
  try {
    browser = await puppeteer.launch({
      executablePath,
      headless: "new",
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
      ],
    });

    const page = await browser.newPage();

    // Load the generated HTML file directly (file:// protocol preserves assets)
    await page.goto(`file://${htmlOut}`, { waitUntil: "networkidle0" });

    const pdfOut = path.join(OUTPUT, `${resumeName}.pdf`);

    await page.pdf({
      path: pdfOut,
      format: "A4",
      printBackground: true,
      margin: { top: "0.3in", right: "0.3in", bottom: "0.3in", left: "0.3in" },
      // Selectable text – never canvas/screenshot based
      tagged: true,
    });

    console.log(`✅  PDF generated: ${pdfOut}`);
  } catch (err) {
    console.error("❌  PDF generation failed:", err.message);
  } finally {
    if (browser) await browser.close();
  }
})();
