"""Scrape dish images via DuckDuckGo image search.

Why DDG and not icrawler/Bing:
  - icrawler's Google parser is broken (Google changed its HTML).
  - icrawler's Bing scraper hits the /images/async HTML endpoint, which serves
    trending-filler junk (architecture, wildlife, fashion) for any niche query.
    couscous/harira survived only because they are globally indexed.
  - DDG queries Bing's real search API -> relevant results for niche dishes,
    and has built-in SafeSearch.

Images are saved from DDG's thumbnail proxy (~350-500px). The original host
URLs mostly reject hotlinked requests; the proxy always serves. ~350px is fine
for a 224px-input classifier.

Re-run safe: skips dishes already at TARGET. Dishes not in KEEP are wiped
before scraping so the old Bing junk is removed.
"""
import os
import time
import random
import urllib.request

from ddgs import DDGS

TARGET = 100          # images to aim for per dish
MIN_OK = 70           # below this after scraping = flagged
MIN_BYTES = 4000      # smaller files are broken/placeholder images
KEEP = {"couscous", "harira"}   # good Bing data already — append, don't wipe

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# English + French queries. Arabic dropped (matches script, not food).
DISHES = {
    "couscous":       ["algerian couscous", "couscous algerien plat", "couscous viande legumes"],
    "chakhchoukha":   ["chakhchoukha algerienne", "chakhchoukha plat", "algerian chakhchoukha food"],
    "rechta":         ["rechta algerienne", "rechta poulet plat", "algerian rechta dish"],
    "mhadjeb":        ["algerian mhadjeb", "mhadjeb crepe farcie", "mhadjeb recipe"],
    "bourek":         ["algerian bourek", "bourek viande algerien", "brik bourek fried"],
    "chorba_frik":    ["chorba frik algerienne", "algerian chorba frik soup", "chorba frik ramadan"],
    "harira":         ["harira soup", "harira algerienne soupe", "harira ramadan bowl"],
    "dolma":          ["dolma algerienne", "algerian dolma stuffed vegetables", "dolma legumes farcis"],
    "tajine_zitoune": ["tajine zitoune algerien", "algerian tajine zitoune", "tajine olives poulet"],
    "karantika":      ["karantika algerienne", "garantita oran", "algerian karantika chickpea"],
    "mhalbi":         ["mhalbi algerien dessert", "algerian mhalbi pudding", "mhalbi riz dessert"],
    "makroud":        ["makroud algerien gateau", "maqrout dattes", "algerian makroud pastry"],
    "baghrir":        ["baghrir algerien", "baghrir crepe mille trous", "algerian baghrir pancake"],
    "zlabia":         ["zlabia algerienne", "zlabia gateau", "algerian zlabia sweet"],
    "kalb_el_louz":   ["kalb el louz gateau", "qalb el louz semoule amande", "algerian kalb el louz"],
}


def count_images(folder):
    if not os.path.isdir(folder):
        return 0
    return len([f for f in os.listdir(folder) if f.lower().endswith(".jpg")])


def wipe_folder(folder):
    if not os.path.isdir(folder):
        return
    for f in os.listdir(folder):
        if f != ".gitkeep":
            os.remove(os.path.join(folder, f))


def ddg_search(query, retries=4):
    for attempt in range(retries):
        try:
            return list(DDGS().images(query, safesearch="on", max_results=100))
        except Exception as e:
            wait = 8 * (attempt + 1)
            print(f"  [retry {attempt + 1}] {query!r}: {e} -- waiting {wait}s")
            time.sleep(wait)
    print(f"  [GIVE UP] {query!r}")
    return []


def download(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=20).read()
        if len(data) < MIN_BYTES:
            return False
        with open(path, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False


def scrape_dish(dish, queries):
    out_dir = f"data/{dish}"
    os.makedirs(out_dir, exist_ok=True)
    seen = set()
    idx = count_images(out_dir)
    for query in queries:
        if count_images(out_dir) >= TARGET:
            break
        print(f"  query: {query}")
        for item in ddg_search(query):
            if count_images(out_dir) >= TARGET:
                break
            url = item.get("thumbnail") or item.get("image")
            if not url or url in seen:
                continue
            seen.add(url)
            if download(url, os.path.join(out_dir, f"ddg_{idx:04d}.jpg")):
                idx += 1
        time.sleep(random.uniform(3, 6))


def main():
    for dish, queries in DISHES.items():
        out_dir = f"data/{dish}"
        if count_images(out_dir) >= TARGET:
            print(f"\n=== {dish} === already has {count_images(out_dir)}, skipping")
            continue
        if dish not in KEEP:
            wipe_folder(out_dir)   # clear old Bing junk
        print(f"\n=== {dish} === (have {count_images(out_dir)})")
        scrape_dish(dish, queries)
        time.sleep(random.uniform(8, 15))

    print("\n==== RESULT ====")
    failed = []
    for dish in DISHES:
        n = count_images(f"data/{dish}")
        mark = "OK" if n >= MIN_OK else "LOW <-- FIX"
        if n < MIN_OK:
            failed.append(dish)
        print(f"  {dish:16s} {n:4d}  {mark}")
    if failed:
        print(f"\n{len(failed)} dish(es) under {MIN_OK}: {', '.join(failed)}")
        print("Re-run this script — it skips dishes already at TARGET.")
    else:
        print("\nAll dishes scraped. Next: manual cleanup (delete wrong/duplicate images).")


if __name__ == "__main__":
    main()
