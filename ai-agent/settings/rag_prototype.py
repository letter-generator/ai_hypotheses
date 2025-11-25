import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import GigaChat 

# Путь к индексу
FAISS_DIR = Path("C:\\PROJECT\\ai-agent\\faiss_index")

print("Загружаем индекс...")
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
vectorstore = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
print("Индекс загружен!")

# Промпты
QA_PROMPT = PromptTemplate.from_template("""
Ты — эксперт-металлург. Отвечай строго по контексту.

КОНТЕКСТ:
{context}

ВОПРОС: {question}

ОТВЕТ:""")

HYPOTHESIS_PROMPT = PromptTemplate.from_template("""
На основе научных данных предложи 3–5 проверяемых гипотез с количественными параметрами.

ПРОБЛЕМА: {question}

ДАННЫЕ:
{context}

ГИПОТЕЗЫ (формат: 1. [Название] → эффект + механизм):""")

def ask(question: str):
    docs = vectorstore.similarity_search(question, k=5)
    context = "\n\n".join([f"Источник: {d.metadata.get('title','?')}\n{d.page_content}" for d in docs])
    llm = GigaChat(
        credentials="MDE5YTU5MzktOGNmOC03ZWIxLTljOGEtODM1NjQxMDIyNzgxOjI0NzdmM2YzLTI5ZDYtNDZiYi04ZjY3LWM4ODliMjA1YTRlYw==",
        model="GigaChat",
        temperature=0.1,
        verify_ssl_certs=False
    )
    return (QA_PROMPT | llm).invoke({"context": context, "question": question}).content

def generate_hypotheses(problem: str):
    docs = vectorstore.similarity_search(problem, k=8)
    context = "\n\n".join([f"Источник: {d.metadata.get('title','?')}\n{d.page_content}" for d in docs])
    llm = GigaChat(
        credentials="MDE5YTU5MzktOGNmOC03ZWIxLTljOGEtODM1NjQxMDIyNzgxOjI0NzdmM2YzLTI5ZDYtNDZiYi04ZjY3LWM4ODliMjA1YTRlYw==",
        model="GigaChat",
        temperature=0.7,
        verify_ssl_certs=False
    )
    return (HYPOTHESIS_PROMPT | llm).invoke({"context": context, "question": problem}).content

if __name__ == "__main__":
    print("\n" + "="*80)
    print("ТЕСТ: Влияние титана")
    print(ask("Как титан влияет на неметаллические включения в стали?"))

    print("\n" + "="*80)
    print("ГИПОТЕЗЫ")
    print(generate_hypotheses("Как снизить неметаллические включения в НЛЗ при выплавке стали?"))