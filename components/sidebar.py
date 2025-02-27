import streamlit as st
from utils.logger import display_logs, clear_logs

def render_sidebar():
    """Render the sidebar with system status"""
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=AlphaSwarm", width=150)
        st.markdown("## AlphaSwarm ATCP/IP Studio")
        
        st.markdown("### ATCP/IP System Status")
        
        status_items = [
            ("Wallet Connected (TCP)", st.session_state.wallet_connected),
            ("Agent Swarm Configured (ATCP)", st.session_state.agents_configured),
            ("IP Asset Registered (IP)", st.session_state.ip_registered),
            ("License Terms Created (IP)", st.session_state.license_created),
            ("License Terms Attached (IP)", st.session_state.license_attached),
            ("Negotiation Protocol Active (TCP/IP)", st.session_state.negotiation_started),
            ("Transaction Finalized (TCP/IP)", st.session_state.transaction_finalized)
        ]
        
        for item, status in status_items:
            if status:
                st.markdown(f"✅ {item}")
            else:
                st.markdown(f"⚪ {item}")
        
        st.markdown("### Activity Log")
        log_filter = st.selectbox("Filter", ["All", "Info", "Warning", "Error", "Success"], key="log_filter_select")
        
        log_container = st.container()
        
        with log_container:
            display_logs(log_filter)
        
        if st.button("Clear Log"):
            clear_logs() 