import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ===== 設定：ここだけ変えればOK =====
TARGET_CITY = "大阪市"
# 例: "堺市", "豊中市", "吹田市", "東大阪市"

FEED_URL = "https://www.data.jma.go.jp/developer/xml/feed/extra_l.xml"

TARGET_WARNING_TYPE = "気象警報・注意報（市町村等）"

WARNING_NAMES = [
    "大雨特別警報",
    "暴風特別警報",
    "暴風雪特別警報",
    "大雪特別警報",
    "波浪特別警報",
    "高潮特別警報",
    "大雨警報",
    "洪水警報",
    "暴風警報",
    "暴風雪警報",
    "大雪警報",
    "波浪警報",
    "高潮警報",
]
# ================================


def fetch_text(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def tag_name(element):
    return element.tag.split("}", 1)[-1]


def find_children(element, name):
    return [child for child in list(element) if tag_name(child) == name]


def find_first_child(element, name):
    for child in list(element):
        if tag_name(child) == name:
            return child
    return None


def get_text(element, child_name):
    child = find_first_child(element, child_name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def get_warning_xml_links(feed_xml):
    root = ET.fromstring(feed_xml)
    links = []

    for entry in root.iter():
        if tag_name(entry) != "entry":
            continue

        title = ""
        link_url = ""

        for child in list(entry):
            name = tag_name(child)
            if name == "title" and child.text:
                title = child.text.strip()
            elif name == "link":
                link_url = child.attrib.get("href", "")

        if "気象警報・注意報" in title and link_url:
            links.append(link_url)

    return links


def parse_city_warnings(xml_text):
    root = ET.fromstring(xml_text)

    active_warnings = []
    city_found = False

    for warning in root.iter():
        if tag_name(warning) != "Warning":
            continue

        if warning.attrib.get("type") != TARGET_WARNING_TYPE:
            continue

        for item in find_children(warning, "Item"):
            areas = find_first_child(item, "Areas")
            if areas is None:
                continue

            area_names = []
            for area in find_children(areas, "Area"):
                area_names.append(get_text(area, "Name"))

            if TARGET_CITY not in area_names:
                continue

            city_found = True

            for kind in find_children(item, "Kind"):
                warning_name = get_text(kind, "Name")
                status = get_text(kind, "Status")

                if warning_name in WARNING_NAMES and status != "解除":
                    active_warnings.append({
                        "name": warning_name,
                        "status": status if status else "発表中"
                    })

    return city_found, active_warnings


def main():
    feed_xml = fetch_text(FEED_URL)
    links = get_warning_xml_links(feed_xml)

    city_found_anywhere = False
    active_warnings = []
    used_xml = None

    for url in links[:80]:
        xml_text = fetch_text(url)
        city_found, warnings = parse_city_warnings(xml_text)

        if city_found:
            city_found_anywhere = True
            used_xml = url

            if warnings:
                active_warnings = warnings
                break

    now = datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()

    output = {
        "city": TARGET_CITY,
        "warning": len(active_warnings) > 0,
        "active_warnings": active_warnings,
        "city_found": city_found_anywhere,
        "checked_at": now,
        "source_feed": FEED_URL,
        "source_xml": used_xml
    }

    Path("docs").mkdir(exist_ok=True)
    Path("docs/warning.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
