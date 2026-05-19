"""Re-scrape the weak classes into review/ folders for manual culling.

The classifier confuses chakhchoukha, karantika and dolma the most (0.55-0.70
recall). This pulls a large candidate pool per class so you can hand-pick the
cleanest images. Output goes to review/<class>/ and does NOT touch data/.

Workflow:
  1. python rescrape_weak.py
  2. Open each review/<class>/ folder, delete wrong/duplicate/junk images.
  3. Replace data/<class>/ with the cleaned ~100-120 keepers.
  4. Re-run train_resnet50.ipynb.
"""
import io
import os
import time
import urllib.request

from PIL import Image
from ddgs import DDGS

QUERIES = {
    "chakhchoukha": ["chakhchoukha algerienne", "chakhchoukha plat algerien",
                     "algerian chakhchoukha food", "chakhchoukha rechta",
                     "chakhchoukha biskra recette"],
    "karantika":    ["karantika algerienne", "garantita oran plat",
                     "calentica algerie", "karantika chickpea flan",
                     "garantita recette algerienne"],
    "dolma":        ["dolma algerienne plat", "dolma legumes farcis algerien",
                     "algerian dolma", "dolma batata algerienne",
                     "dolma kefta algerienne"],
}
PER_QUERY = 60
TARGET    = 160          # big pool — you cull it down to ~100-120 by hand
MIN_DIM   = 256
HEADERS   = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=20).read()


def big_enough(data):
    if len(data) < 5000:
        return False
    try:
        return min(Image.open(io.BytesIO(data)).size) >= MIN_DIM
    except Exception:
        return False


def scrape(dish, queries):
    out = f"review/{dish}"
    os.makedirs(out, exist_ok=True)
    seen = set()
    n = 0
    for q in queries:
        if n >= TARGET:
            break
        results = []
        for attempt in range(3):
            try:
                results = list(DDGS().images(q, safesearch="on",
                                             max_results=PER_QUERY))
                break
            except Exception as e:
                print(f"  [{q}] retry {attempt}: {e}")
                time.sleep(8)
        print(f"  {q!r}: {len(results)} candidates")
        for item in results:
            if n >= TARGET:
                break
            for url in (item.get("image"), item.get("thumbnail")):
                if not url or url in seen:
                    continue
                seen.add(url)
                try:
                    data = fetch(url)
                except Exception:
                    continue
                if not big_enough(data):
                    continue
                with open(f"{out}/{n:04d}.jpg", "wb") as f:
                    f.write(data)
                n += 1
                break
        time.sleep(3)
    print(f"{dish}: saved {n} candidates -> {out}/")


if __name__ == "__main__":
    for dish, queries in QUERIES.items():
        print(f"\n=== {dish} ===")
        scrape(dish, queries)
    print("\nDone. Hand-pick the cleanest ~100-120 per class from review/,")
    print("replace data/<class>/, then re-run train_resnet50.ipynb.")
