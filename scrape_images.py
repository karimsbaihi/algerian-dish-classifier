"""Scrape dish images with icrawler/Bing.

Re-run safe: counts existing files and skips dishes already at TARGET.
Arabic queries removed on purpose — they match the script, not the food.
"""
from icrawler.builtin import BingImageCrawler
from icrawler.builtin.bing import BingFeeder
import os
import time
import random


class SafeBingFeeder(BingFeeder):
    """BingFeeder with strict SafeSearch forced on — blocks explicit results."""

    def feed(self, keyword, offset, max_num, filters=None):
        base_url = ("https://www.bing.com/images/async?q={}&first={}"
                    "&adlt=strict&safeSearch=Strict")
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters)
        filter_str = "&qft=" + filter_str if filter_str else ""

        for i in range(offset, offset + max_num, 20):
            url = base_url.format(keyword, i) + filter_str
            self.out_queue.put(url)
            self.logger.debug(f"put url to url_queue: {url}")

TARGET = 100          # raw images to aim for; manual cleanup trims to ~80 clean
PER_QUERY = 40        # 3 queries x 40 = ~120 raw, leaves room for dupes/junk
MIN_OK = 60           # below this after scraping = flagged as failed

# English + French queries only. Food-specific words ("plat", "food", "dish")
# pull cooked dishes instead of calligraphy / wrong cuisines.
DISHES = {
    "couscous":       ["algerian couscous plat", "couscous algerien viande legumes", "couscous food dish"],
    "chakhchoukha":   ["chakhchoukha algerienne", "chakhchoukha plat algerien", "algerian chakhchoukha food"],
    "rechta":         ["rechta algerienne plat", "rechta poulet algerien", "algerian rechta dish"],
    "mhadjeb":        ["mhadjeb algerien", "mhadjeb crepe farcie algerienne", "algerian mhadjeb food"],
    "bourek":         ["bourek algerien viande", "algerian bourek fried", "brik bourek plat"],
    "chorba_frik":    ["chorba frik algerienne", "chorba frik soupe ramadan", "algerian chorba frik soup"],
    "harira":         ["harira soupe bol", "harira algerienne soup", "harira ramadan soup bowl"],
    "dolma":          ["dolma algerienne plat", "dolma legumes farcis algerien", "algerian dolma stuffed vegetables"],
    "tajine_zitoune": ["tajine zitoune algerien", "tajine olives poulet algerien", "algerian tajine zitoune dish"],
    "karantika":      ["karantika algerienne", "garantita oran plat", "algerian karantika chickpea flan"],
    "mhalbi":         ["mhalbi algerien dessert", "mhalbi riz creme dessert", "algerian mhalbi pudding"],
    "makroud":        ["makroud algerien gateau", "maqrout dattes semoule", "algerian makroud pastry"],
    "baghrir":        ["baghrir crepe mille trous", "baghrir algerien", "algerian baghrir pancake"],
    "zlabia":         ["zlabia algerienne", "zlabia boufarik gateau", "algerian zlabia sweet"],
    "kalb_el_louz":   ["kalb el louz gateau", "qalb el louz semoule amande", "algerian kalb el louz dessert"],
}


def count_images(folder):
    if not os.path.isdir(folder):
        return 0
    return len([f for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))])


def scrape_dish(dish, queries):
    out_dir = f"data/{dish}"
    os.makedirs(out_dir, exist_ok=True)
    for query in queries:
        if count_images(out_dir) >= TARGET:
            break
        print(f"  query: {query}")
        try:
            crawler = BingImageCrawler(
                feeder_cls=SafeBingFeeder,
                storage={"root_dir": out_dir},
                feeder_threads=1,
                parser_threads=1,
                downloader_threads=2,   # low and slow — Bing blocks aggressive crawls
            )
            crawler.crawl(
                keyword=query,
                max_num=PER_QUERY,
                min_size=(300, 300),
                file_idx_offset="auto",
            )
        except Exception as e:
            print(f"  [SKIP] {query} failed: {e}")
        time.sleep(random.uniform(8, 14))   # pause between queries


def main():
    for dish, queries in DISHES.items():
        have = count_images(f"data/{dish}")
        if have >= TARGET:
            print(f"\n=== {dish} === already has {have}, skipping")
            continue
        print(f"\n=== {dish} === (have {have})")
        scrape_dish(dish, queries)
        # one retry if the dish came back nearly empty (likely a transient block)
        if count_images(f"data/{dish}") < MIN_OK:
            print(f"  low result, waiting 30s and retrying {dish}")
            time.sleep(30)
            scrape_dish(dish, queries)
        time.sleep(random.uniform(15, 25))  # pause between dishes

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
        print("Re-run this script — it skips dishes already at TARGET and retries the rest.")
    else:
        print("\nAll dishes scraped. Next: manual cleanup.")


if __name__ == "__main__":
    main()
