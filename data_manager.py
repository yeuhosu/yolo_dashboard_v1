import gspread
import pandas as pd
import streamlit as st

SPREADSHEET_NAME = "거인화 4일버전 ver1.0"
WORKSHEET_NAME = "raw_data"


def get_gc():
    return gspread.service_account_from_dict(st.secrets["gcp"])


@st.cache_resource
def _get_worksheet():
    # 認証とシートのオープンは毎回やらず、プロセス内で使い回す
    return get_gc().open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)


def normalize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty and len(df.columns) == 0:
        return df

    normalized_df = df.copy()
    normalized_df.columns = [col.strip() if isinstance(col, str) else col for col in normalized_df.columns]

    # 2. Calories列の空文字や不正な値を数値に変換し、失敗したものは NaN（または0）にする
    if "Calories" in normalized_df.columns:
        normalized_df["Calories"] = pd.to_numeric(
            normalized_df["Calories"].astype(str).str.strip(), errors="coerce"
        ).fillna(0)  # 欠損値を0にする場合
    # Duration列など、他の数値列で同じエラーが起きる可能性がある場合は一緒に処理すると安全です
    if "Duration" in normalized_df.columns:
        normalized_df["Duration"] = pd.to_numeric(
            normalized_df["Duration"].astype(str).str.strip(),
            errors="coerce",
        )

    return normalized_df


@st.cache_data(ttl=600, show_spinner=False)
def _load_records() -> pd.DataFrame:
    # 例外はここで握りつぶさない（失敗時の空データをキャッシュしないため）
    data = _get_worksheet().get_all_records()
    df = pd.DataFrame(data)
    df = normalize_dataframe_columns(df)
    if not df.empty:
        df["RowIndex"] = list(range(2, len(df) + 2))
    return df


def _invalidate_cache():
    _load_records.clear()


def get_sheet_data():
    try:
        df = _load_records()
        st.session_state["_last_good_df"] = df
        return df
    except Exception as e:
        # 接続が切れていた等で認証情報が古くなっている可能性があるので作り直す
        _get_worksheet.clear()
        last_good = st.session_state.get("_last_good_df")
        if last_good is not None:
            st.warning(f"最新データの読み込みに失敗したため、前回のデータを表示しています: {e}")
            return last_good
        st.error(f"読み込みエラー: {e}")
        return pd.DataFrame()


def add_workout_data(data_list):
    try:
        _get_worksheet().append_row(data_list)
        _invalidate_cache()
        return True
    except Exception as e:
        _get_worksheet.clear()
        st.error(f"書き込みエラー: {e}")
        return False


def update_workout_data(row_index, data_list):
    try:
        # A列から順に、data_list の長さ分だけその行を上書きする
        end_col = gspread.utils.rowcol_to_a1(1, len(data_list)).rstrip("1")
        range_name = f"A{row_index}:{end_col}{row_index}"
        _get_worksheet().update(range_name=range_name, values=[data_list])
        _invalidate_cache()
        return True
    except Exception as e:
        _get_worksheet.clear()
        st.error(f"更新エラー: {e}")
        return False


def delete_workout_data(row_index):
    try:
        _get_worksheet().delete_rows(row_index)
        _invalidate_cache()
        return True
    except Exception as e:
        _get_worksheet.clear()
        st.error(f"削除エラー: {e}")
        return False
