"""
IRP Retirement Tracker - Main Streamlit Application
A web application for tracking Korean IRP toward 400M KRW retirement goal by December 2030.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from data_handler import load_data, save_data
from utils import calculate_progress, format_currency

# Page configuration
st.set_page_config(
    page_title="IRP Retirement Tracker",
    page_icon="💰",
    layout="wide"
)

def main():
    st.title("🎯 IRP Retirement Tracker")
    st.markdown("Track your progress toward **400M KRW** by December 2030")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["Dashboard", "Track Deposits", "RSU Tracking", "Market Dashboard", 
         "Rebalancing", "Projections", "Reports"]
    )
    
    # Load data
    data = load_data()
    
    if page == "Dashboard":
        show_dashboard(data)
    elif page == "Track Deposits":
        show_deposits(data)
    elif page == "RSU Tracking":
        show_rsu(data)
    elif page == "Market Dashboard":
        show_market()
    elif page == "Rebalancing":
        show_rebalancing(data)
    elif page == "Projections":
        show_projections(data)
    elif page == "Reports":
        show_reports(data)

def show_dashboard(data):
    """Display main dashboard with progress metrics"""
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    current_balance = data.get("current_balance", 175_700_000)
    target = 400_000_000
    progress = (current_balance / target) * 100
    
    with col1:
        st.metric("Current Balance", format_currency(current_balance))
    with col2:
        st.metric("Target Goal", format_currency(target))
    with col3:
        st.metric("Progress", f"{progress:.1f}%")
    with col4:
        st.metric("Days Remaining", calculate_days_remaining())
    
    # Progress bar
    st.progress(min(progress / 100, 1.0))
    
    st.info("Dashboard visualization coming soon...")

def show_deposits(data):
    """Track monthly deposits"""
    st.header("💵 Track Deposits")
    st.info("Deposit tracking coming soon...")

def show_rsu(data):
    """Track RSU vesting"""
    st.header("📈 RSU Tracking")
    st.info("RSU tracking coming soon...")

def show_market():
    """Display market dashboard"""
    st.header("🌍 Market Dashboard")
    st.info("Market data coming soon...")

def show_rebalancing(data):
    """Rebalancing alerts and recommendations"""
    st.header("⚖️ Rebalancing")
    st.info("Rebalancing alerts coming soon...")

def show_projections(data):
    """Show balance projections"""
    st.header("🔮 Projections")
    st.info("Projections coming soon...")

def show_reports(data):
    """Generate reports"""
    st.header("📄 Reports")
    st.info("Reports coming soon...")

def calculate_days_remaining():
    """Calculate days until retirement target date"""
    target_date = datetime(2030, 12, 31)
    today = datetime.now()
    return (target_date - today).days

if __name__ == "__main__":
    main()
