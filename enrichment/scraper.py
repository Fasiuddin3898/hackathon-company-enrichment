import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from rapidfuzz import fuzz
from urllib.parse import urlparse
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
EMAIL_REGEX = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
PHONE_REGEX = r'\+?\d[\d\-\(\)\s]{7,}\d'

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def extract_emails(text):
    emails = re.findall(EMAIL_REGEX, text)
    return list(set(emails))

def extract_phones(html):
    soup = BeautifulSoup(html, "lxml")
    phones = set()

    # Extract from tel: links (most reliable method)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("tel:"):
            number = href.replace("tel:", "").strip()
            # Remove spaces and hyphens
            number = re.sub(r'[\s\-]', '', number)
            # Only add if length is reasonable (8-15 digits)
            if 8 <= len(number) <= 15:
                phones.add(number)

    # Only use regex as fallback if no tel: links found
    if not phones:
        # Find individual phone numbers, not a long continuous string
        text = soup.get_text(" ", strip=True)
        # Look for common phone patterns with spaces/dashes
        regex_matches = re.findall(
            r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            text
        )
        for match in regex_matches:
            cleaned = re.sub(r'[\s\-\(\)]', '', match)
            if 8 <= len(cleaned) <= 15:
                phones.add(cleaned)

    return list(phones)

def fetch_page(url):

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            return response.text

    except:
        pass

    return ""

def clean_html(html):

    soup = BeautifulSoup(html, "lxml")

    for tag in soup([
        "script",
        "style",
        "nav",
        "footer"
    ]):
        tag.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True
    )

    return text

def get_internal_links(base_url):

    html = fetch_page(base_url)

    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")

    links = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        full_url = urljoin(
            base_url,
            href
        )

        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.append(full_url)

    return list(set(links))

IMPORTANT_KEYWORDS = [
    "about",
    "contact",
    "service",
    "solution",
    "company"
]

def get_relevant_links(base_url):

    links = get_internal_links(base_url)

    selected = []

    for link in links:

        score = max(
            fuzz.partial_ratio(
                keyword,
                link.lower()
            )
            for keyword in IMPORTANT_KEYWORDS
        )

        if score > 70:
            selected.append(link)

    return selected[:5]

def ai_extract(text):

    print("=" * 50)
    print("TEXT LENGTH:", len(text))
    print("=" * 50)
    print(text[:1000])
    print("=" * 50)

    prompt = f"""
      Return ONLY valid JSON.

      Never invent information.

      If information is unavailable,
      return empty string.

      Schema:

      {{
        "website_name":"",
        "company_name":"",
        "address":"",
        "core_service":"",
        "target_customer":"",
        "probable_pain_point":"",
        "outreach_opener":""
      }}

      Content:

      {text[:6000]}
      """
    try:

        print("CALLING GEMINI")
        response = model.generate_content(
            prompt
        )

        output = response.text.strip()
        print("\n===================")
        print("RAW GEMINI OUTPUT")
        print("===================")
        print(output)
        print("===================\n")

        output = output.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        )

        output = output.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        )

        return json.loads(output)

    except Exception as e:

        print("AI Error:", e)

        return {
            "website_name":"",
            "company_name":"",
            "address":"",
            "core_service":"",
            "target_customer":"",
            "probable_pain_point":"",
            "outreach_opener":""
        }
    
def enrich_company(url: str) -> dict:

    combined_text = ""

    html = fetch_page(url)

    if html:
        combined_text += clean_html(html)

    relevant_links = get_relevant_links(url)

    print("Relevant links:", relevant_links)

    for page in relevant_links:

        html = fetch_page(page)

        if html:

            combined_text += "\n\n"

            combined_text += clean_html(html)

    emails = extract_emails(combined_text)

    phones = extract_phones(combined_text)

    ai_data = ai_extract(combined_text)

    result = {
        "website_name":
            ai_data.get(
                "website_name",
                ""
            ),

        "company_name":
            ai_data.get(
                "company_name",
                ""
            ),

        "address":
            ai_data.get(
                "address",
                ""
            ),

        "mobile_number":
            phones[0] if phones else "",

        "mail":
            emails,

        "core_service":
            ai_data.get(
                "core_service",
                ""
            ),

        "target_customer":
            ai_data.get(
                "target_customer",
                ""
            ),

        "probable_pain_point":
            ai_data.get(
                "probable_pain_point",
                ""
            ),

        "outreach_opener":
            ai_data.get(
                "outreach_opener",
                ""
            )
    }

    return result
    
