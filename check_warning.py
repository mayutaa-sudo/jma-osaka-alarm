import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ====== ここだけ変更すれば市町村を変えられます ======
TARGET_CITY = "大阪市"
# 例: "堺市", "豊中市", "吹田市", "東大阪市"
# ================================================

FEED_URL = "https://www.data.jma.go.jp/developer/xml/feed/extra_l.xml"

WARNING_WORDS = [
    "特別警報",
    "大雨警報",
    "洪水警報",
    "暴風警報",
    "暴風雪警報",
    "大雪警報",
    "波浪警報",
    "高潮警報",
]

def fetch_text(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")

def get_latest_warning_links(feed_xml):
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(feed_xml)

    links = []
    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns)
        if "気象警報・注意報" not in title:
            continue

        link = entry.find("atom:link", ns)
        if link is not None and link.get("href"):
            links.append(link.get("href"))

    return links

def judge_warning(xml_text):
    if TARGET_CITY not in xml_text:
        return False, []

    found = []
    for word in WARNING_WORDS:
        pattern = TARGET_CITY + r".{0,200}" + word
        if re.search(pattern, xml_text, re.DOTALL):
            found.append(word)

    return len(found) > 0, found

def main():
    feed_xml = fetch_text(FEED_URL)
    links = get_latest_warning_links(feed_xml)

    warning = False
    matched_warnings = []
    used_url = None

    for url in links[:50]:
        xml_text = fetch_text(url)
        result, found = judge_warning(xml_text)

        if result:
            warning = True
            matched_warnings = found
            used_url = url
            break

    now = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()

    output = {
        "city": TARGET_CITY,
        "warning": warning,
        "matched_warnings": matched_warnings,
        "checked_at": now,
        "source_feed": FEED_URL,
        "source_xml": used_url,
    }

    Path("docs").mkdir(exist_ok=True)
    Path("docs/warning.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
