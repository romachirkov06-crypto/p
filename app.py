import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO
import time
import os

# ==========================================
# 1. НАСТРОЙКА СТРАНИЦЫ И КАСТОМНЫЙ CSS
# ==========================================
st.set_page_config(
    page_title="Опрос: Цифровые привычки перед сном",
    page_icon="🌙",
    layout="wide"
)

st.markdown("""
<style>
    /* Фиолетовый градиент заголовка */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white !important;
        text-align: center;
        margin-bottom: 2rem;
    }
    .main-header h1, .main-header p {
        color: white !important;
    }
    
    /* Красивые карточки — работает в обеих темах */
    [data-testid="stForm"] {
        background: linear-gradient(145deg, #f3e7ff 0%, #e9d5ff 100%);
        border-radius: 1rem;
        padding: 1rem;
        border: 2px solid #c084fc;
    }
    [data-testid="stForm"] label, [data-testid="stForm"] span {
        color: #4c1d95 !important;
    }
    
    /* Кнопка отправки */
    .stButton>button {
        background: linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%) !important;
        color: white !important;
        border-radius: 0.8rem !important;
        border: none !important;
        padding: 0.8rem 2rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(139, 92, 246, 0.4) !important;
    }
    
    /* Слайдеры фиолетовые */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background-color: #8b5cf6 !important;
    }
    
    /* Успешное сообщение */
    .stSuccess {
        background: linear-gradient(135deg, #d8b4fe 0%, #c084fc 100%) !important;
        border: 2px solid #a855f7 !important;
        border-radius: 1rem !important;
    }
    .stSuccess p {
        color: #4c1d95 !important;
    }
    
    /* Метрики */
    [data-testid="stMetricValue"] {
        color: #7c3aed !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricLabel"] {
        color: #6b21a8 !important;
    }
    
    /* Разделитель */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #c084fc, #8b5cf6, #c084fc);
        margin: 2rem 0;
    }
    
    /* Dataframe */
    .stDataFrame {
        border: 1px solid #c084fc !important;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. ИНИЦИАЛИЗАЦИЯ FIREBASE
# ==========================================
if not firebase_admin._apps:
    try:
        if os.path.exists("key.json"):
            # Для локального запуска
            cred = credentials.Certificate("key.json")
        else:
            # Для Streamlit Cloud
            firebase_config = st.secrets["firebase_key"]
            cred = credentials.Certificate(dict(firebase_config))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Ошибка инициализации Firebase: {e}")
        st.stop()

db = firestore.client()

# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🌙 Цифровые привычки перед сном</h1>
    <p style="opacity: 0.9; margin-top: 0.5rem;">
        Анонимный опрос о влиянии экранов, синего света и контента на качество сна
    </p>
</div>
""", unsafe_allow_html=True)

# Счётчик ответов
try:
    count = len(list(db.collection("sleep_survey_responses").stream()))
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem;">
        <span style="
            background: linear-gradient(135deg, #8b5cf6, #a855f7);
            color: white;
            padding: 0.4rem 1.2rem;
            border-radius: 2rem;
            font-size: 0.9rem;
            font-weight: 600;
        ">
            Уже собрано ответов: {count}
        </span>
    </div>
    """, unsafe_allow_html=True)
except:
    pass

# ==========================================
# 3. ФОРМА ОПРОСА
# ==========================================
with st.form("survey_form"):
    st.subheader("Заполните форму")
    
    col1, col2 = st.columns(2)
    
    with col1:
        age = st.number_input("Ваш возраст", min_value=14, max_value=80, step=1, value=18)
        gender = st.radio("Пол", ["Мужской", "Женский", "Предпочитаю не указывать"])
        occupation = st.selectbox(
            "Ваш основной род деятельности",
            ["Школьник", "Студент", "Работающий", "Работающий студент", "Другое"]
        )
        sleep_duration = st.selectbox(
            "Сколько часов в сутки вы обычно спите?",
            ["Менее 5 часов", "5-6 часов", "6-7 часов", "7-8 часов", "Более 8 часов"]
        )
    
    with col2:
        screen_time = st.slider(
            "Сколько времени вы проводите у экрана за 1 час до сна? (в минутах)",
            0, 180, 60, step=10
        )
        blue_light_filter = st.radio(
            "Используете ли вы фильтр синего света (ночной режим) на устройствах?",
            ["Да, всегда", "Иногда", "Нет, никогда"]
        )
        content_type = st.multiselect(
            "Какой контент вы чаще всего потребляете перед сном?",
            ["Социальные сети", "Видео (YouTube/TikTok)", "Мессенджеры", "Новости", 
             "Игры", "Книги/Статьи", "Подкасты/Музыка", "Работа/Учеба"]
        )
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    with col3:
        sleep_quality = st.slider(
            "Оцените качество вашего сна в среднем (1 — очень плохое, 10 — отличное)",
            1, 10, 5
        )
    with col4:
        fatigue_level = st.slider(
            "Как часто вы чувствуете усталость утром? (1 — никогда, 10 — постоянно)",
            1, 10, 5
        )
        
    feeling_after_screen = st.radio(
        "Как вы обычно чувствуете себя после использования гаджетов перед сном?",
        ["Расслабленным", "Взбудораженным/тревожным", "Сонным", "Никак не влияет"]
    )
    
    comment = st.text_area(
        "Дополнительные комментарии (по желанию)",
        placeholder="Поделитесь своим опытом борьбы с экранным временем перед сном..."
    )
    
    submitted = st.form_submit_button("🌙 Отправить ответ", use_container_width=True)

# ==========================================
# 4. СОХРАНЕНИЕ ДАННЫХ
# ==========================================
if submitted:
    doc_data = {
        "age": int(age),
        "gender": gender,
        "occupation": occupation,
        "sleep_duration": sleep_duration,
        "screen_time_min": int(screen_time),
        "blue_light_filter": blue_light_filter,
        "content_type": content_type,
        "sleep_quality": int(sleep_quality),
        "fatigue_level": int(fatigue_level),
        "feeling_after_screen": feeling_after_screen,
        "comment": comment,
        "timestamp": datetime.utcnow()
    }
    
    try:
        db.collection("sleep_survey_responses").add(doc_data)
        st.success("✅ Спасибо! Ваш ответ сохранён в облачной базе данных.")
        
        # Анимация
        st.balloons()
        
        # Благодарственная карточка
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f3e7ff, #e9d5ff);
            border-radius: 1rem;
            padding: 1.5rem;
            border-left: 5px solid #8b5cf6;
            margin-top: 1rem;
        ">
            <h3 style="color: #7c3aed; margin: 0;">🌙 Спасибо за участие!</h3>
            <p style="color: #6b21a8; margin: 0.5rem 0 0 0;">
                Ваши ответы помогают понять, как цифровые технологии влияют на наш сон.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Ошибка при сохранении: {e}")

# ==========================================
# 5. АНАЛИТИЧЕСКАЯ ПАНЕЛЬ
# ==========================================
st.markdown("---")
st.subheader("📊 Панель аналитики")

if st.checkbox("🔍 Показать аналитику", value=False):
    docs = db.collection("sleep_survey_responses").stream()
    data = [doc.to_dict() for doc in docs]
    
    if not data:
        st.info("📭 Пока нет собранных данных.")
    else:
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Сводка
        st.subheader("📌 Сводка данных")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Среднее качество сна", f"{df['sleep_quality'].mean():.1f}/10")
        with col_b:
            st.metric("Средняя усталость утром", f"{df['fatigue_level'].mean():.1f}/10")
        with col_c:
            st.metric("Ср. экранное время (мин)", f"{df['screen_time_min'].mean():.0f}")
            
        st.dataframe(df.head(20), use_container_width=True)
        
        # Визуализации
        st.subheader("📈 Визуализация результатов")
        col_v1, col_v2 = st.columns(2)
        
        with col_v1:
            fig_quality = px.histogram(
                df, x="sleep_quality", nbins=10,
                title="Распределение качества сна",
                labels={"sleep_quality": "Оценка качества сна (1–10)", "count": "Количество"},
                color_discrete_sequence=["#8b5cf6"]
            )
            fig_quality.update_layout(bargap=0.1)
            st.plotly_chart(fig_quality, use_container_width=True)
            
        with col_v2:
            fig_screen = px.scatter(
                df, x="screen_time_min", y="sleep_quality",
                title="Влияние экранного времени на качество сна",
                labels={"screen_time_min": "Экранное время (мин)", "sleep_quality": "Качество сна"},
                color="fatigue_level",
                color_continuous_scale="Purples"
            )
            st.plotly_chart(fig_screen, use_container_width=True)

        # Контент
        st.subheader("📱 Потребляемый контент перед сном")
        content_list = []
        for items in df["content_type"].dropna():
            content_list.extend(items)
        
        if content_list:
            content_df = pd.DataFrame(content_list, columns=["Контент"])
            content_counts = content_df["Контент"].value_counts().reset_index()
            content_counts.columns = ["Тип контента", "Количество"]
            
            fig_content = px.bar(
                content_counts, x="Количество", y="Тип контента", orientation='h',
                title="Популярность контента перед сном",
                color="Количество", color_continuous_scale="Purples"
            )
            st.plotly_chart(fig_content, use_container_width=True)

        # Динамика
        st.subheader("📅 Динамика поступления ответов")
        df["date"] = df["timestamp"].dt.date
        daily = df.groupby("date").size().reset_index(name="Количество")
        fig_time = px.line(
            daily, x="date", y="Количество",
            title="Количество ответов по дням", markers=True,
            color_discrete_sequence=["#a855f7"]
        )
        st.plotly_chart(fig_time, use_container_width=True)

        # Комментарии
        st.subheader("💬 Комментарии респондентов")
        comments = df[df["comment"].str.strip() != ""]["comment"].dropna().tolist()
        if comments:
            for i, c in enumerate(comments[:10], 1):
                with st.expander(f"Комментарий #{i}"):
                    st.write(c)
        else:
            st.info("Комментариев пока нет.")

        # ==========================================
        # 6. ЭКСПОРТ ДАННЫХ
        # ==========================================
        st.markdown("---")
        st.subheader("💾 Экспорт данных")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            csv_buffer = BytesIO()
            df_export = df.copy()
            
            if 'timestamp' in df_export.columns:
                df_export['timestamp'] = df_export['timestamp'].astype(str)
            if 'date' in df_export.columns:
                df_export['date'] = df_export['date'].astype(str)
            if 'content_type' in df_export.columns:
                df_export['content_type'] = df_export['content_type'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else x
                )
                
            df_export.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_buffer.seek(0)
            
            st.download_button(
                label="📥 Скачать CSV",
                data=csv_buffer,
                file_name=f"sleep_survey_results_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with export_col2:
            excel_buffer = BytesIO()
            df_excel = df.copy()
            
            if 'timestamp' in df_excel.columns:
                df_excel['timestamp'] = df_excel['timestamp'].astype(str)
            if 'date' in df_excel.columns:
                df_excel['date'] = df_excel['date'].astype(str)
            if 'content_type' in df_excel.columns:
                df_excel['content_type'] = df_excel['content_type'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else x
                )
                
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_excel.to_excel(writer, sheet_name='Ответы', index=False)
                
                summary_data = {
                    'Метрика': ['Всего ответов', 'Среднее качество сна', 'Средняя усталость', 'Ср. экранное время (мин)'],
                    'Значение': [
                        len(df),
                        f"{df['sleep_quality'].mean():.2f}",
                        f"{df['fatigue_level'].mean():.2f}",
                        f"{df['screen_time_min'].mean():.2f}"
                    ]
                }
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Сводка', index=False)
                
                occ_summary = df['occupation'].value_counts().reset_index()
                occ_summary.columns = ['Род деятельности', 'Количество']
                occ_summary.to_excel(writer, sheet_name='Деятельность', index=False)
                
            excel_buffer.seek(0)
            
            st.download_button(
                label="📥 Скачать Excel",
                data=excel_buffer,
                file_name=f"sleep_survey_results_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
