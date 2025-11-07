import os
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_community.chat_models import GigaChat
from langchain_core.prompts import PromptTemplate
from typing import List


# Тестовые документы
TEST_DOCS = [
    "Сталь — это сплав железа с углеродом (до 2,14 %). Основные свойства: прочность, пластичность, коррозионная стойкость. "
    "Для повышения коррозионной стойкости добавляют хром (нержавеющая сталь).",

    "Чугун получают в доменной печи из железной руды, кокса и известняка. Содержание углерода в чугуне — 2,14–6,67 %. "
    "Чугун хрупок, но дешев в производстве.",

    "Алюминий — легкий металл, плотность 2,7 г/см³. Используется в авиации и упаковке. "
    "Электролизом получают из боксита по процессу Холла-Эру.",

    "Титан обладает высокой удельной прочностью и коррозионной стойкостью. "
    "Применяется в аэрокосмической отрасли и медицине (импланты). "
    "Добывается из ильменита и рутила.",

    "Медь — отличный проводник электричества. Применяется в электротехнике, сантехнике. "
    "Основные месторождения: Чили, Перу, Россия."
]

def create_vectorstore(docs: List[str] = TEST_DOCS) -> FAISS:
    documents = [Document(page_content=text) for text in docs]
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_documents(documents, embeddings)

# ЯВНЫЙ ПРОМПТ
RAG_PROMPT = """Ты — эксперт по металлургии. Отвечай ТОЛЬКО на основе предоставленного контекста.
Если в контексте нет ответа — скажи "Информация отсутствует в базе знаний".

Контекст:
{context}

Вопрос: {question}

Ответ:"""

def answer_question(question: str, vectorstore: FAISS | None = None, gigachat_token: str | None = None) -> dict:
    if not gigachat_token:
        raise ValueError("Токен GigaChat обязателен")

    vs = vectorstore or create_vectorstore()

    # 1. Поиск релевантных документов
    docs = vs.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    # 2. LLM
    llm = GigaChat(
        credentials=gigachat_token,
        model="GigaChat",
        temperature=0.1,
        verify_ssl_certs=False
    )

    # 3. Явный промпт + прямой вызов
    prompt = PromptTemplate.from_template(RAG_PROMPT)
    chain = prompt | llm

    response = chain.invoke({
        "context": context,
        "question": question
    })

    return {
        "answer": response.content,
        "sources": [doc.page_content for doc in docs]
    }
