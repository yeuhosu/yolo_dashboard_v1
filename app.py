import streamlit as st
import pandas as pd
import datetime as _dt
from datetime import date

from data_manager import (
    get_sheet_data,
    add_workout_data,
    update_workout_data,
    delete_workout_data,
)

st.set_page_config(page_title="Training Logger", layout="centered")
st.markdown(
    """
    <style>
    /* カレンダーの日付グリッドだけ横並びを維持・コンパクト化 */
    .st-key-calendar_grid div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 4px !important;
    }
    .st-key-calendar_grid div[data-testid="stColumn"],
    .st-key-calendar_grid div[data-testid="column"] {
        min-width: 0 !important;
        width: auto !important;
        flex: 1 1 0 !important;
        padding: 0 2px !important;
    }
    .st-key-calendar_grid button {
        padding: 0.25rem 0.1rem !important;
        font-size: 0.8rem !important;
        min-height: 2.2rem !important;
    }

    /* KPIサマリーもモバイルで横並びを維持 */
    .st-key-kpi_summary div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 6px !important;
    }
    .st-key-kpi_summary div[data-testid="stColumn"],
    .st-key-kpi_summary div[data-testid="column"] {
        min-width: 0 !important;
        width: auto !important;
        flex: 1 1 0 !important;
    }
    .st-key-kpi_summary [data-testid="stMetric"] {
        padding: 8px 4px !important;
    }
    .st-key-kpi_summary [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        white-space: normal !important;
    }
    .st-key-kpi_summary [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
     /* 直近の記録カード */
    .record-card {
        background-color: #F5F5F7;
        border-radius: 14px;
        padding: 14px 16px 10px 16px;
        margin-bottom: 10px;
        border-left: 4px solid #FF4B4B;
    }
    .record-card.cardio {
        border-left-color: #4B9BFF;
    }
    .record-card .record-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .record-card .exercise-name {
        font-weight: 700;
        font-size: 1.05rem;
        color: #1A1A1A;
    }
    .record-card .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        color: white;
        background-color: #FF4B4B;
        white-space: nowrap;
    }
    .record-card .badge.cardio {
        background-color: #4B9BFF;
    }
    .record-card .record-meta {
        color: #555;
        font-size: 0.88rem;
        margin-bottom: 2px;
    }
    .record-card .record-note {
        color: #888;
        font-size: 0.8rem;
        margin-top: 4px;
        font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💪 筋トレ記録")

# データ取得
df = get_sheet_data()

# --- タブの作成 ---
tab1, tab2, tab3 = st.tabs(["記録入力", "カレンダー", "全履歴"])

PART_OPTIONS = ["胸", "背中", "脚", "肩", "上腕2頭", "上腕3頭", "腹筋", "有酸素"]
CARDIO_PART = "有酸素"
NEW_EXERCISE_LABEL = "＋ 新しい種目を追加"


def clear_form_state():
    for key in [
        "date_input",
        "exercise_choice",
        "new_exercise_input",
        "weight_input",
        "reps_input",
        "parts_input",
        "duration_input",
        "calories_input",
        "note_input",
        "edit_row_index",
        "editing_mode",
        "autofill_target",
    ]:
        st.session_state.pop(key, None)


def normalize_date(value):
    if isinstance(value, str):
        try:
            return _dt.date.fromisoformat(value)
        except Exception:
            return date.today()
    return value


def get_latest_record_map(dataframe: pd.DataFrame) -> dict:
    if "Exercise" not in dataframe.columns or dataframe.empty:
        return {}

    records = dataframe.copy()
    records = records.dropna(subset=["Exercise"])
    records["Exercise"] = records["Exercise"].astype(str).str.strip()
    records = records[records["Exercise"] != ""]

    if records.empty:
        return {}

    if "RowIndex" in records.columns:
        records = records.sort_values(["Date", "RowIndex"], ascending=[False, False], kind="mergesort")
    else:
        records = records.sort_values(["Date"], ascending=False, kind="mergesort")

    latest_map = {}
    for _, row in records.iterrows():
        exercise = str(row["Exercise"]).strip()
        if exercise not in latest_map:
            latest_map[exercise] = row
    return latest_map
def calculate_streak(event_dates: set) -> int:
    """今日または昨日を起点に、連続して記録がある日数を数える"""
    if not event_dates:
        return 0

    today = _dt.date.today()
    if today in event_dates:
        cursor = today
    elif (today - _dt.timedelta(days=1)) in event_dates:
        # 今日はまだ記録していなくても、昨日までの連続は維持する
        cursor = today - _dt.timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in event_dates:
        streak += 1
        cursor -= _dt.timedelta(days=1)
    return streak

with tab1:
        # --- KPIサマリー ---
    if not df.empty and "Date" in df.columns:
        try:
            date_series = pd.to_datetime(df["Date"]).dt.date
        except Exception:
            date_series = pd.Series([], dtype="object")

        event_date_set = set(date_series.unique())
        week_start = _dt.date.today() - _dt.timedelta(days=6)
        week_days_trained = len({d for d in event_date_set if d >= week_start})

        today = _dt.date.today()
        month_days_trained = len({
            d for d in event_date_set
            if d.year == today.year and d.month == today.month
        })

        streak = calculate_streak(event_date_set)
    else:
        week_days_trained = 0
        month_days_trained = 0
        streak = 0

    with st.container(key="kpi_summary"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("今週の日数", f"{week_days_trained}日")
        with col_b:
            st.metric("今月の日数", f"{month_days_trained}日")
        with col_c:
            st.metric("連続記録", f"{streak}日", help="今日または昨日までの連続トレーニング日数")

    st.divider()

    # --- ① まず部位を選択（フォームの外＝選ぶと即座に種目候補が絞り込まれる）---
    part_selected = st.selectbox(
        "部位",
        PART_OPTIONS,
        index=None,
        placeholder="部位を選択してください",
        key="parts_input",
        help="部位を選ぶと、その部位で過去に記録した種目だけが種目リストに表示されます。",
    )
    is_cardio = part_selected == CARDIO_PART

    # --- ② 選んだ部位でExerciseを絞り込み ---
    def _row_matches_part(row_part_str, selected_part):
        row_parts = {p.strip() for p in str(row_part_str).split(",") if p.strip()}
        return selected_part in row_parts

    if part_selected and "Part" in df.columns and not df.empty:
        filtered_df = df[df["Part"].apply(lambda x: _row_matches_part(x, part_selected))]
    else:
        filtered_df = df  # 部位未選択の場合は全種目を表示

    if "Exercise" in filtered_df.columns and not filtered_df.empty:
        existing_exercises = sorted(
            {str(e).strip() for e in filtered_df["Exercise"].dropna() if str(e).strip()}
        )
    else:
        existing_exercises = []

    exercise_options = [NEW_EXERCISE_LABEL] + existing_exercises

    # 部位変更などで、今選択中の種目が候補から消えていたら先頭にリセット
    if st.session_state.get("exercise_choice") not in exercise_options:
        st.session_state["exercise_choice"] = exercise_options[0]

    # --- ③ 種目→重量・回数・時間・カロリー・部位を自動入力するコールバック ---
    def _apply_exercise_autofill():
        exercise_name = st.session_state.get("exercise_choice")
        if not exercise_name or exercise_name == NEW_EXERCISE_LABEL:
            return

        latest_record_map = get_latest_record_map(df)
        if exercise_name not in latest_record_map:
            return

        latest_record = latest_record_map[exercise_name]
        try:
            weight_default = float(latest_record.get("Weight", 0) or 0)
        except (TypeError, ValueError):
            weight_default = 0.0
        try:
            reps_default = int(latest_record.get("Reps", 0) or 0)
        except (TypeError, ValueError):
            reps_default = 0
        try:
            duration_default = float(latest_record.get("Duration", 0) or 0)
        except (TypeError, ValueError):
            duration_default = 0.0
        try:
            calories_default = float(latest_record.get("Calories", 0) or 0)
        except (TypeError, ValueError):
            calories_default = 0.0

        part_list = [
            p.strip() for p in str(latest_record.get("Part", "")).split(",") if p.strip()
        ]

        st.session_state["weight_input"] = weight_default
        st.session_state["reps_input"] = reps_default
        st.session_state["duration_input"] = duration_default
        st.session_state["calories_input"] = calories_default
        if part_list and part_list[0] in PART_OPTIONS:
            st.session_state["parts_input"] = part_list[0]
        st.session_state["autofill_target"] = exercise_name

    exercise_choice = st.selectbox(
        "種目名",
        exercise_options,
        key="exercise_choice",
        on_change=_apply_exercise_autofill,
    )

    # --- ここで、キー付きウィジェットのデフォルト値を「まだ無い場合だけ」設定 ---
    st.session_state.setdefault("date_input", date.today())
    st.session_state.setdefault("new_exercise_input", "")
    st.session_state.setdefault("weight_input", 0.0)
    st.session_state.setdefault("reps_input", 0)
    st.session_state.setdefault("duration_input", 0.0)
    st.session_state.setdefault("calories_input", 0.0)
    st.session_state.setdefault("note_input", "")

    st.caption("※ 以前に記録した種目を選ぶと、内容が自動で入ります")

    with st.form("training_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input("日付", key="date_input")
            new_exercise = st.text_input(
                "新しい種目名（「＋ 新しい種目を追加」を選んだ場合に入力）",
                key="new_exercise_input",
            )
        with col2:
            if is_cardio:
                duration = st.number_input(
                    "時間（分）",
                    min_value=0.0,
                    step=1.0,
                    key="duration_input",
                )
                calories = st.number_input(
                    "消費カロリー (kcal)",
                    min_value=0.0,
                    step=10.0,
                    key="calories_input",
                )
            else:
                weight = st.number_input(
                    "重量 (kg)",
                    min_value=0.0,
                    step=0.01,
                    key="weight_input",
                )
                reps = st.number_input(
                    "回数",
                    min_value=0,
                    step=1,
                    key="reps_input",
                )

        note = st.text_input("メモ", key="note_input")

        editing_mode = bool(st.session_state.get("editing_mode", False))
        submit_label = "更新する" if editing_mode else "記録を保存"
        submitted = st.form_submit_button(submit_label)

        if submitted:
            if exercise_choice == NEW_EXERCISE_LABEL:
                exercise = new_exercise.strip()
            else:
                exercise = exercise_choice

            if not part_selected:
                st.error("「部位」を選択してください。")
            elif not exercise:
                st.error("「種目名」を入力（または選択）してください。")
            elif is_cardio and duration <= 0:
                st.error("「時間（分）」を入力してください。")
            elif not is_cardio and (weight <= 0 and reps <= 0):
                st.error("「重量」と「回数」の両方を入力してください。")
            else:
                if is_cardio:
                    weight_val, reps_val = 0, 0
                    duration_val, calories_val = duration, calories
                else:
                    weight_val, reps_val = weight, reps
                    duration_val, calories_val = 0, 0

                data_row = [
                    str(date_val),
                    exercise,
                    weight_val,
                    reps_val,
                    part_selected,
                    note,
                    duration_val,
                    calories_val,
                ]
                row_index = st.session_state.get("edit_row_index")

                with st.spinner("保存中..."):
                    if editing_mode and row_index is not None:
                        ok = update_workout_data(int(row_index), data_row)
                    else:
                        ok = add_workout_data(data_row)

                if ok:
                    st.toast("記録しました。" if not editing_mode else "更新しました。")

                    # 編集モードだけ解除し、入力内容はそのまま残す
                    st.session_state["editing_mode"] = False
                    st.session_state["edit_row_index"] = None

                    # 新規種目を保存した場合は、ドロップダウンをその種目に切り替えておく
                    if exercise_choice == NEW_EXERCISE_LABEL:
                        st.session_state["exercise_choice"] = exercise
                        st.session_state["new_exercise_input"] = ""
                        st.session_state["autofill_target"] = exercise

                    st.rerun()
                else:
                    st.error("保存に失敗しました。")

    st.divider()
    st.subheader("直近の記録")

    def start_edit(row_index, row):
        st.session_state["edit_row_index"] = int(row_index)
        st.session_state["editing_mode"] = True
        st.session_state["date_input"] = normalize_date(row.get("Date", date.today()))
        st.session_state["exercise_choice"] = str(row.get("Exercise", ""))
        st.session_state["new_exercise_input"] = ""
        st.session_state["weight_input"] = float(row.get("Weight", 0) or 0)
        st.session_state["reps_input"] = int(row.get("Reps", 0) or 0)
        st.session_state["duration_input"] = float(row.get("Duration", 0) or 0)
        st.session_state["calories_input"] = float(row.get("Calories", 0) or 0)

        row_parts = [p.strip() for p in str(row.get("Part", "")).split(",") if p.strip()]
        st.session_state["parts_input"] = (
            row_parts[0] if row_parts and row_parts[0] in PART_OPTIONS else None
        )

        st.session_state["note_input"] = str(row.get("Note", ""))
        st.session_state["autofill_target"] = str(row.get("Exercise", ""))

    def start_delete(row_index):
        with st.spinner("削除中..."):
            ok = delete_workout_data(int(row_index))
        st.session_state["_delete_ok"] = ok

    if not df.empty and "Date" in df.columns:
        recent_df = df.copy()
        if "RowIndex" in recent_df.columns:
            recent_df = recent_df.sort_values(["Date", "RowIndex"], ascending=[False, False], kind="mergesort")
        else:
            recent_df = recent_df.sort_values("Date", ascending=False, kind="mergesort")
        recent_df = recent_df.head(8)

        for _, row in recent_df.iterrows():
            row_index = row.get("RowIndex")
            row_is_cardio = str(row.get("Part", "")).strip() == CARDIO_PART
            card_class = "record-card cardio" if row_is_cardio else "record-card"
            badge_class = "badge cardio" if row_is_cardio else "badge"

            if row_is_cardio:
                meta = f"⏱ {row.get('Duration', '')}分　🔥 {row.get('Calories', '')}kcal"
            else:
                meta = f"🏋 {row.get('Weight', '')}kg × {row.get('Reps', '')}回"

            note_html = (
                f'<div class="record-note">📝 {row.get("Note", "")}</div>'
                if str(row.get("Note", "")).strip()
                else ""
            )

            st.markdown(
                f"""
                <div class="{card_class}">
                    <div class="record-top">
                        <span class="exercise-name">{row.get('Exercise', '')}</span>
                        <span class="{badge_class}">{row.get('Part', '')}</span>
                    </div>
                    <div class="record-meta">{row.get('Date', '')}　・　{meta}</div>
                    {note_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_edit, col_delete = st.columns(2)
            with col_edit:
                st.button(
                    "編集",
                    key=f"edit-{row_index}",
                    use_container_width=True,
                    on_click=start_edit,
                    args=(row_index, row),
                )
            with col_delete:
                st.button(
                    "削除",
                    key=f"delete-{row_index}",
                    use_container_width=True,
                    on_click=start_delete,
                    args=(row_index,),
                )

        if "_delete_ok" in st.session_state:
            if st.session_state.pop("_delete_ok"):
                st.toast("削除しました。")
            else:
                st.error("削除に失敗しました。")
    else:
        st.info("まだ記録がありません。")

# --- タブ2: カレンダー ---
with tab2:
    import calendar as _cal

    event_dates = set()
    if "Date" in df.columns and not df.empty:
        try:
            event_dates = set(pd.to_datetime(df["Date"]).dt.date.astype(str).unique())
        except Exception:
            event_dates = set(df["Date"].astype(str).unique())

    today = _dt.datetime.today()
    year = st.session_state.get("cal_year", today.year)
    month = st.session_state.get("cal_month", today.month)

    cal = _cal.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    prev_month = (month - 1) or 12
    prev_year = year - 1 if month == 1 else year
    next_month = month + 1 if month < 12 else 1
    next_year = year + 1 if month == 12 else year

    # ナビゲーション行（コンパクトCSSの対象外＝ゆったり表示）
    nav_cols = st.columns([1, 2, 1])
    with nav_cols[0]:
        if st.button("◀ 前の月", use_container_width=True):
            st.session_state["cal_year"] = prev_year
            st.session_state["cal_month"] = prev_month
            st.rerun()
    with nav_cols[1]:
        st.markdown(
            f"<h4 style='text-align:center; margin:0.4rem 0;'>{year}年{month}月</h4>",
            unsafe_allow_html=True,
        )
    with nav_cols[2]:
        if st.button("次の月 ▶", use_container_width=True):
            st.session_state["cal_year"] = next_year
            st.session_state["cal_month"] = next_month
            st.rerun()

    # ここから下だけ「カレンダーグリッド」として囲む
    with st.container(key="calendar_grid"):
        weekday_cols = st.columns(7)
        for wcol, wname in zip(weekday_cols, ["日", "月", "火", "水", "木", "金", "土"]):
            wcol.markdown(
                f"<div style='text-align:center;font-weight:600;color:#888'>{wname}</div>",
                unsafe_allow_html=True,
            )

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
                    st.session_state["clicked_date"] = date_str

    st.divider()

    selected_date = st.session_state.get("clicked_date", None)
    if selected_date:
        st.subheader(f"📅 {selected_date} の記録")
        try:
            day_df = df[pd.to_datetime(df["Date"]).dt.date.astype(str) == selected_date]
        except Exception:
            day_df = df[df["Date"].astype(str) == selected_date]

        if not day_df.empty:
            display_cols = [c for c in ["Exercise", "Weight", "Reps", "Part", "Note", "Duration", "Calories"] if c in day_df.columns]
            st.table(day_df[display_cols])
        else:
            st.info("この日はトレーニング記録がありません。")
    else:
        st.caption("日付をクリックすると、その日の記録が表示されます。赤色のマスがトレーニング実施日です。")


# --- タブ3: 全履歴 ---
with tab3:
    st.subheader("トレーニング履歴")
    if not df.empty:
        history_df = df.copy()
        if "RowIndex" in history_df.columns:
            history_df = history_df.drop(columns=["RowIndex"])
        st.dataframe(history_df.sort_values("Date", ascending=False), width=1000)
    else:
        st.info("まだ記録がありません。")