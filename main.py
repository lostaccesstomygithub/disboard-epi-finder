# https://disboard.org/site/get-invite/<ID> <- git invite
# verification cookie = ageVerified 1

import curl_cffi
from bs4 import BeautifulSoup
import re
import loguru

import time

def normalize(text: str) -> str:
    return text.lower()

def load_phrases(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [normalize(line).strip() for line in f if line.strip()]

def scan(text: str, phrases: list[str]) -> list[str]:
    norm = normalize(text)
    matches = []
    for p in phrases:
        pattern = r"\b" + re.escape(p) + r"\b"
        if re.search(pattern, norm):
            matches.append(p)
    return matches

phrases = load_phrases("codewords.txt")
output = open("discords.csv", "w+", encoding="utf-8")
output.write("server_id,flags\n")

session = curl_cffi.Session(cookies={"ageVerified": "1"}, impersonate="chrome")

first_page = session.get("https://disboard.org/search?keyword=proship&nsfw=1")
soup_first = BeautifulSoup(first_page.content, "lxml")
csrf_token = soup_first.find("meta", attrs={"name": "csrf-token"})["content"]

index = 1
while True:
    request = session.get(
        f"https://disboard.org/search?keyword=proship&nsfw=1&page={index}",
        headers={
            "Referer": "https://disboard.org/search?keyword=proship&nsfw=1",
            "x-requested-with": "XMLHttpRequest",
            "x-csrf-token": csrf_token,
        },
    )
    parsed = BeautifulSoup(request.content, "lxml")
    servers = parsed.find_all(class_="column is-one-third-desktop is-half-tablet")

    if not servers:
        break

    for server in servers:
        members_el = server.find("span", class_="server-online")
        members = members_el.text if members_el else None

        name_el = server.select_one("div.server-name a")
        name = name_el["title"] if name_el else None

        card = server.find(class_=re.compile(r"\bserver-\d+\b"))
        server_id = None
        if card:
            m = re.search(r"server-(\d+)", " ".join(card.get("class", [])))
            server_id = m.group(1) if m else None

        desc_el = server.find("div", class_="elastic-text-inner")
        description = desc_el.text if desc_el else ""
        if "verification" not in description:
            results = scan(description, phrases)
            if len(results) > 0:
                tagged = "|".join(results)
                loguru.logger.info(f"{name} [{server_id}] Members: {members}, {tagged}")
                output.write(f"{server_id},{tagged}\n")
    time.sleep(2)
    index += 1