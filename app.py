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
NEW_EXERCISE_LABEL = "＋ 新しい種目を追加"


def clear_form_state():
    for key in [
        "date_input",
        "exercise_choice",
        "new_exercise_input",
        "weight_input",
        "reps_input",
        "parts_input",
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


# --- タブ1: 記録入力 ---
with tab1:
    st.session_state.setdefault("parts_input", [])

    # --- ① まず部位を選択（フォームの外＝選ぶと即座に種目候補が絞り込まれる）---
    parts = st.multiselect(
        "部位",
        PART_OPTIONS,
        key="parts_input",
        help="部位を選ぶと、その部位で過去に記録した種目だけが種目リストに表示されます。",
    )

    # --- ② 選んだ部位でExerciseを絞り込み ---
    def _row_matches_parts(row_part_str, selected_parts):
        row_parts = {p.strip() for p in str(row_part_str).split(",") if p.strip()}
        return bool(row_parts & set(selected_parts))

    if parts and "Part" in df.columns and not df.empty:
        filtered_df = df[df["Part"].apply(lambda x: _row_matches_parts(x, parts))]
    else:
        filtered_df = df  # 部位未選択の場合は全種目を表示

    if "Exercise" in filtered_df.columns and not filtered_df.empty:
        existing_exercises = sorted(
            {str(e).strip() for e in filtered_df["Exercise"].dropna() if str(e).strip()}
        )
    else:
        existing_exercises = []

    exercise_options = [NEW_EXERCISE_LABEL] + existing_exercises
    latest_record_map = get_latest_record_map(df)

    # 部位変更などで、今選択中の種目が候補から消えていたら先頭にリセット
    if st.session_state.get("exercise_choice") not in exercise_options:
        st.session_state["exercise_choice"] = exercise_options[0]

    exercise_choice = st.selectbox("種目名", exercise_options, key="exercise_choice")

    if (
        exercise_choice != NEW_EXERCISE_LABEL
        and exercise_choice in latest_record_map
        and st.session_state.get("autofill_target") != exercise_choice
    ):
        latest_record = latest_record_map[exercise_choice]
        try:
            weight_default = float(latest_record.get("Weight", 0) or 0)
        except (TypeError, ValueError):
            weight_default = 0.0
        try:
            reps_default = int(latest_record.get("Reps", 0) or 0)
        except (TypeError, ValueError):
            reps_default = 0

        st.session_state["weight_input"] = weight_default
        st.session_state["reps_input"] = reps_default
        st.session_state["autofill_target"] = exercise_choice

    # --- ここで、キー付きウィジェットのデフォルト値を「まだ無い場合だけ」設定 ---
    st.session_state.setdefault("date_input", date.today())
    st.session_state.setdefault("new_exercise_input", "")
    st.session_state.setdefault("weight_input", 0.0)
    st.session_state.setdefault("reps_input", 0)
    st.session_state.setdefault("note_input", "")

    st.caption("※ 以前に記録した種目を選ぶと、重量・回数が自動で入ります")

    with st.form("training_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            date_val = st.date_input(
                "日付",
                key="date_input",
            )
            new_exercise = st.text_input(
                "新しい種目名（「＋ 新しい種目を追加」を選んだ場合に入力）",
                key="new_exercise_input",
            )
        with col2:
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

            if not exercise:
                st.error("「種目名」を入力（または選択）してください。")
            elif weight <= 0 and reps <= 0:
                st.error("「重量」と「回数」の両方を入力してください。")
            else:
                part_str = ", ".join(parts)
                row_index = st.session_state.get("edit_row_index")

                with st.spinner("保存中..."):
                    if editing_mode and row_index is not None:
                        ok = update_workout_data(
                            int(row_index),
                            [str(date_val), exercise, weight, reps, part_str, note],
                        )
                    else:
                        ok = add_workout_data([str(date_val), exercise, weight, reps, part_str, note])
                                        
                if ok:
                    st.toast("記録しました。" if not editing_mode else "更新しました。")

                    # 編集モードだけ解除し、入力内容（日付・種目・重量・回数・部位・メモ）はそのまま残す
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
        st.session_state["parts_input"] = [
            p.strip() for p in str(row.get("Part", "")).split(",") if p.strip()
        ]
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
            with st.container():
                cols = st.columns([2.2, 1.0, 0.8, 0.8, 1.0])
                with cols[0]:
                    st.write(f"{row.get('Date', '')} · {row.get('Exercise', '')}")
                with cols[1]:
                    st.caption(f"重量: {row.get('Weight', '')}kg")
                with cols[2]:
                    st.caption(f"回数: {row.get('Reps', '')}")
                with cols[3]:
                    st.caption(f"部位: {row.get('Part', '')}")
                with cols[4]:
                    st.button(
                        "編集",
                        key=f"edit-{row_index}",
                        use_container_width=True,
                        on_click=start_edit,
                        args=(row_index, row),
                    )
                    st.button(
                        "削除",
                        key=f"delete-{row_index}",
                        use_container_width=True,
                        on_click=start_delete,
                        args=(row_index,),
                    )

                st.caption(f"メモ: {row.get('Note', '')}")
                st.divider()

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
            st.table(day_df[["Exercise", "Weight", "Reps", "Part", "Note"]])
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