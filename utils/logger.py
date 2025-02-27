import streamlit as st
from datetime import datetime

def add_log(message, level="info"):
    """Add a log message and show a toast notification"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Store in session state for history
    st.session_state.log_messages.append({
        "timestamp": timestamp,
        "level": level,
        "message": message
    })
    
    # Show toast notification
    if level == "error":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    elif level == "success":
        st.success(message)
    else:
        st.toast(message)

def display_logs(filter_level="All"):
    """Display filtered log messages"""
    filtered_logs = st.session_state.log_messages
    if filter_level != "All":
        filtered_logs = [log for log in filtered_logs if log["level"].lower() == filter_level.lower()]
    
    for log in filtered_logs:
        level = log["level"]
        timestamp = log["timestamp"]
        message = log["message"]
        
        css_class = f"log-{level.lower()}"
        st.markdown(f"<div class='{css_class}'><small>{timestamp}</small><br>{message}</div>", unsafe_allow_html=True)

def clear_logs():
    """Clear all log messages"""
    st.session_state.log_messages = [] 