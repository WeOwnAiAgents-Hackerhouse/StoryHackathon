import streamlit as st
import os
import json

# Import utility modules
from utils.session import initialize_session_state
from utils.logger import add_log

# Import components
from components.sidebar import render_sidebar
from components.wallet import wallet_setup
from components.agent_config import agent_configuration
from components.ip_registration import ip_registration
from components.license_manager import license_manager
from components.negotiation import negotiation
from components.monitoring import asset_monitoring
from components.analytics import performance_analytics

# Initialize session state
initialize_session_state()

# App header and CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 1rem;
}
.sub-header {
    font-size: 1.5rem;
    font-weight: 600;
    color: #f0f0f0;
    margin-bottom: 0.5rem;
}
.card {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.log-info {
    background-color: rgba(33, 150, 243, 0.1);
    border-left: 4px solid #2196F3;
    padding: 10px;
    margin-bottom: 8px;
}
.log-warning {
    background-color: rgba(255, 193, 7, 0.1);
    border-left: 4px solid #FFC107;
    padding: 10px;
    margin-bottom: 8px;
}
.log-error {
    background-color: rgba(244, 67, 54, 0.1);
    border-left: 4px solid #F44336;
    padding: 10px;
    margin-bottom: 8px;
}
.log-success {
    background-color: rgba(76, 175, 80, 0.1);
    border-left: 4px solid #4CAF50;
    padding: 10px;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# Main app header
st.markdown('<h1 class="main-header">AlphaSwarm ATCP/IP Studio</h1>', unsafe_allow_html=True)
st.markdown("Create, configure, and deploy agent swarms following the ATCP/IP architecture")

# Create tabs for module navigation - this replaces the stepper
tab_names = [
    "Wallet Connection", 
    "Agent Configuration", 
    "IP Asset Registration", 
    "License Terms Definition", 
    "Transaction Negotiation", 
    "Asset Monitoring", 
    "Performance Analytics"
]

# Store the selected tab index in session state to maintain it between reruns
if "selected_tab" not in st.session_state:
    st.session_state.selected_tab = 0

# Create the tabs
tabs = st.tabs(tab_names)

# Function to handle tab-specific content
def render_tab_content(tab_index):
    # Render the corresponding component in each tab
    if tab_index == 0:
        wallet_setup()
    elif tab_index == 1:
        agent_configuration()
    elif tab_index == 2:
        ip_registration()
    elif tab_index == 3:
        license_manager()
    elif tab_index == 4:
        negotiation()
    elif tab_index == 5:
        asset_monitoring()
    elif tab_index == 6:
        performance_analytics()

# Display content of the selected tab
with tabs[st.session_state.selected_tab]:
    render_tab_content(st.session_state.selected_tab)

# Add tab navigation controls below the tabs for better flow
col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    if st.session_state.selected_tab > 0:
        if st.button("Previous Module", key="prev_module"):
            # Update the selected tab index
            st.session_state.selected_tab -= 1
            # Show a notification
            prev_tab_name = tab_names[st.session_state.selected_tab]
            st.toast(f"Navigating to: {prev_tab_name}")
            # Rerun to update the UI immediately
            st.rerun()

with col3:
    if st.session_state.selected_tab < len(tab_names) - 1:
        if st.button("Next Module", key="next_module"):
            # Update the selected tab index
            st.session_state.selected_tab += 1
            # Show a notification
            next_tab_name = tab_names[st.session_state.selected_tab]
            st.toast(f"Navigating to: {next_tab_name}")
            # Rerun to update the UI immediately
            st.rerun()

# Render sidebar
render_sidebar()