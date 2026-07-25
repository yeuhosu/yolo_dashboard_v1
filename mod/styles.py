# CSS 関係をここにまとめることでapp.pyの可読性を上げる
# ライブラリのインポート
import streamlit as st

def inject_global_css():
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

def inject_day_button_css(button_key: str, color: str):
    st.markdown(
        f"""
        <style>
        .st-key-{button_key} button {{
            background-color: {color} !important;
            color: white !important;
            font-weight: 600;
            border-radius: 10px;
            padding: 8px 6px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )