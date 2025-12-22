"""
ArXiv + OpenAlex 
cохраняется в data/raw.jsonl
"""
import json
import time
import requests
import os
import random
import re
from pathlib import Path


#BASE_DIR = Path(__file__).parent
DATA_DIR = Path("C:\\PROJECT\\ai-agent\\data")
DATA_DIR.mkdir(exist_ok=True)
RAW_OUTPUT = Path("C:\\PROJECT\\ai-agent\\data\\raw.jsonl")

MIN_ARTICLES = 60  
REQUEST_DELAY = (2.0, 4.0)
KEYWORDS = [
    "steel deoxidation", "non-metallic inclusions", "titanium microalloying",
    "continuous casting inclusions", "steel cleanliness", "inclusion engineering",
    "calcium treatment steel", "secondary metallurgy", "slag metal reaction",
    "aluminum killed steel", "titanium inclusion", "steel refining"
]


def search_arxiv(query: str, max_results: int = 30):
    articles = []
    base_url = "http://export.arxiv.org/api/query"
    start = 0
    while len(articles) < max_results:
        params = {
            "search_query": f'all:"{query}"',
            "start": start,
            "max_results": 100,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        try:
            resp = requests.get(base_url, params=params, timeout=15)
            resp.raise_for_status()
            entries = re.findall(r'<entry>(.*?)</entry>', resp.text, re.DOTALL)
            for entry in entries:
                title = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
                abstract = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
                arxiv_id = re.search(r'<id>http://arxiv.org/abs/([^<]+)</id>', entry)
                pdf_link = re.search(r'<link title="pdf" href="([^"]+)"', entry)

                if title and abstract and arxiv_id:
                    articles.append({
                        "title": title.group(1).strip().replace("\n", " "),
                        "abstract": abstract.group(1).strip().replace("\n", " "),
                        "source": f"arxiv:{arxiv_id.group(1)}",
                        "pdf_url": pdf_link.group(1) if pdf_link else f"https://arxiv.org/pdf/{arxiv_id.group(1)}.pdf"
                    })
                if len(articles) >= max_results:
                    break
            if len(entries) < 100:
                break
            start += 100
        except Exception as e:
            print(f"ArXiv error: {e}")
            break
        time.sleep(random.uniform(*REQUEST_DELAY))
    return articles


def search_openalex(query: str, max_results: int = 30):
    articles = []
    url = "https://api.openalex.org/works"
    cursor = "*"
    while len(articles) < max_results:
        params = {
            "filter": f'title.search:"{query}"',
            "per_page": 50,
            "cursor": cursor,
            "select": "id,display_name,abstract_inverted_index,primary_location"
        }
        try:
            resp = requests.get(url, params=params, timeout=20)
            data = resp.json()
            for work in data.get("results", []):
                title = work.get("display_name", "")
                abstract = ""
                if work.get("abstract_inverted_index"):
                    inv_idx = work["abstract_inverted_index"]
                    max_pos = max((pos for positions in inv_idx.values() for pos in positions), default=0)
                    words = [""] * (max_pos + 1)
                    for word, positions in inv_idx.items():
                        for pos in positions:
                            if pos < len(words):
                                words[pos] = word
                    abstract = " ".join(w for w in words if w)
# json
                pdf_url = ""
                if work.get("primary_location", {}).get("pdf_url"):
                    pdf_url = work["primary_location"]["pdf_url"]
                elif work.get("primary_location", {}).get("landing_page_url"):
                    pdf_url = work["primary_location"]["landing_page_url"]

                if title and abstract:
                    articles.append({
                        "title": title,
                        "abstract": abstract,
                        "source": work["id"],
                        "pdf_url": pdf_url
                    })
                if len(articles) >= max_results:
                    break

            cursor = data.get("meta", {}).get("next_cursor", "")
            if not cursor:
                break
        except Exception as e:
            print(f"OpenAlex error: {e}")
            break
        time.sleep(random.uniform(*REQUEST_DELAY))
    return articles


def save_jsonl(articles, filepath):
    seen = set()
    unique = []
    for art in articles:
        key = art["source"]
        if key not in seen and art.get("title") and art.get("abstract"):
            seen.add(key)
            unique.append(art)
    
    with open(filepath, "w", encoding="utf-8") as f:
        for art in unique:
            f.write(json.dumps(art, ensure_ascii=False) + "\n")
    print(f"Сохранено {len(unique)} уникальных статей → {filepath}")


def main():
    all_articles = []
    per_keyword = max(5, MIN_ARTICLES // len(KEYWORDS) + 5)

    print("парсинг статей...")
    for kw in KEYWORDS:
        print(f"→ {kw}")
        arxiv = search_arxiv(kw, per_keyword)
        openalex = search_openalex(kw, per_keyword)
        all_articles.extend(arxiv + openalex)
        print(f"    +{len(arxiv)} (ArXiv) +{len(openalex)} (OpenAlex). всего {len(all_articles)}")
        if len(all_articles) >= MIN_ARTICLES + 20:
            break

    final = all_articles[:MIN_ARTICLES + 30]  #запас на дубли
    save_jsonl(final, RAW_OUTPUT)
    print(f"\nвсё оке. файл: {RAW_OUTPUT}")

if __name__ == "__main__":
    main()