import streamlit as st
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import GigaChat 
import json
import os

from settings.config import GIGACHAT_TOKEN, generator_prompt, critic_prompt, qa_prompt
from rag import ask, generate_hypotheses, vectorstore

st.set_page_config(page_title="HypGen", layout="wide")


with open("style.css", "r") as css_file:
    css = css_file.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# заголовок
st.title("HypGen")
st.markdown("<h3 style='color: #ffffff;'>текст текст текст</h3>", unsafe_allow_html=True)
st.markdown("*Здесь могла быть ваша реклама*")




# __________________________________________________________________________________
# система сохранения чатов. не работает 
CHAT_FILE = "chat_history.json"

def init_chat_history():
    if 'chat_history' not in st.session_state:
        if os.path.exists(CHAT_FILE) and os.path.getsize(CHAT_FILE) > 0:
            try:
                with open(CHAT_FILE, "r", encoding="utf-8") as f:
                    st.session_state.chat_history = json.load(f)
            except (json.JSONDecodeError, Exception):
                st.session_state.chat_history = {"chat_1": []}
        else:
            st.session_state.chat_history = {"chat_1": []}
    
    if 'current_chat_id' not in st.session_state:
        if st.session_state.chat_history:
            st.session_state.current_chat_id = next(iter(st.session_state.chat_history))
        else:
            st.session_state.current_chat_id = "chat_1"
            st.session_state.chat_history["chat_1"] = []
    
    # состояние для хранения результатов последней операции
    if 'last_operation' not in st.session_state:
        st.session_state.last_operation = None  
    if 'last_results' not in st.session_state:
        st.session_state.last_results = None    
    if 'last_sources' not in st.session_state:
        st.session_state.last_sources = None    
    if 'last_raw_hypotheses' not in st.session_state:
        st.session_state.last_raw_hypotheses = None  


def save_chat_history():
    try:
        with open(CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump(st.session_state.chat_history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Ошибка сохранения чата: {e}")


def create_new_chat():
    st.session_state.last_operation = None
    st.session_state.last_results = None
    st.session_state.last_sources = None
    st.session_state.last_raw_hypotheses = None
    
    new_id = f"chat_{len(st.session_state.chat_history) + 1}"
    st.session_state.chat_history[new_id] = []
    st.session_state.current_chat_id = new_id
    save_chat_history()


def delete_chat(chat_id):
    if chat_id in st.session_state.chat_history:
        del st.session_state.chat_history[chat_id]
        save_chat_history()

        if st.session_state.current_chat_id == chat_id:
            if st.session_state.chat_history:
                st.session_state.current_chat_id = next(iter(st.session_state.chat_history))
            else:
                create_new_chat()
        
        st.session_state.last_operation = None
        st.session_state.last_results = None
        st.session_state.last_sources = None
        st.session_state.last_raw_hypotheses = None
        return True
    return False
# __________________________________________________________________________________






init_chat_history()

# боковая панель
with st.sidebar:
    st.image("logo.svg", width='stretch')
    
    st.header("✉")
    
    if st.button("✢ Новый чат", width='stretch'):
        create_new_chat()


    #___________________________________________________________________________________________
    chats_to_delete = [] 
    
    if not st.session_state.chat_history:
        st.info("Нет сохранённых чатов")
    else:
        chat_ids = list(st.session_state.chat_history.keys())
        
        for chat_id in chat_ids:
            if chat_id not in st.session_state.chat_history:
                continue
                
            messages = st.session_state.chat_history[chat_id]
            
            if messages:
                first_user_msg = next((m for m in messages if m.get("role") == "user"), None)
                if first_user_msg:
                    chat_name = first_user_msg.get("content", "Чат")[:30]
                    if len(first_user_msg.get("content", "")) > 30:
                        chat_name += "..."
                else:
                    chat_name = "Пустой чат"
            else:
                chat_name = "..."
            
            is_active = chat_id == st.session_state.current_chat_id
            button_style = "primary" if is_active else "secondary"
            
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(
                    chat_name, 
                    key=f"select_{chat_id}_{chat_name}",  
                    width='stretch',
                    type=button_style
                ):
                    st.session_state.current_chat_id = chat_id
                    st.session_state.last_operation = None
                    st.session_state.last_results = None
                    st.session_state.last_sources = None
                    st.session_state.last_raw_hypotheses = None
            with col2:
                if st.button(
                    "✕", 
                    key=f"delete_{chat_id}_{chat_name}",  
                    help="Удалить чат"
                ):
                    chats_to_delete.append(chat_id)
    
    if chats_to_delete:
        for chat_id in chats_to_delete:
            delete_chat(chat_id)
#_____________________________________________________________________________________________


    
    st.markdown("---")
    with st.expander("О системе", expanded=False):
        st.markdown("""
        **HypGen** — интеллектуальный помощник металлурга
        
        - **Генерация гипотез**: GigaChat-Pro
        - **Оспаривание**: GigaChat-Max
        - **База знаний**: 100+ научных статей (Arxiv, OpenaAlex)
        - **Поиск**: FAISS + multilingual-e5-large-instruct
        """)
        st.caption(" ✉ 2025 | Проектный практикум")


tab1, tab2 = st.tabs(["  Генерация гипотез", "  Вопрос-ответ"])

with tab1:
    st.subheader("○ ○ ○")
    problem = st.text_area(
        "   ",
        placeholder="...",
        height=100,
        key="problem_input"
    )
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        generate_btn = st.button("▷ Start", type="primary", key="generate_hypotheses", width='stretch')
    
    if generate_btn and problem:
        if not vectorstore:
            st.error("База знаний не загружена. Пожалуйста, проверьте наличие файлов FAISS индекса.")
        else:
            with st.spinner(" Поиск в базе знаний..."):
                try:
                    docs = vectorstore.similarity_search(problem, k=10)
                    context = "\n\n".join([
                        f"📄 {d.metadata.get('title', 'Без названия')}:\n{d.page_content[:800]}..." 
                        for d in docs
                    ])
                    
                    with st.spinner(" Генерация гипотез..."):
                        inal, raw, docs = generate_hypotheses(problem)
                    
                    with st.spinner(" Оценка гипотез..."):
                        final_response = (CRITIC_PROMPT | critic_llm).invoke({
                            "raw_hypotheses": raw_hypotheses,
                            "context": context
                        })
                        final_hypotheses = final_response.content
                    
                    # сохранение истории чата 
                    st.session_state.chat_history[st.session_state.current_chat_id].append({
                        "role": "user", 
                        "content": f"**Проблема:** {problem}"
                    })
                    st.session_state.chat_history[st.session_state.current_chat_id].append({
                        "role": "assistant", 
                        "content": f"**Сгенерированные гипотезы:**\n\n{final_hypotheses}"
                    })
                    save_chat_history()
                    
                    st.session_state.last_operation = 'generate'
                    st.session_state.last_results = final_hypotheses
                    st.session_state.last_sources = docs[:5]
                    st.session_state.last_raw_hypotheses = raw_hypotheses
                    
                except Exception as e:
                    st.error(f"Ошибка при генерации гипотез: {str(e)}")
                    st.info("Попробуйте переформулировать проблему или проверьте подключение к GigaChat.")

with tab2:
    st.subheader("○ ○ ○")
    question = st.text_area(
        "   ",
        placeholder=". . .",
        height=100,
        key="qa_input"
    )
    
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        qa_btn = st.button("▷ Start", type="primary", key="qa_answer", width='stretch')
    
    if qa_btn and question:
        if not vectorstore:
            st.error("База знаний не загружена. Пожалуйста, проверьте наличие файлов FAISS индекса.")
        else:
            with st.spinner(" Поиск релевантной информации..."):
                try:
                    docs = vectorstore.similarity_search(question, k=5)
                    context = "\n\n".join([
                        f"{d.metadata.get('title', 'Без названия')}:\n{d.page_content[:1000]}..." 
                        for d in docs
                    ])
                    
                    with st.spinner(" Формирование ответа..."):
                        response = (QA_PROMPT | generator_llm).invoke({
                            "context": context, 
                            "question": question
                        })
                        answer = response.content
                    
                    # сохранение истории чата
                    st.session_state.chat_history[st.session_state.current_chat_id].append({
                        "role": "user", 
                        "content": f"**Вопрос:** {question}"
                    })
                    st.session_state.chat_history[st.session_state.current_chat_id].append({
                        "role": "assistant", 
                        "content": f"**Ответ:**\n\n{answer}"
                    })
                    save_chat_history()
                    
                    st.session_state.last_operation = 'qa'
                    st.session_state.last_results = answer
                    st.session_state.last_sources = docs
                    
                except Exception as e:
                    st.error(f"Ошибка при поиске ответа: {str(e)}")
                    st.info("Попробуйте переформулировать вопрос или проверьте подключение к GigaChat.")


if st.session_state.last_operation == 'generate':
    st.success("### Топ-3 гипотезы")
    st.markdown(st.session_state.last_results)
    
    with st.expander("⌕ Исходные гипотезы"):
        st.markdown(st.session_state.last_raw_hypotheses)
    
    with st.expander("☍ Использованные источники"):
        for i, d in enumerate(st.session_state.last_sources, 1):
            st.write(f"**{i}. {d.metadata.get('title', 'Без названия')}**")
            if 'source' in d.metadata:
                st.caption(f"Источник: {d.metadata.get('source', '')}")
            if 'year' in d.metadata:
                st.caption(f"Год: {d.metadata.get('year', '')}")
            st.divider()

elif st.session_state.last_operation == 'qa':
    st.info("### 💡 Ответ")
    st.markdown(st.session_state.last_results)
    
    with st.expander("☍ Использованные источники"):
        for i, d in enumerate(st.session_state.last_sources, 1):
            st.write(f"**{i}. {d.metadata.get('title', 'Без названия')}**")
            if 'source' in d.metadata:
                st.caption(f"Источник: {d.metadata.get('source', '')}")
            if 'year' in d.metadata:
                st.caption(f"Год: {d.metadata.get('year', '')}")
            st.write(f"**Фрагмент:** {d.page_content[:500]}...")
            st.divider()


current_messages = st.session_state.chat_history.get(st.session_state.current_chat_id, []) # показ истории чата в основном окне

if current_messages:
    st.markdown("### ⊲ История чата ⊳")
    for msg in current_messages:
        with st.chat_message(msg.get("role", "user")):
            st.markdown(msg.get("content", ""))

st.markdown("---")
st.caption(" ✉ 2025 | Проектный практикум")











qa_prompt = qa_prompt = """
Ты — ведущий эксперт-металлург с 20-летним опытом работы на промышленных комбинатах и в научных институтах. Ты разбираешься в химии, особенно в химии металлов, в физике, компьютерных науках и программирировании.

КОНТЕКСТ ИЗ НАУЧНЫХ СТАТЕЙ:
{context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ:
{question}

ТВОЯ ЗАДАЧА: Дать максимально полезный ответ для практикующего металлурга, используя информацию из контекста. Не придумывай факты и не выходи за рамки предоставленных данных. Если вопрос выходит за рамки твоих экспертных знаний, если запрос совсем не по теме, честно сообщи об этом пользователю. Предупреди, что  вопрос не в твоей области компетенций. Но все же ответь на такой вопрос, логично, структурно и профессионально, насколько это возможно. 

СТРАТЕГИЯ ОТВЕТА (действуй по порядку):

1. ПРОВЕРЬ КОНТЕКСТ:
   - Если в контексте ЕСТЬ точная и полная информация → используй её как основу ответа
   - Если информация в контексте ЕСТЬ, но неполная/поверхностная → используй как основу, дополни экспертным знанием
   - Если информации в контексте НЕТ/мало → дай экспертный ответ, но честно укажи это

2. СФОРМИРУЙ ОТВЕТ:
   - Ответ должен быть подробным, техническим и полезным для металлурга
   - Приводи конкретные данные, цифры, формулы из контекста
   - Объясняй физико-химические механизмы, если уместно
   - Структурируй ответ логично с подзаголовками и списками, если нужно.

3. ПРОВЕРЬ СВОЙ ОТВЕТ:
   - Проверь, что не добавил выдуманные факты или данные
   - Если не уверен в ответе, честно скажи об этом
   - Проверь тон сообщения: он должен быть профессиональным, уважительным и полезным.
"""
