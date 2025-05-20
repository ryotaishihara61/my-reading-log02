import streamlit as st
import pandas as pd
import requests
import datetime
import matplotlib.pyplot as plt
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets 認証
def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    sheet_id = st.secrets["1uAnEQFm6qwf-4xsYcAJyRQlfjkZgpDKlnBMQYfecEAs"]
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

# Google Books API でISBNから書籍情報を取得
def fetch_book_info(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    if "items" not in data:
        return None
    volume = data["items"][0]["volumeInfo"]
    return {
        "title": volume.get("title", ""),
        "author": volume.get("authors", [""])[0],
        "image": volume.get("imageLinks", {}).get("thumbnail", "")
    }

# 書籍をシートに保存
def save_book(sheet, record):
    row = [
        record["isbn"],
        record["title"],
        record["author"],
        record["date"],
        record["memo"],
        record["rating"],
        record["image"]
    ]
    sheet.append_row(row)

# データフレーム取得
def load_data(sheet):
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

# UI スタート
st.set_page_config(page_title="読書記録アプリ", layout="wide")
st.title("📚 読書記録アプリ")

sheet = get_worksheet()

# タブ選択
tab1, tab2 = st.tabs(["📥 新しい本を記録", "📖 一覧・グラフ"])

# ---- TAB 1: 登録 ----
with tab1:
    st.subheader("📘 書籍情報を入力")
    isbn = st.text_input("ISBN-13", placeholder="例: 9784763141880")
    if st.button("書籍検索") and isbn:
        info = fetch_book_info(isbn)
        if info:
            st.success("書籍が見つかりました")
            st.image(info["image"])
            title = st.text_input("タイトル", value=info["title"])
            author = st.text_input("著者", value=info["author"])
        else:
            st.error("書籍が見つかりませんでした")
            title = st.text_input("タイトル")
            author = st.text_input("著者")
    else:
        title = st.text_input("タイトル")
        author = st.text_input("著者")

    date = st.date_input("読了日", value=datetime.date.today())
    rating = st.slider("評価（★）", 1, 5, 3)
    memo = st.text_area("メモ・感想")
    image = info["image"] if "info" in locals() and info else ""

    if st.button("📌 保存する"):
        record = {
            "isbn": isbn,
            "title": title,
            "author": author,
            "date": date.strftime("%Y-%m-%d"),
            "memo": memo,
            "rating": rating,
            "image": image
        }
        save_book(sheet, record)
        st.success("保存しました！")

# ---- TAB 2: 一覧・グラフ ----
with tab2:
    st.subheader("📖 読了記録一覧")
    df = load_data(sheet)

    if df.empty:
        st.info("まだ記録がありません。")
    else:
        # 検索・フィルター
        col1, col2 = st.columns(2)
        with col1:
            search = st.text_input("🔍 タイトル・著者検索")
        with col2:
            min_rating = st.selectbox("⭐ 最低評価", ["すべて", "1", "2", "3", "4", "5"])

        if search:
            df = df[df["title"].str.contains(search, case=False) | df["author"].str.contains(search, case=False)]
        if min_rating != "すべて":
            df = df[df["rating"].astype(int) >= int(min_rating)]

        # 表示
        st.dataframe(df[["date", "title", "author", "rating", "memo"]], use_container_width=True)

        # グラフ
        st.subheader("📊 月別読了数")
        df["month"] = df["date"].str[:7]
        chart_data = df.groupby("month").size().reset_index(name="count")
        fig, ax = plt.subplots()
        ax.bar(chart_data["month"], chart_data["count"], color="#60a5fa")
        ax.set_ylabel("冊数")
        ax.set_xlabel("年月")
        ax.set_title("月ごとの読了冊数")
        st.pyplot(fig)
