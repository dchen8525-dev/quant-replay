from __future__ import annotations

import streamlit as st

from src import database
from src.pages.account import account_page
from src.pages.backtest import backtest_page
from src.pages.dashboard import dashboard_page
from src.pages.diagnostics import diagnostics_page
from src.pages.factors import factors_page
from src.pages.new_trade import new_trade_page
from src.pages.portfolio import portfolio_page
from src.pages.review import review_page
from src.pages.strength import strength_page
from src.pages.trade_analysis import trade_analysis_page
from src.pages.trade_history import trade_history_page
from src.pages.watchlist import watchlist_page

PAGES = {
    "Dashboard": dashboard_page,
    "Strategy Backtest": backtest_page,
    "Simulated Account": account_page,
    "Strength Ranking": strength_page,
    "Review Report": review_page,
    "Factor Research": factors_page,
    "Portfolio Lab": portfolio_page,
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
