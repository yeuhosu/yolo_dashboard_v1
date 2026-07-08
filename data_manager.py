import gspread
import pandas as pd
import streamlit as st


def get_gc():
    return gspread.service_account_from_dict(st.secrets["gcp"])


def get_sheet_data():
    try:
        gc = get_gc()
        sh = gc.open("거인화 4일버전 ver1.0")
        worksheet = sh.worksheet("raw_data")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
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
        worksheet.update(range_name, [data_list])
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