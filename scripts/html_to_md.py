from readability import Document
import requests, html2text

def fetch_full_html(url: str) -> str:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text

def extract_main_html(html: str) -> str:
    doc = Document(html)
    return doc.summary(html_partial=True)

def html_to_markdown(html: str) -> str:
    h = html2text.HTML2Text()
    h.body_width = 0
    h.ignore_links = False
    h.ignore_images = False
    h.protect_links = True
    return h.handle(html).strip()
