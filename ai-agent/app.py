import streamlit as st
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import GigaChat 
import os

st.set_page_config(page_title="HypGen :)", layout="wide")
st.title("Test")
st.markdown("**на основе статей ArXiv/OpenAlex**")

# Загрузка индекса
@st.cache_resource
def load_vectorstore():
    try:
        FAISS_DIR = Path("C:/faiss_metal_index")
        embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        return FAISS.load_local(
            FAISS_DIR, 
            embeddings, 
            allow_dangerous_deserialization=True
        )
    except Exception as e:
        st.error(f"Ошибка загрузки базы данных: {e}")
        return None

vectorstore = load_vectorstore()

# Промпты
QA_PROMPT = PromptTemplate.from_template("""
Ты — эксперт-металлург НЛМК. Отвечай строго по контексту.

КОНТЕКСТ: 
{context}

ВОПРОС: 
{question}

ОТВЕТ (будь точным и используй только информацию из контекста):""")

HYPOTHESIS_PROMPT = PromptTemplate.from_template("""
Ты — научный исследователь в металлургии. Сгенерируй 3-5 проверяемых гипотез с конкретными параметрами (%, °C, время).

ПРОБЛЕМА: 
{question}

РЕЛЕВАНТНЫЕ ДАННЫЕ: 
{context}

ГИПОТЕЗЫ (пронумерованный список с механизмами и ожидаемыми параметрами):
1. [Название гипотезы] → [Эффект] + [Механизм] + [Параметры: X%, Y°C, Z мин]
""")

# LLM
@st.cache_resource
def get_llm():
    try:
        return GigaChat(
            credentials="MDE5YTU5MzktOGNmOC03ZWIxLTljOGEtODM1NjQxMDIyNzgxOjI0NzdmM2YzLTI5ZDYtNDZiYi04ZjY3LWM4ODliMjA1YTRlYw==",
            model="GigaChat",
            temperature=0.7,
            verify_ssl_certs=False,
            timeout=30
        )
    except Exception as e:
        st.error(f"Ошибка инициализации GigaChat: {e}")
        return None

llm = get_llm()

# UI
tab1, tab2 = st.tabs(["Генерация гипотез", "Q&A"])

with tab1:
    st.subheader("Генерация научных гипотез")
    problem = st.text_area(
        "Опишите проблему:",
        placeholder="Например: 'Снизить количество неметаллических включений в непрерывнолитой заготовке при выплавке стали'",
        height=100
    )
    
    if st.button("Сгенерировать гипотезы", type="primary") and problem:
        if not llm or not vectorstore:
            st.error("Система не инициализирована. Проверьте подключение к базе данных и GigaChat.")
        else:
            with st.spinner("Поиск релевантных исследований и генерация гипотез..."):
                try:
                    docs = vectorstore.similarity_search(problem, k=8)
                    context = "\n\n".join([
                        f"📄 {d.metadata.get('title', 'Без названия')}:\n{d.page_content[:500]}..." 
                        for d in docs
                    ])
                    
                    chain = HYPOTHESIS_PROMPT | llm
                    response = chain.invoke({"context": context, "question": problem})
                    hypotheses = response.content
                    
                    st.success("### Сгенерированные гипотезы:")
                    st.markdown(hypotheses)
                    
                    with st.expander("Использованные источники (топ-3)"):
                        for i, d in enumerate(docs[:3], 1):
                            st.write(f"{i}. **{d.metadata.get('title', 'Без названия')}**")
                            if 'source' in d.metadata:
                                st.caption(f"Источник: {d.metadata.get('source', '')}")
                            
                except Exception as e:
                    st.error(f"Ошибка при генерации гипотез: {e}")

with tab2:
    st.subheader("Вопрос-ответ по базе знаний")
    question = st.text_input(
        "Задайте вопрос:",
        placeholder="Например: 'Влияние содержания титана на образование оксидных вклющений в стали'"
    )
    
    if st.button("Ответить", type="primary") and question:
        if not llm or not vectorstore:
            st.error("Система не инициализирована. Проверьте подключение к базе данных и GigaChat.")
        else:
            with st.spinner("Поиск ответа в базе знаний..."):
                try:
                    docs = vectorstore.similarity_search(question, k=5)
                    context = "\n\n".join([
                        f"{d.metadata.get('title', 'Без названия')}:\n{d.page_content}" 
                        for d in docs
                    ])
                    
                    chain = QA_PROMPT | llm
                    response = chain.invoke({"context": context, "question": question})
                    answer = response.content
                    
                    st.info("### Ответ:")
                    st.markdown(answer)
                    
                    with st.expander("Источники ответа"):
                        for i, d in enumerate(docs, 1):
                            st.write(f"{i}. **{d.metadata.get('title', 'Без названия')}**")
                            if 'source' in d.metadata:
                                st.caption(f"Источник: {d.metadata.get('source', '')}")
                            st.write(f"Релевантный фрагмент: {d.page_content[:300]}...")
                            st.divider()
                            
                except Exception as e:
                    st.error(f"Ошибка при поиске ответа: {e}")


with st.sidebar:
    st.header("ℹО системе")
    st.markdown("""
    **HypGen** - ии-агент для генерации гипотез и вопросно-ответного поиска 
    по научным публикациям в металлургии.
    
    **База данных:** 90 статей
    **Модель:** GigaChat
    **Поиск:** FAISS + multilingual-e5-large
    
    ### Как использовать:
    1. Введите проблему для генерации гипотез
    2. Задайте вопрос для поиска в базе
    3. Используйте полученные гипотезы для исследований
    """)

st.markdown("---")
st.caption("Прототип: RAG + GigaChat | Металлургические исследования")