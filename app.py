import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt

# Google Sheets 認証
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
df.columns = [col.strip() for col in df.columns]  # 列名の前後の空白を削除
df["評価"] = pd.to_numeric(df["評価"], errors="coerce")

st.title("📚 読書記録ログ")
st.write("📋 現在の列名:", df.columns.tolist())  # デバッグ用

# 検索・フィルター
keyword = st.text_input("🔍 タイトル・著者で検索")
rating_filter = st.selectbox("⭐ 評価で絞り込み", options=["すべて", "★5", "★4以上", "★3以上", "★2以上", "★1以上"])
month_filter = st.selectbox(
    "📅 年月で絞り込み",
    options=["すべて"] + sorted(df["読了日"].dropna().astype(str).str[:7].unique())
)

# 絞り込み処理
filtered_df = df.copy()

if keyword:
    filtered_df = filtered_df[
        filtered_df["タイトル"].astype(str).str.contains(keyword, case=False, na=False) |
        filtered_df["著者"].astype(str).str.contains(keyword, case=False, na=False)
    ]

if rating_filter != "すべて":
    try:
        stars = int(rating_filter.replace("★", "").replace("以上", ""))
        filtered_df = filtered_df[filtered_df["評価"] >= stars]
    except Exception as e:
        st.error(f"評価フィルターエラー: {e}")

if month_filter != "すべて":
    filtered_df = filtered_df[filtered_df["読了日"].astype(str).str.startswith(month_filter)]

# 読書記録の表示
for _, row in filtered_df.iterrows():
    st.markdown(f"### {row['タイトル']}")
    st.write(f"著者: {row['著者']}")
    st.write(f"読了日: {row['読了日']}")
    st.write(f"評価: {'★' * int(row['評価']) if pd.notna(row['評価']) else 'なし'}")

    if row["メモ"]:
        st.write(f"メモ: {row['メモ']}")

    image_url = str(row.get("表紙画像", "")).strip()
    if image_url.startswith("http"):
        try:
            safe_url = image_url.replace("http://", "https://")
            st.image(safe_url, width=100)
        except Exception as e:
            st.warning(f"画像の読み込みエラー: {e}")
    else:
        st.write("📕 表紙画像なし")

    st.markdown("---")

# 月別グラフ
if not df.empty:
    df["年月"] = df["読了日"].astype(str).str[:7]
    monthly_count = df["年月"].value_counts().sort_index()

    st.subheader("📊 月別読了数")
    fig, ax = plt.subplots()
    monthly_count.plot(kind="bar", ax=ax)
    ax.set_xlabel("年月")
    ax.set_ylabel("冊数")
    st.pyplot(fig)
