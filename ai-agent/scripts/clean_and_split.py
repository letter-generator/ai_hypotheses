import json
import re
import os
from pathlib import Path
from typing import List, Dict
import tiktoken  


#BASE_DIR = Path(__file__).parent
RAW_FILE = Path("C:\\PROJECT\\ai-agent\\data\\raw.jsonl")
CHUNKS_FILE = Path("C:\\PROJECT\\ai-agent\\data\\clean.jsonl")
(CHUNKS_FILE.parent).mkdir(exist_ok=True)

MAX_TOKENS_PER_CHUNK = 800      
OVERLAP_TOKENS = 200            
ENCODER = tiktoken.encoding_for_model("gpt-4o") 

def count_tokens(text: str) -> int:
    return len(ENCODER.encode(text, disallowed_special=()))

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\$.*?\$', '', text)
    text = re.sub(r'\\\(.*?\\\)', '', text)
    text = re.sub(r'\\\[.*?\\\]', '', text)
    text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\[[0-9,–-]+\]', '', text)
    text = re.sub(r'\([A-Za-z].*?[0-9]{4}[a-z]?\)', '', text)
    text = re.sub(r'(Figure|Fig\.|Table|Eq\.|Equation)[\s]*[0-9IVX.]+', '', text)
    text = re.sub(r'[^\w\s.,;:!?\-\(\)%/°]', '', text)
    return text.strip()

def split_into_chunks(text: str, metadata: Dict, max_tokens: int = MAX_TOKENS_PER_CHUNK, overlap: int = OVERLAP_TOKENS) -> List[Dict]:
    tokens = ENCODER.encode(text, disallowed_special=())
    chunks = []
    i = 0
    chunk_id = 0
    while i < len(tokens):
        end = i + max_tokens
        chunk_tokens = tokens[i:end]
        chunk_text = ENCODER.decode(chunk_tokens)
        
        chunks.append({
            "chunk_id": f"{metadata['source']}_{chunk_id}",
            "title": metadata.get("title", "")[:200],
            "source": metadata["source"],
            "pdf_url": metadata.get("pdf_url", ""),
            "chunk_text": chunk_text.strip(),
            "chunk_tokens": len(chunk_tokens),
            "start_token": i,
            "end_token": end
        })
        chunk_id += 1
        i = end - overlap  # перекрытие
        if i >= len(tokens):
            break
    return chunks


def main():
    if not RAW_FILE.exists():
        print(f"Ошибка: не найден {RAW_FILE}")
        print("сначала запустить парсер parse.py")
        return
    all_chunks = []
    print("чтение сырых данных...")
    with open(RAW_FILE, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                article = json.loads(line)
                full_text = ""
                if article.get("title"):
                    full_text += article["title"] + " "
                if article.get("abstract"):
                    full_text += article["abstract"] + " "
                cleaned = clean_text(full_text)
                if len(cleaned) < 100:
                    continue  # слишком короткий
                metadata = {
                    "title": article.get("title", ""),
                    "source": article["source"],
                    "pdf_url": article.get("pdf_url", "")
                }
                chunks = split_into_chunks(cleaned, metadata)
                all_chunks.extend(chunks)
                if line_num % 10 == 0:
                    print(f"Обработано {line_num} статей → {len(all_chunks)} чанков") 
            except json.JSONDecodeError as e:
                print(f"Ошибка JSON в строке {line_num}: {e}")
                continue

    # сохранение файла
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    
    print(f"→ {len(all_chunks)} чанков сохранено в {CHUNKS_FILE}")
    print(f"Средний размер чанка: {sum(c['chunk_tokens'] for c in all_chunks)//len(all_chunks)} токенов")


if __name__ == "__main__":
    main()