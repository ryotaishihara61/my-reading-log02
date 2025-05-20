import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt

st.set_page_config(page_title="📚 読書記録", layout="wide")

# Google Sheets 認証
def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    return sheet

# データ取得とDataFrame変換
sheet = get_worksheet()
data = sheet.get_all_records()
df = pd.DataFrame(data)

# UI - タイトル
st.title("📚 読書記録一覧")

# 検索・絞り込み
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    keyword = st.text_input("🔍 タイトルや著者で検索")
with col2:
    rating_filter = st.selectbox("⭐ 評価で絞り込み", options=["すべて", "★5", "★4以上", "★3以上", "★2以上", "★1以上"])
with col3:
    month_filter = st.selectbox("📅 年月で絞り込み", options=["すべて"] + sorted(df["読了日"].str[:7].unique()))

# フィルター処理
filtered_df = df.copy()

if keyword:
    filtered_df = filtered_df[
        filtered_df["タイトル"].str.contains(keyword, case=False, na=False) |
        filtered_df["著者"].str.contains(keyword, case=False, na=False)
    ]

if rating_filter != "すべて":
    threshold = int(rating_filter[1])
    filtered_df = filtered_df[filtered_df["評価"] >= threshold]

if month_filter != "すべて":
    filtered_df = filtered_df[filtered_df["読了日"].str.startswith(month_filter)]

# 表示
for _, row in filtered_df.iterrows():
    with st.container():
        cols = st.columns([1, 5])
        with cols[0]:
            if row["表紙画像"]:
                st.image(row["表紙画像"], width=100)
            else:
                st.image("no-image.png", width=100)
        with cols[1]:
            st.subheader(row["タイトル"])
            st.caption(f"著者: {row['著者']} / 読了日: {row['読了日']}")
            st.markdown("⭐" * int(row["評価"]))
            if row["メモ"]:
                st.markdown(f"✏️ {row['メモ']}")

# 📊 グラフ
st.markdown("---")
st.subheader("📊 月別読了数")

if not df.empty:
    df["読了月"] = df["読了日"].str[:7]
    monthly_counts = df["読了月"].value_counts().sort_index()
    fig, ax = plt.subplots()
    monthly_counts.plot(kind="bar", ax=ax)
    ax.set_xlabel("年月")
    ax.set_ylabel("読了冊数")
    ax.set_title("月別読了数")
    st.pyplot(fig)
