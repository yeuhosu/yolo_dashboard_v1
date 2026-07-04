import streamlit as st
from data_manager import get_sheet_data, add_workout_data
from datetime import date
import pandas as pd
import datetime as _dt

st.set_page_config(page_title="Training Logger", layout="centered")
st.title("💪 筋トレ記録")

df = get_sheet_data()

# --- タブの作成 ---
tab1, tab2, tab3 = st.tabs(["記録入力", "カレンダー", "全履歴"])

# --- タブ1: 記録入力 ---
with tab1:
      # 過去の入力履歴から種目名リストを作成（表記ゆれ防止のため前後の空白は除去し重複排除）
    NEW_EXERCISE_LABEL = "＋ 新しい種目を追加"
    if 'Exercise' in df.columns and not df.empty:
        existing_exercises = sorted(
            {str(e).strip() for e in df['Exercise'].dropna() if str(e).strip()}
        )
    else:
        existing_exercises = []
    exercise_options = [NEW_EXERCISE_LABEL] + existing_exercises
    
    with st.form("training_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input("日付", date.today())
            exercise = st.text_input("種目名")
        with col2:
            weight = st.number_input("重量 (kg)", min_value=0.0, step=0.25)
            reps = st.number_input("回数", min_value=0, step=1)

        # 部位を複数選択可能に
        parts = st.multiselect("部位", ["胸", "背中", "脚", "肩", "上腕2頭", "上腕3頭", "腹筋", "有酸素"])
        note = st.text_input("メモ")

        submitted = st.form_submit_button("記録を保存")
        if submitted:
            # --- バリデーションチェック ---
            if not exercise:
                st.error("「種目名」を入力してください。")
            elif weight <= 0 and reps <= 0:
                st.error("「重量」と「回数」の両方を入力してください。")
            else:
                # バリデーションクリア！保存処理へ
                part_str = ", ".join(parts)
                if add_workout_data([str(date_val), exercise, weight, reps, part_str, note]):
                    st.success("追加しました！")
                    st.rerun()
                else:
                    st.error("保存に失敗しました。")

# --- タブ2: カレンダー ---
with tab2:
    import calendar as _cal

    # イベント日の集合（YYYY-MM-DD）
    event_dates = set()
    if 'Date' in df.columns and not df.empty:
        try:
            event_dates = set(pd.to_datetime(df['Date']).dt.date.astype(str).unique())
        except Exception:
            event_dates = set(df['Date'].astype(str).unique())

    # 表示する年・月（session_state で保持、未設定なら今月）
    today = _dt.datetime.today()
    year = st.session_state.get('cal_year', today.year)
    month = st.session_state.get('cal_month', today.month)

    cal = _cal.Calendar(firstweekday=6)  # 週の始まりを日曜に
    month_days = cal.monthdayscalendar(year, month)

    # ナビゲーション
    prev_month = (month - 1) or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    nav_cols = st.columns([1, 2, 1])
    with nav_cols[0]:
        if st.button('◀ 前の月', use_container_width=True):
            st.session_state['cal_year'] = prev_year
            st.session_state['cal_month'] = prev_month
            st.rerun()
    with nav_cols[1]:
        st.markdown(f"<h3 style='text-align:center'>{year}年 {month}月</h3>", unsafe_allow_html=True)
    with nav_cols[2]:
        if st.button('次の月 ▶', use_container_width=True):
            st.session_state['cal_year'] = next_year
            st.session_state['cal_month'] = next_month
            st.rerun()

    # 曜日ヘッダー（日曜始まり）
    weekday_cols = st.columns(7)
    for wcol, wname in zip(weekday_cols, ["日", "月", "火", "水", "木", "金", "土"]):
        wcol.markdown(f"<div style='text-align:center;font-weight:600;color:#888'>{wname}</div>", unsafe_allow_html=True)

    # カレンダー本体：各週を7カラムで描画。全ボタンを同じ見た目（同サイズ）にし、
    # 実施日だけ type="primary"（テーマの強調色＝赤系）にすることで統一感を出す
    for week in month_days:
        cols = st.columns(7, gap="small")
        for i, d in enumerate(week):
            col = cols[i]
            if d == 0:
                col.write("")
                continue

            date_str = f"{year:04d}-{month:02d}-{d:02d}"
            has_event = date_str in event_dates

            with col:
                clicked = st.button(
                    str(d),
                    key=f"day-{date_str}",
                    use_container_width=True,
                    type="primary" if has_event else "secondary",
                )
            if clicked:
                st.session_state['clicked_date'] = date_str

    st.divider()

    # クリックされた日付の記録を表示
    selected_date = st.session_state.get('clicked_date', None)
    if selected_date:
        st.subheader(f"📅 {selected_date} の記録")
        try:
            day_df = df[pd.to_datetime(df['Date']).dt.date.astype(str) == selected_date]
        except Exception:
            day_df = df[df['Date'].astype(str) == selected_date]

        if not day_df.empty:
            st.table(day_df[["Exercise", "Weight", "Reps", "Part", "Note"]])
        else:
            st.info("この日はトレーニング記録がありません。")
    else:
        st.caption("日付をクリックすると、その日の記録が表示されます。赤色のマスがトレーニング実施日です。")

# --- タブ3: 全履歴 ---
with tab3:
    st.subheader("トレーニング履歴")
    if not df.empty:
        st.dataframe(df.sort_values("Date", ascending=False), width=1000)
        # if "Weight" in df.columns:
        #     st.line_chart(df.set_index("Date")["Weight"])
    else:
        st.info("まだ記録がありません。")