import faiss
import numpy as np
import jsonlines
import logging
from pathlib import Path
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
VECTORS_DIR = project_root / "data" / "vectors"
FAISS_DIR = project_root / "data" / "faiss"


class FAISSIndexBuilder:
    def __init__(self):
        self.index = None
        self.metadata = []
    
    def load_embeddings_and_metadata(self):
        embeddings_path = VECTORS_DIR / "embeddings.npy"
        metadata_path = VECTORS_DIR / "metadata.jsonl"
        
        if not embeddings_path.exists():
            raise FileNotFoundError(f"Файл эмбеддингов не найден: {embeddings_path}")
        if not metadata_path.exists():
            raise FileNotFoundError(f"Файл метаданных не найден: {metadata_path}")
        
        embeddings = np.load(embeddings_path)
        
        metadata = []
        with jsonlines.open(metadata_path, 'r') as reader:
            for item in reader:
                metadata.append(item)
                
        return embeddings, metadata
    
    def build_index(self, index_type: str = "FlatL2"):
        embeddings, metadata = self.load_embeddings_and_metadata()
        self.metadata = metadata
        
        # Нормализация не обязательна, но улучшит стабильность
        faiss.normalize_L2(embeddings)
        
        dimension = embeddings.shape[1]
        num_vectors = len(embeddings)
        
        if index_type == "FlatL2":
            index = faiss.IndexFlatL2(dimension)
        elif index_type == "HNSW" and num_vectors > 1000:
            index = faiss.IndexHNSWFlat(dimension, 32)
            index.hnsw.efConstruction = 200
        elif index_type == "IVF" and num_vectors > 10000:
            nlist = min(100, num_vectors // 39)
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)
        else:
            index = faiss.IndexFlatL2(dimension)
        
        # Обучение (при необходимости)
        if hasattr(index, 'is_trained') and not index.is_trained:
            index.train(embeddings)
        
        index.add(embeddings)
        self.index = index
        
        return index
    
    def save_index(self):
        if self.index is None:
            raise ValueError("Индекс не построен")
        
        FAISS_DIR.mkdir(parents=True, exist_ok=True)
        
        index_path = FAISS_DIR / "metal_knowledge.index"
        
        try:
            faiss.write_index(self.index, str(index_path))
            logger.info("FAISS-индекс сохранен")
        except Exception as e:
            logger.error(f"Ошибка сохранения индекса: {e}")
            self._save_index_alternative(str(index_path))


        '''info = {
            "dimension": self.index.d,
            "total_vectors": self.index.ntotal,
        }
        info_path = FAISS_DIR / "faiss_info.json"
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)'''
        

        return str(index_path)
    
    def _save_index_alternative(self, index_path):
        # Альтернативное сохранение индекса
        try:
            temp_path = "temp_metal_knowledge.index"
            faiss.write_index(self.index, temp_path)
            
            import shutil
            shutil.copy(temp_path, index_path)
            
            Path(temp_path).unlink()
            logger.info("Индекс сохранен альтернативным способом")
        except Exception as e:
            logger.error(f"Альтернативное сохранение индекса не удалось: {e}")
            raise
    
    def search(self, query_text: str, k: int = 5):
        if self.index is None:
            logger.error("Индекс не построен")
            return
        
        if not query_text or not query_text.strip():
            logger.error("Не указан текст запроса для поиска")
            return None
        
        query_embedding = self.model.encode([query_text])
        faiss.normalize_L2(query_embedding)
        
        # Поиск в FAISS
        distances, indices = self.index.search(query_embedding, k)
        
        valid_results = 0
        for idx in indices[0]:
            if 0 <= idx < len(self.metadata):
                valid_results += 1
        
        if valid_results == 0:
            logger.warning("Не найдено ни одного результата")
            return None
        
        return distances, indices

def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--index-type', '-t', default='FlatL2', choices=['FlatL2', 'HNSW', 'IVF'])
    parser.add_argument('--test-search', '-s', action='store_true')
    parser.add_argument('--k', type=int, default=5)
    
    args = parser.parse_args()
    
    try:
        builder = FAISSIndexBuilder()
        builder.build_index(index_type=args.index_type)
        builder.save_index()
        
        if args.test_search:
            builder.test_search(k=args.k)
            
    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise


if __name__ == "__main__":
    main()