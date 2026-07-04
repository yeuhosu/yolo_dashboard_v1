import gspread
import pandas as pd
import streamlit as st

def get_gc():
    # Streamlit CloudのSecretsから読み込む
    return gspread.service_account_from_dict(st.secrets["gcp"])
  
  
@st.cache_data(ttl=60)
def get_sheet_data():
    try:
        gc = get_gc()
        sh = gc.open("거인화 4일버전 ver1.0") 
        worksheet = sh.worksheet("raw_data")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
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
      
