import sys

import curl_cffi
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse
import re

server_id = sys.argv[1]

session = curl_cffi.Session(cookies={"ageVerified": "1"}, impersonate="chrome")

first_page = session.get("https://disboard.org/search?keyword=proship&nsfw=1")
soup_first = BeautifulSoup(first_page.content, "lxml")
csrf_token = soup_first.find("meta", attrs={"name": "csrf-token"})["content"]


get_invite = session.post("https://disboard.org/site/get-invite/" + server_id, impersonate="chrome", headers={
    "Referer": "https://disboard.org/server/join/" + server_id,
    "X-CSRF-Token": csrf_token,
}).text

invite = urlunparse(urlparse(get_invite)._replace(query=""))
print(invite.strip('"'))