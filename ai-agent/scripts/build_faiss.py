import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


FAISS_DIR = Path("C:\\PROJECT\\ai-agent\\faiss_index")  # !тут были проблемы с onedrive. потом поменять на директорию проекта
FAISS_DIR.mkdir(exist_ok=True)


CHUNKS_FILE = Path("C:\\PROJECT\\ai-agent\\data\\clean.jsonl")

if not CHUNKS_FILE.exists():
    print(f"Не найден: {CHUNKS_FILE}")
    exit()

print("загрузка модели эмбеддингов multilingual-e5-large-instruct...")
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large-instruct",
    model_kwargs={'device': 'cpu'}
)

print("загрузка чанков...")
docs = []
skipped_short = 0
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if len(data["chunk_text"].strip()) < 200:
                skipped_short += 1
                continue
            docs.append(Document(
                page_content=data["chunk_text"],   
                metadata={
                    "title": data.get("title", "Без названия"),
                    "source": data.get("source", ""),
                    "pdf_url": data.get("pdf_url", ""),
                    "chunk_id": data.get("chunk_id", f"chunk_{i}"),
                    "country": data.get("country", "Не определено"),
                    "year": data.get("year", "Не определено")
                }
            ))
            if i % 50 == 0:
                print(f"   загружено {i} чанков...")
        except json.JSONDecodeError as e:
            print(f"Ошибка JSON в строке {i}: {e}")
            continue
        except KeyError as e:
            print(f"Отсутствует поле {e} в строке {i}")
            continue
print(f"Всего загружено {len(docs)} чанков")
print(f"Пропущено (короче 200 символов): {skipped_short}")

print("создание FAISS-индекса ...")
vectorstore = FAISS.from_documents(docs, embeddings)
vectorstore.save_local(FAISS_DIR)

print(f"\nвсё готово")
print(f"индекс здесь: {FAISS_DIR}")

"""
# Тестовый поиск
print("\nТестовый поиск по запросу «титан и неметаллические включения»:")
results = vectorstore.similarity_search("титан и неметаллические включения", k=3)
for i, doc in enumerate(results, 1):
    print(f"\n{i}. {doc.metadata.get('title', 'Без названия')[:100]}")
    print(f"   Страна: {doc.metadata.get('country')}, Год: {doc.metadata.get('year')}")
    print(doc.page_content[:400] + "...")
"""
