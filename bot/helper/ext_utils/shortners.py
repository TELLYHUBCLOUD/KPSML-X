from base64 import b64encode
from random import choice, random, randrange
from time import sleep as sync_sleep
from urllib.parse import quote

from aiohttp import ClientSession
from cloudscraper import create_scraper
from urllib3 import disable_warnings

from bot import LOGGER, shorteners_list

# Worker URL
WORKER_URL = "https://tellylinks.tellycloudapi.workers.dev/shorten"


def short_url(longurl, attempt=0):
    if attempt >= 4:
        return longurl

    # ========= METHOD 1: Cloudflare Worker =========
    try:
        import requests
        res = requests.get(f"{WORKER_URL}?url={quote(longurl)}", timeout=10).json()
        if res.get("success"):
            return res.get("shortUrl")
    except:
        pass

    # ========= METHOD 2: Custom Shorteners =========
    if not shorteners_list:
        return longurl

    i = 0 if len(shorteners_list) == 1 else randrange(len(shorteners_list))
    _dic = shorteners_list[i]
    _shortener = _dic['domain']
    _api = _dic['api_key']

    cget = create_scraper().request
    disable_warnings()

    try:
        if "shorte.st" in _shortener:
            headers = {'public-api-token': _api}
            data = {'urlToShorten': quote(longurl)}
            return cget('PUT', 'https://api.shorte.st/v1/data/url', headers=headers, data=data).json()['shortenedUrl']

        elif "linkvertise" in _shortener:
            url = quote(b64encode(longurl.encode("utf-8")))
            lv = [
                f"https://link-to.net/{_api}/{random()*1000}/dynamic?r={url}",
                f"https://up-to-down.net/{_api}/{random()*1000}/dynamic?r={url}",
                f"https://direct-link.net/{_api}/{random()*1000}/dynamic?r={url}",
                f"https://file-link.net/{_api}/{random()*1000}/dynamic?r={url}",
            ]
            return choice(lv)

        elif "bitly.com" in _shortener:
            headers = {"Authorization": f"Bearer {_api}"}
            return cget('POST', "https://api-ssl.bit.ly/v4/shorten",
                        json={"long_url": longurl}, headers=headers).json()['link']

        elif "ouo.io" in _shortener:
            return cget('GET', f"http://ouo.io/api/{_api}?s={longurl}", verify=False).text

        elif "cutt.ly" in _shortener:
            return cget('GET', f"http://cutt.ly/api/api.php?key={_api}&short={longurl}").json()['url']['shortLink']

        else:
            res = cget('GET', f"https://{_shortener}/api?api={_api}&url={quote(longurl)}").json()
            shorted = res.get("shortenedUrl")

            if not shorted:
                sh = cget('GET', f"https://api.shrtco.de/v2/shorten?url={quote(longurl)}").json()
                shorted = sh['result']['full_short_link']

            return shorted

    except Exception as e:
        LOGGER.error(e)
        sync_sleep(1)
        return short_url(longurl, attempt+1)
