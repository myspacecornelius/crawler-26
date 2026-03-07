"""
CRAWL — PDF Bio Parser

Downloads and parses PDF files linked from team pages to extract
contact information (names, roles, emails) from partner bios
and annual reports.

Uses pdfplumber for text extraction with fallback to PyPDF2.

Usage:
    from enrichment.pdf_parser import PDFParser
    parser = PDFParser()
    contacts = await parser.parse_linked_pdfs(page, fund_url, fund_name)
"""

import asyncio
import logging
import os
import re
import tempfile
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp

logger = logging.getLogger(__name__)

# Common file patterns for team/bio PDFs
BIO_PDF_PATTERNS = re.compile(
    r'(team|bio|profile|partner|annual|report|directory|leadership)',
    re.IGNORECASE,
)


class PDFParser:
    """Parse PDF documents linked from fund websites for contact data."""

    def __init__(self, max_pdfs: int = 5, max_size_mb: int = 10):
        self.max_pdfs = max_pdfs
        self.max_size = max_size_mb * 1024 * 1024

    async def find_pdf_links(
        self, page_html: str, base_url: str
    ) -> List[str]:
        """Find PDF links on a page that likely contain team/bio info."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(page_html, "html.parser")
        pdf_urls = []
        base_netloc = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.lower().endswith(".pdf"):
                continue

            full_url = urljoin(base_url, href)

            # Only internal PDFs
            if urlparse(full_url).netloc != base_netloc:
                continue

            # Check if the link text or URL suggests a bio/team PDF
            link_text = a.get_text(strip=True).lower()
            url_lower = full_url.lower()

            if BIO_PDF_PATTERNS.search(link_text) or BIO_PDF_PATTERNS.search(url_lower):
                pdf_urls.append(full_url)

        return pdf_urls[:self.max_pdfs]

    async def download_and_parse(
        self, session: aiohttp.ClientSession, pdf_url: str
    ) -> Optional[str]:
        """Download a PDF and extract text content."""
        try:
            async with session.get(
                pdf_url,
                timeout=aiohttp.ClientTimeout(total=20),
                headers={"User-Agent": "Mozilla/5.0"},
            ) as resp:
                if resp.status != 200:
                    return None
                content_length = int(resp.headers.get("Content-Length", 0))
                if content_length > self.max_size:
                    logger.debug(f"  PDF too large ({content_length} bytes): {pdf_url}")
                    return None

                data = await resp.read()
                if len(data) > self.max_size:
                    return None

                return self._extract_text(data)
        except Exception as e:
            logger.debug(f"  PDF download error ({pdf_url}): {e}")
            return None

    def _extract_text(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text from PDF bytes. Tries pdfplumber first, then PyPDF2."""
        # Try pdfplumber
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                pages_text = []
                for page in pdf.pages[:20]:  # Cap at 20 pages
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                return "\n".join(pages_text) if pages_text else None
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback to PyPDF2
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(pdf_bytes))
            pages_text = []
            for page in reader.pages[:20]:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            return "\n".join(pages_text) if pages_text else None
        except ImportError:
            logger.warning("  ⚠️  Neither pdfplumber nor PyPDF2 installed — PDF parsing unavailable")
            return None
        except Exception:
            return None

    def extract_contacts_from_text(
        self, text: str, fund_name: str
    ) -> List[dict]:
        """Extract name-role-email triples from PDF text."""
        contacts = []

        # Extract emails
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)

        # Extract name-role pairs using common patterns
        # Pattern: "Name\nTitle" or "Name, Title" or "Name — Title"
        lines = text.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) > 80:
                continue

            # Check if this looks like a name (2-4 capitalized words)
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                # Check next line for role
                role = ""
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    role_keywords = [
                        "partner", "director", "associate", "analyst",
                        "principal", "vice president", "vp", "managing",
                        "founder", "ceo", "cto", "head", "chief",
                    ]
                    if any(kw in next_line.lower() for kw in role_keywords):
                        role = next_line

                if role:  # Only add if we found a role (avoid false positives)
                    contacts.append({
                        "name": line,
                        "role": role,
                        "fund": fund_name,
                    })

        # Try to match emails to contacts
        for contact in contacts:
            name_lower = contact["name"].lower().replace(" ", "")
            for email in emails:
                local = email.split("@")[0].lower()
                if name_lower[:4] in local:
                    contact["email"] = email
                    break

        return contacts

    async def parse_linked_pdfs(
        self, page_html: str, base_url: str, fund_name: str
    ) -> List[dict]:
        """Full pipeline: find PDF links → download → parse → extract contacts."""
        pdf_urls = await self.find_pdf_links(page_html, base_url)
        if not pdf_urls:
            return []

        logger.info(f"  📄 Found {len(pdf_urls)} bio PDFs on {base_url}")
        all_contacts = []

        async with aiohttp.ClientSession() as session:
            for url in pdf_urls:
                text = await self.download_and_parse(session, url)
                if text:
                    contacts = self.extract_contacts_from_text(text, fund_name)
                    all_contacts.extend(contacts)
                    if contacts:
                        logger.info(f"  📄 PDF: {len(contacts)} contacts from {url}")

        return all_contacts
