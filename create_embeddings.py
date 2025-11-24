import numpy as np
import jsonlines
import logging
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
CLEAN_DATA_PATH = project_root / "data" / "clean" / "clean_articles.jsonl"
VECTORS_DIR = project_root / "data" / "vectors"
LOCAL_MODEL_PATH = project_root / "all-MiniLM-L6-v2"

class EmbeddingGenerator:
    def __init__(self):
        self.model = None
        self.embeddings = None
        self.metadata = []
    
    def load_local_model(self):
        if not LOCAL_MODEL_PATH.exists():
            raise FileNotFoundError(f"Локальная модель не найдена: {LOCAL_MODEL_PATH}")
        
        try:
            self.model = SentenceTransformer(str(LOCAL_MODEL_PATH))
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки локальной модели: {e}")
            return False
    
    def load_clean_articles(self):
        if not CLEAN_DATA_PATH.exists():
            raise FileNotFoundError(f"Файл не найден: {CLEAN_DATA_PATH}")
        
        articles = []
        with jsonlines.open(CLEAN_DATA_PATH, 'r') as reader:
            for article in reader:
                articles.append(article)
        
        return articles
    
    def prepare_texts(self, articles):
        texts_for_embedding = []
        processed_metadata = []
        
        for i, article in enumerate(articles):
            text_parts = []
            if article.get('title'):
                text_parts.append(article['title'])
            if article.get('abstract'):
                text_parts.append(article['abstract'])
            if article.get('text'):
                text_parts.append(article['text'])
            
            # Создание метаданных
            if text_parts:
                full_text = ' '.join(text_parts)
                texts_for_embedding.append(full_text)
                
                metadata_entry = {
                    "id": article.get("id", f"article_{i}"),
                    "original_id": article.get("original_id", ""),
                    "title": article.get("title", ""),
                    "embedding_index": i,
                    "text_length": len(full_text)
                }
                for key in ["authors", "year", "journal", "url", "chunk_index"]:
                    if key in article:
                        metadata_entry[key] = article[key]
                
                processed_metadata.append(metadata_entry)
            else:
                texts_for_embedding.append("")
                processed_metadata.append({
                    "id": article.get("id", f"article_{i}"),
                    "embedding_index": i,
                    "title": "Текст отсутствует",
                    "text_length": 0
                })
        
        return texts_for_embedding, processed_metadata
    
    def generate_embeddings(self):
        if not self.load_local_model():
            raise RuntimeError("Не удалось загрузить локальную модель")
        
        articles = self.load_clean_articles()
        
        texts, metadata = self.prepare_texts(articles)
        self.metadata = metadata
        
        self.embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=16
        )
        
        return self.embeddings, self.metadata
    
    def save_results(self):
        if self.embeddings is None:
            raise ValueError("Эмбеддинги не сгенерированы")
        
        VECTORS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Сохранение эмбеддингов
        embeddings_path = VECTORS_DIR / "embeddings.npy"
        np.save(embeddings_path, self.embeddings)
        
        # Сохранение метаданных
        metadata_path = VECTORS_DIR / "metadata.jsonl"
        with jsonlines.open(metadata_path, 'w') as writer:
            for item in self.metadata:
                writer.write(item)
        
        logger.info("Эмбеддинги сгенерированы")

def main():
    try:
        generator = EmbeddingGenerator()
        generator.generate_embeddings()
        generator.save_results()
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise

if __name__ == "__main__":
    main()