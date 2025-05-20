import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt

# Google Sheets認証
def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        scope
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
    return spreadsheet.sheet1

# データの取得
sheet = get_worksheet()
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("📚 読書記録ログ")

# 検索・フィルター
keyword = st.text_input("🔍 タイトル・著者で検索")
rating_filter = st.selectbox("⭐ 評価で絞り込み", options=["すべて", "★5", "★4以上", "★3以上", "★2以上", "★1以上"])
month_filter = st.selectbox("📅 年月で絞り込み", options=["すべて"] + sorted(df["読了日"].str[:7].dropna().unique()))

# 絞り込み処理
filtered_df = df.copy()

if keyword:
    filtered_df = filtered_df[
        filtered_df["タイトル"].str.contains(keyword, case=False, na=False) |
        filtered_df["著者"].str.contains(keyword, case=False, na=False)
    ]

if rating_filter != "すべて":
    stars = int(rating_filter.replace("★", "").replace("以上", ""))
    filtered_df = filtered_df[filtered_df["評価"] >= stars]

if month_filter != "すべて":
    filtered_df = filtered_df[filtered_df["読了日"].str.startswith(month_filter)]

# 表示
for _, row in filtered_df.iterrows():
    st.markdown(f"### {row['タイトル']}")
    st.write(f"著者: {row['著者']}")
    st.write(f"読了日: {row['読了日']}")
    st.write(f"評価: {'★' * int(row['評価'])}")
    if row["メモ"]:
        st.write(f"メモ: {row['メモ']}")
    if row["表紙画像"]:
        st.image(row["表紙画像"], width=100)
    st.markdown("---")

# 月別グラフ
if not df.empty:
    df["年月"] = df["読了日"].str[:7]
    monthly_count = df["年月"].value_counts().sort_index()
    st.subheader("📊 月別読了数")
    fig, ax = plt.subplots()
    monthly_count.plot(kind="bar", ax=ax)
    ax.set_xlabel("年月")
    ax.set_ylabel("冊数")
    st.pyplot(fig)
