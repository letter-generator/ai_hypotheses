import streamlit as st
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import GigaChat 

st.set_page_config(page_title="HypGen :)", layout="wide")
st.title("HypGen. гипотезы + q&a")
st.markdown("**на основе 90 статей (ArXiv/OpenAlex)**")

# Загрузка индекса
@st.cache_resource
def load_vectorstore():
    FAISS_DIR = Path("C:/faiss_metal_index")
    embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
    return FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)

vectorstore = load_vectorstore()

# Промпты
QA_PROMPT = PromptTemplate.from_template("""
Ты — эксперт-металлург НЛМК. Отвечай по контексту.

КОНТЕКСТ: {context}

ВОПРОС: {question}

ОТВЕТ:""")

HYPOTHESIS_PROMPT = PromptTemplate.from_template("""
Сгенерируй 3–5 testable гипотез с параметрами (%, °C).

ПРОБЛЕМА: {question}

ДАННЫЕ: {context}

ГИПОТЕЗЫ (1. [Название] → эффект + механизм):""")

# LLM
@st.cache_resource
def get_llm():
    return GigaChat(
        credentials="MDE5YTU5MzktOGNmOC03ZWIxLTljOGEtODM1NjQxMDIyNzgxOjI0NzdmM2YzLTI5ZDYtNDZiYi04ZjY3LWM4ODliMjA1YTRlYw==",
        model="GigaChat",
        temperature=0.7,
        verify_ssl_certs=False
    )

llm = get_llm()

# UI
tab1, tab2 = st.tabs(["Генерация гипотез", "Q&A"])

with tab1:
    problem = st.text_input("Проблема (например, 'Снизить включения в НЛЗ при выплавке стали')")
    if st.button("Сгенерировать гипотезы", type="primary") and problem:
        with st.spinner("Генерирую..."):
            docs = vectorstore.similarity_search(problem, k=8)
            context = "\n\n".join([f"Источник: {d.metadata.get('title','?')}\n{d.page_content}" for d in docs])
            chain = HYPOTHESIS_PROMPT | llm
            hypotheses = chain.invoke({"context": context, "question": problem}).content
        st.success("**Гипотезы:**")
        st.markdown(hypotheses)
        st.markdown("**Источники:**")
        for d in docs[:3]:
            st.write(f"• {d.metadata.get('title', '?')} ({d.metadata.get('source', '')})")

with tab2:
    question = st.text_input("Вопрос (например, 'Влияние титана на включения')")
    if st.button("Ответить", type="primary") and question:
        with st.spinner("Ищу в базе..."):
            docs = vectorstore.similarity_search(question, k=5)
            context = "\n\n".join([f"Источник: {d.metadata.get('title','?')}\n{d.page_content}" for d in docs])
            chain = QA_PROMPT | llm
            answer = chain.invoke({"context": context, "question": question}).content
        st.info(answer)
        st.markdown("**Источники:**")
        for d in docs:
            st.write(f"• {d.metadata.get('title', '?')} ({d.metadata.get('source', '')})")

st.markdown("---")
st.caption("Прототип: RAG + GigaChat.")