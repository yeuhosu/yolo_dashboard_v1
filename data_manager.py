import gspread
import pandas as pd
import streamlit as st


def get_gc():
    return gspread.service_account_from_dict(st.secrets["gcp"])


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


def get_sheet_data():
    try:
        gc = get_gc()
        sh = gc.open("거인화 4일버전 ver1.0")
        worksheet = sh.worksheet("raw_data")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        df = normalize_dataframe_columns(df)
        if not df.empty:
            df["RowIndex"] = list(range(2, len(df) + 2))
        return df
    except Exception as e:
        st.error(f"読み込みエラー: {e}")
        return pd.DataFrame()


def add_workout_data(data_list):
    try:
        gc = get_gc()
        sh = gc.open("거인화 4일버전 ver1.0")
        worksheet = sh.worksheet("raw_data")
        worksheet.append_row(data_list)
        return True
    except Exception as e:
        st.error(f"書き込みエラー: {e}")
        return False


def update_workout_data(row_index, data_list):
    try:
        gc = get_gc()
        sh = gc.open("거인화 4일버전 ver1.0")
        worksheet = sh.worksheet("raw_data")
        # A列から順に、data_list の長さ分だけその行を上書きする
        end_col = gspread.utils.rowcol_to_a1(1, len(data_list)).rstrip("1")
        range_name = f"A{row_index}:{end_col}{row_index}"
        worksheet.update(range_name=range_name, values=[data_list])
        return True
    except Exception as e:
        st.error(f"更新エラー: {e}")
        return False


def delete_workout_data(row_index):
    try:
        gc = get_gc()
        sh = gc.open("거인화 4일버전 ver1.0")
        worksheet = sh.worksheet("raw_data")
        worksheet.delete_rows(row_index)
        return True
    except Exception as e:
        st.error(f"削除エラー: {e}")
        return False