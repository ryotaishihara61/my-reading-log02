import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
import pandas as pd

# Google Sheets に接続する関数
def get_worksheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # secrets.toml に記載されたサービスアカウント情報を読み込む
    service_account_info = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    return sheet

# データを読み込む関数
def load_data():
    sheet = get_worksheet()
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    return df

# Streamlit UI
st.title("📚 読書記録アプリ")

# データ読み込み
try:
    df = load_data()
except Exception as e:
    st.error(f"読み込みエラー: {e}")
    st.stop()

# 検索・フィルター
search_query = st.text_input("🔍 タイトルや著者で検索")
rating_filter = st.selectbox("⭐ 評価で絞り込み", options=[0, 1, 2, 3, 4, 5], format_func=lambda x: f"★{x}以上" if x else "すべて")
month_filter = st.selectbox("📅 年月で絞り込み", options=["すべて"] + sorted(df["date"].str[:7].unique()))

# フィルター処理
filtered_df = df.copy()
if search_query:
    search_query = search_query.lower()
    filtered_df = filtered_df[
        filtered_df["title"].str.lower().str.contains(search_query) |
        filtered_df["author"].str.lower().str.contains(search_query)
    ]
if rating_filter:
    filtered_df = filtered_df[filtered_df["rating"] >= rating_filter]
if month_filter != "すべて":
    filtered_df = filtered_df[filtered_df["date"].str.startswith(month_filter)]

# 一覧表示
st.subheader("📖 読書一覧")
if filtered_df.empty:
    st.info("該当するデータがありません。")
else:
    for _, row in filtered_df.iterrows():
        with st.container():
            cols = st.columns([1, 4])
            with cols[0]:
                if row["image"].startswith("http"):
                    st.image(row["image"], width=80)
                else:
                    st.image("no-image.png", width=80)
            with cols[1]:
                st.markdown(f"**{row['title']}**")
                st.markdown(f"著者: {row['author']}　📅 {row['date']}　⭐ {'★'*int(row['rating'])}")
                if row["memo"]:
                    st.markdown(f"> {row['memo']}")

# グラフ表示
st.subheader("📊 月別読了数")
if "date" in df.columns:
    df["month"] = df["date"].str[:7]
    chart_data = df["month"].value_counts().sort_index()
    fig, ax = plt.subplots()
    chart_data.plot(kind="bar", ax=ax, color="#60a5fa")
    ax.set_xlabel("年月")
    ax.set_ylabel("冊数")
    st.pyplot(fig)
