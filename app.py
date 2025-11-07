import streamlit as st
from rag_prototype import answer_question, create_vectorstore, TEST_DOCS
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="RAG по металлургии — GigaChat", layout="centered")
st.title("RAG + Гипотезы (GigaChat)")

# Ключ
gigachat_key = st.sidebar.text_input(
    "GigaChat API Key",
    type="password",
    value=os.getenv("GIGACHAT_API_KEY", "")
)

if "vectorstore" not in st.session_state:
    with st.spinner("Создаём базу знаний..."):
        st.session_state.vectorstore = create_vectorstore(TEST_DOCS)


question = st.text_area(
    "Введите ваш вопрос по металлургии",
    height=120,
    placeholder="Например: Что такое нержавеющая сталь? Как получают алюминий?"
)

if st.button("Ответить") and gigachat_key:
    with st.spinner("Ищу в документах..."):
        resp = answer_question(
            question=question,
            vectorstore=st.session_state.vectorstore,
            gigachat_token=gigachat_key
        )
    
    st.success("Ответ из базы знаний:")
    st.write(resp["answer"])
    
    with st.expander("Источники (3 документа):"):
        for i, src in enumerate(resp["sources"], 1):
            st.caption(f"{i}. {src}")





















"""

# app.py
import os
import streamlit as st
from rag_prototype import answer_question, create_vectorstore, TEST_DOCS
from dotenv import load_dotenv

load_dotenv()  # загружает .env

st.title("RAG по металлургии — GigaChat")

# Ключ
gigachat_key = st.sidebar.text_input("GigaChat API Key", type="password", value=os.getenv("GIGACHAT_API_KEY", ""))

if "vectorstore" not in st.session_state:
    with st.spinner("Создаём векторную БД..."):
        st.session_state.vectorstore = create_vectorstore(TEST_DOCS)

question = st.text_area("Задайте вопрос", height=100)
if st.button("Ответить") and question and gigachat_key:
    with st.spinner("GigaChat думает..."):
        resp = answer_question(question, st.session_state.vectorstore, gigachat_key)
    st.success("Ответ:")
    st.write(resp["answer"])
    with st.expander("Источники"):
        for i, src in enumerate(resp["sources"], 1):
            st.caption(f"{i}. {src}")
else:
    if not gigachat_key:
        st.warning("Вставьте GigaChat API ключ в боковую панель.")

"""






















"""
import streamlit as st
import os
from rag_prototype import answer_question, create_vectorstore, TEST_DOCS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# -------------------------------
# Конфигурация
# -------------------------------
st.set_page_config(page_title="RAG + Hypothesis Tester", layout="centered")
st.title("🧪 RAG-прототип + Генерация гипотез")

# API-ключ
api_key = st.sidebar.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key

mode = st.sidebar.radio("Режим работы", ["RAG (FAISS)", "Простая генерация гипотез"])

# -------------------------------
# 1. RAG-режим
# -------------------------------
if mode == "RAG (FAISS)":
    if "vectorstore" not in st.session_state:
        with st.spinner("Создаём векторную БД..."):
            st.session_state.vectorstore = create_vectorstore(TEST_DOCS)

    problem = st.text_area("Введите проблему / вопрос", height=120)
    if st.button("Сгенерировать ответ"):
        if not problem.strip():
            st.warning("Введите вопрос.")
        elif not api_key:
            st.error("Укажите OpenAI API Key.")
        else:
            with st.spinner("Ищем в базе..."):
                resp = answer_question(problem, st.session_state.vectorstore, api_key)
            st.success("Ответ готов")
            st.write("**Ответ:**")
            st.write(resp["answer"])
            with st.expander("Источники"):
                for i, src in enumerate(resp["sources"], 1):
                    st.caption(f"Источник {i}: {src}")

# -------------------------------
# 2. Режим генерации гипотез (простой prompt)
# -------------------------------
else:
    problem = st.text_area("Введите проблему", height=120)
    if st.button("Сгенерировать гипотезы"):
        if not problem.strip():
            st.warning("Введите проблему.")
        elif not api_key:
            st.error("Укажите OpenAI API Key.")
        else:
            with st.spinner("Генерируем гипотезы..."):
                llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=api_key)
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "Ты — эксперт-аналитик. На основе описанной проблемы предложи 3–5 научных гипотез, которые можно проверить экспериментально. Формат: нумерованный список."),
                    ("human", "{problem}")
                ])
                chain = prompt | llm
                response = chain.invoke({"problem": problem})
            st.success("Гипотезы готовы")
            st.write(response.content)

"""