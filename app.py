from __future__ import annotations

import streamlit as st

from src import database
from src.pages.dashboard import dashboard_page
from src.pages.diagnostics import diagnostics_page
from src.pages.new_trade import new_trade_page
from src.pages.trade_analysis import trade_analysis_page
from src.pages.trade_history import trade_history_page
from src.pages.watchlist import watchlist_page

PAGES = {
    "Dashboard": dashboard_page,
    "New Simulated Trade": new_trade_page,
    "Trade Analysis": trade_analysis_page,
    "Trade History": trade_history_page,
    "Watchlist": watchlist_page,
    "Data Diagnostics": diagnostics_page,
}


def main() -> None:
    st.set_page_config(page_title="QuantReplay", layout="wide")
    database.init_db()
    st.title("QuantReplay")
    page = st.sidebar.radio("页面", list(PAGES))
    PAGES[page]()


if __name__ == "__main__":
    main()
