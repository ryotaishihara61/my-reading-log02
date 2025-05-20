import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt
from matplotlib import font_manager
import requests

# 日本語フォントを読み込み（プロジェクトにファイルが必要）
font_path = "ipaexg.ttf"
jp_font = font_manager.FontProperties(fname=font_path)

# 📌 安全に画像を表示する関数
def safe_image_display(url: str, width: int = 100):
    try:
        # 空欄や None のときは no-image.png を使用
        if not url or not isinstance(url, str) or url.strip() == "":
            url = "https://raw.githubusercontent.com/ryotaishihara61/my-reading-log02/main/no-image.png"

        if url.startswith("http"):
            secure_url = url.replace("http://", "https://")
            resp = requests.head(secure_url, timeout=3)
            if resp.status_code == 200 and "image" in resp.headers.get("Content-Type", ""):
                st.image(secure_url, width=width)
            else:
                st.warning("⚠️ 表紙画像が無効な形式です")
        else:
            st.warning("⚠️ 表紙画像URLが無効です")
    except Exception as e:
        st.warning(f"⚠️ 表紙画像の読み込みエラー: {e}")

# 🔐 Google Sheets認証
def get_worksheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        scope
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(st.secrets["spreadsheet_id"])
    return spreadsheet.sheet1

# 📄 データの取得
sheet = get_worksheet()
data = sheet.get_all_records()
df = pd.DataFrame(data)
df.columns = [col.strip() for col in df.columns]
df["評価"] = pd.to_numeric(df["評価"], errors="coerce")

st.title("📚 読了ズ")

# 🔍 検索・フィルター
keyword = st.text_input("🔍 タイトル・著者で検索")
rating_filter = st.selectbox("⭐ 評価で絞り込み", options=["すべて", "★5", "★4以上", "★3以上", "★2以上", "★1以上"])
month_filter = st.selectbox("📅 年月で絞り込み", options=["すべて"] + sorted(df["読了日"].astype(str).str[:7].dropna().unique()))

filtered_df = df.copy()

if keyword:
    filtered_df = filtered_df[
        filtered_df["タイトル"].str.contains(keyword, case=False, na=False) |
        filtered_df["著者"].str.contains(keyword, case=False, na=False)
    ]

if rating_filter != "すべて":
    try:
        stars = int(str(rating_filter).replace("★", "").replace("以上", ""))
        filtered_df = filtered_df[filtered_df["評価"] >= stars]
    except Exception as e:
        st.error(f"評価のフィルター処理でエラー: {e}")

if month_filter != "すべて":
    filtered_df = filtered_df[filtered_df["読了日"].astype(str).str.startswith(month_filter)]

# 📋 表示
for _, row in filtered_df.iterrows():
    st.markdown(f"### {row['タイトル']}")
    st.write(f"著者: {row['著者']}")
    st.write(f"読了日: {row['読了日']}")
    st.write(f"評価: {'★' * int(row['評価'])}")
    if row.get("メモ"):
        st.write(f"メモ: {row['メモ']}")
    safe_image_display(str(row.get("表紙画像", "")))
    st.markdown("---")

# 📊 月別読了グラフ
if not df.empty:
    import matplotlib.ticker as ticker
    plt.rcParams['font.family'] = 'IPAexGothic'

    df["年月"] = df["読了日"].astype(str).str[:7]
    monthly_count = df["年月"].value_counts().sort_index()

    st.subheader("📊 月別読了数")
    fig, ax = plt.subplots()
    monthly_count.plot(kind="bar", ax=ax)

    ax.set_xlabel("年月", fontproperties=jp_font)
    ax.set_ylabel("冊数", fontproperties=jp_font)
    ax.set_title("月別読了数", fontproperties=jp_font)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))  # Y軸目盛りを整数に

    ax.tick_params(axis='x', labelrotation=45)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
       label.set_fontproperties(jp_font)

    st.pyplot(fig)

st.header("📖 新しい本の登録")

isbn_input = st.text_input("ISBNコードを入力（例: 978-4101202433 または 9784101202433）")

if st.button("🔍 本を検索"):
    isbn_clean = isbn_input.replace("-", "").strip()
    if not isbn_clean.isdigit():
        st.error("無効なISBNコードです。数字またはハイフン付きで入力してください。")
    else:
        google_books_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn_clean}"
        try:
            res = requests.get(google_books_url)
            res.raise_for_status()
            items = res.json().get("items")
            if items:
                volume_info = items[0]["volumeInfo"]
                title = volume_info.get("title", "")
                authors = ", ".join(volume_info.get("authors", []))
                image = volume_info.get("imageLinks", {}).get("thumbnail", "")
                st.success("📚 本が見つかりました。下記内容で登録してください。")

                with st.form("register_book"):
                    memo = st.text_input("メモ")
                    rating = st.slider("評価", 1, 5, 3)
                    read_date = st.date_input("読了日")
                    submit = st.form_submit_button("✅ 登録")

                    if submit:
                        sheet = get_worksheet()
                        sheet.append_row([
                            isbn_clean,
                            title,
                            authors,
                            str(read_date),
                            memo,
                            rating,
                            image
                        ])
                        st.success("✅ 登録が完了しました！")
            else:
                st.warning("該当する本が見つかりませんでした。")
        except Exception as e:
            st.error(f"📡 Google Books API の取得中にエラーが発生しました: {e}")