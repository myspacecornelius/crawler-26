/**
 * Export the Honeypot landing page to PDF using Playwright.
 *
 * Usage:
 *   npx tsx scripts/export-pdf.ts          # uses http://localhost:3000
 *   npx tsx scripts/export-pdf.ts 3001     # custom port
 *
 * Requires: npm i -D playwright tsx
 * One-liner alternative:
 *   npx playwright pdf http://localhost:3000 public/honeypot-progress.pdf
 */

import { chromium } from "playwright";
import path from "path";

const PORT = process.argv[2] ?? "3000";
const URL = `http://localhost:${PORT}`;
const OUT = path.resolve(__dirname, "../public/honeypot-progress.pdf");

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  console.log(`Loading ${URL} …`);
  await page.goto(URL, { waitUntil: "networkidle" });

  // Let animations settle
  await page.waitForTimeout(1500);

  await page.pdf({
    path: OUT,
    format: "A4",
    printBackground: true,
    margin: { top: "16mm", bottom: "16mm", left: "12mm", right: "12mm" },
  });

  console.log(`PDF saved → ${OUT}`);
  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
