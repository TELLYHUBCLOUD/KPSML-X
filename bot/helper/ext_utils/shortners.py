from asyncio import sleep
from base64 import b64encode
from random import choice, random, randrange
from time import sleep as sync_sleep
from urllib.parse import quote
from aiohttp import ClientSession
from cloudscraper import create_scraper
from urllib3 import disable_warnings
from bot import LOGGER, shorteners_list

# Cloudflare Worker URL
WORKER_URL = "https://tellylinks.tellycloudapi.workers.dev/shorten"

async def short_url(longurl, attempt=0):
    """
    Shortens URL using multiple methods with priority:
    1. Cloudflare Worker (Primary - GPLinks with custom domain + landing page)
    2. Custom shorteners list (Fallback - all old shorteners)
    3. Direct return original URL (Last resort)
    
    Args:
        longurl: The long URL to be shortened
        attempt: Current attempt number (max 4)
    
    Returns:
        Shortened URL or original URL if all attempts fail
    """
    
    # Max attempts check
    if attempt >= 4:
        LOGGER.warning(f"Max attempts reached for URL: {longurl}")
        return longurl
    
    async with ClientSession() as session:
        
        # ========== METHOD 1: Cloudflare Worker (Primary) ==========
        try:
            async with session.get(
                f"{WORKER_URL}?url={quote(longurl)}",
                timeout=10
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        # Returns: https://tellylinks.tellycloudapi.workers.dev/3UwMmEW
                        worker_url = result.get("shortUrl")
                        LOGGER.info(f"✅ Worker shortened: {longurl[:50]}... -> {worker_url}")
                        return worker_url
        except Exception as e:
            LOGGER.error(f"❌ Worker shortening failed: {e}")
        
        # ========== METHOD 2: Custom Shorteners (Fallback) ==========
        if not shorteners_list:
            LOGGER.warning("No shorteners configured, returning original URL")
            return longurl
        
        i = 0 if len(shorteners_list) == 1 else randrange(len(shorteners_list))
        _shorten_dict = shorteners_list[i]
        _shortener = _shorten_dict['domain']
        _shortener_api = _shorten_dict['api_key']
        
        try:
            # Using cloudscraper for compatibility with old code
            cget = create_scraper().request
            disable_warnings()
            
            # Shorte.st
            if "shorte.st" in _shortener:
                headers = {'public-api-token': _shortener_api}
                data = {'urlToShorten': quote(longurl)}
                shorted = cget('PUT', 'https://api.shorte.st/v1/data/url', headers=headers, data=data).json()['shortenedUrl']
                LOGGER.info(f"✅ Shorte.st used: {shorted}")
                return shorted
            
            # Linkvertise
            elif "linkvertise" in _shortener:
                url = quote(b64encode(longurl.encode("utf-8")))
                linkvertise = [
                    f"https://link-to.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                    f"https://up-to-down.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                    f"https://direct-link.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}",
                    f"https://file-link.net/{_shortener_api}/{random() * 1000}/dynamic?r={url}"
                ]
                shorted = choice(linkvertise)
                LOGGER.info(f"✅ Linkvertise used: {shorted}")
                return shorted
            
            # Bitly
            elif "bitly.com" in _shortener:
                headers = {"Authorization": f"Bearer {_shortener_api}"}
                shorted = cget('POST', "https://api-ssl.bit.ly/v4/shorten", json={"long_url": longurl}, headers=headers).json()["link"]
                LOGGER.info(f"✅ Bitly used: {shorted}")
                return shorted
            
            # Ouo.io
            elif "ouo.io" in _shortener:
                shorted = cget('GET', f'http://ouo.io/api/{_shortener_api}?s={longurl}', verify=False).text
                LOGGER.info(f"✅ Ouo.io used: {shorted}")
                return shorted
            
            # Cutt.ly
            elif "cutt.ly" in _shortener:
                shorted = cget('GET', f'http://cutt.ly/api/api.php?key={_shortener_api}&short={longurl}').json()['url']['shortLink']
                LOGGER.info(f"✅ Cutt.ly used: {shorted}")
                return shorted
            
            # Generic shortener (GPLinks, UrlShortX, etc.)
            else:
                res = cget('GET', f'https://{_shortener}/api?api={_shortener_api}&url={quote(longurl)}').json()
                shorted = res.get('shortenedUrl')
                
                # Fallback to shrtco if generic fails
                if not shorted:
                    try:
                        shrtco_res = cget('GET', f'https://api.shrtco.de/v2/shorten?url={quote(longurl)}').json()
                        shrtco_link = shrtco_res['result']['full_short_link']
                        res = cget('GET', f'https://{_shortener}/api?api={_shortener_api}&url={shrtco_link}').json()
                        shorted = res.get('shortenedUrl')
                    except Exception as e:
                        LOGGER.error(f"Shrtco fallback failed: {e}")
                
                if shorted:
                    LOGGER.info(f"✅ Generic shortener used ({_shortener}): {shorted}")
                    return shorted
                
        except Exception as e:
            LOGGER.error(f"❌ Custom shortener failed ({_shortener}): {e}")
        
        # ========== METHOD 3: Retry ==========
        sync_sleep(1)
        attempt += 1
        LOGGER.info(f"🔄 Retrying... Attempt {attempt}/4")
        return await short_url(longurl, attempt)
