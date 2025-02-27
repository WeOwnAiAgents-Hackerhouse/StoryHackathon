import streamlit as st
from utils.logger import add_log

def initialize_session_state():
    """Initialize all session state variables"""
    
    # System state
    if 'network' not in st.session_state:
        st.session_state.network = "testnet"
    if 'wallet_connected' not in st.session_state:
        st.session_state.wallet_connected = False
    if 'agents_configured' not in st.session_state:
        st.session_state.agents_configured = False
    if 'ip_registered' not in st.session_state:
        st.session_state.ip_registered = False
    if 'license_created' not in st.session_state:
        st.session_state.license_created = False
    if 'license_attached' not in st.session_state:
        st.session_state.license_attached = False
    if 'negotiation_started' not in st.session_state:
        st.session_state.negotiation_started = False
    if 'transaction_finalized' not in st.session_state:
        st.session_state.transaction_finalized = False
    
    # Data objects
    if 'story_api' not in st.session_state:
        st.session_state.story_api = None
    if 'coordinator' not in st.session_state:
        st.session_state.coordinator = None
    if 'ip_asset_id' not in st.session_state:
        st.session_state.ip_asset_id = None
    if 'license_terms_id' not in st.session_state:
        st.session_state.license_terms_id = None
    if 'negotiation_id' not in st.session_state:
        st.session_state.negotiation_id = None
    if 'transaction_id' not in st.session_state:
        st.session_state.transaction_id = None
    
    # User data
    if 'wallet_address' not in st.session_state:
        st.session_state.wallet_address = ""
    if 'wallet_balance' not in st.session_state:
        st.session_state.wallet_balance = 0
    
    # Collections
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    if 'royalties' not in st.session_state:
        st.session_state.royalties = []
    if 'ip_assets' not in st.session_state:
        st.session_state.ip_assets = []
    
    # Form data for each step (to preserve inputs)
    if 'wallet_form_data' not in st.session_state:
        st.session_state.wallet_form_data = {}
    if 'agent_form_data' not in st.session_state:
        st.session_state.agent_form_data = {}
    if 'ip_form_data' not in st.session_state:
        st.session_state.ip_form_data = {}
    if 'license_form_data' not in st.session_state:
        st.session_state.license_form_data = {}
    if 'negotiation_form_data' not in st.session_state:
        st.session_state.negotiation_form_data = {}
    
    # Navigation
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'steps' not in st.session_state:
        st.session_state.steps = [
            "Wallet Connection", 
            "Agent Configuration", 
            "IP Asset Registration", 
            "License Terms Definition", 
            "Transaction Negotiation", 
            "Asset Monitoring", 
            "Performance Analytics"
        ]
    
    # Step completion tracking
    if 'completed_steps' not in st.session_state:
        st.session_state.completed_steps = set()

def next_step():
    """
    Move to the next step in the workflow
    Preserves state and tracks completion
    """
    if st.session_state.current_step < len(st.session_state.steps) - 1:
        # Mark current step as completed
        st.session_state.completed_steps.add(st.session_state.current_step)
        # Move to next step
        st.session_state.current_step += 1
        add_log(f"Moved to step {st.session_state.current_step+1}: {st.session_state.steps[st.session_state.current_step]}")

def prev_step():
    """
    Move to the previous step in the workflow
    Preserves all state
    """
    if st.session_state.current_step > 0:
        st.session_state.current_step -= 1
        add_log(f"Returned to step {st.session_state.current_step+1}: {st.session_state.steps[st.session_state.current_step]}")

def save_form_data(step_name, data):
    """
    Save form data for a specific step to preserve inputs when navigating
    
    Args:
        step_name: Name of the step (e.g., 'wallet', 'agent', etc.)
        data: Dictionary of form data to save
    """
    form_key = f"{step_name}_form_data"
    if form_key in st.session_state:
        st.session_state[form_key].update(data)
    else:
        st.session_state[form_key] = data
    
    add_log(f"Saved form data for {step_name}")

def get_form_data(step_name, default=None):
    """
    Get saved form data for a specific step
    
    Args:
        step_name: Name of the step (e.g., 'wallet', 'agent', etc.)
        default: Default value if no data exists
    
    Returns:
        Dictionary of saved form data or default
    """
    form_key = f"{step_name}_form_data"
    return st.session_state.get(form_key, default if default is not None else {})

def can_proceed(current_step):
    """
    Check if user can proceed to the next step based on completion criteria
    
    Args:
        current_step: Current step index
    
    Returns:
        Boolean indicating if user can proceed
    """
    # Define requirements for each step
    requirements = [
        lambda: st.session_state.wallet_connected,  # Wallet Connection
        lambda: st.session_state.agents_configured,  # Agent Configuration
        lambda: st.session_state.ip_registered,     # IP Registration
        lambda: st.session_state.license_created and st.session_state.license_attached,  # License Terms
        lambda: st.session_state.negotiation_started,  # Negotiation
        lambda: True,  # Monitoring (always can proceed)
        lambda: True,  # Analytics (always can proceed)
    ]
    
    if current_step >= len(requirements):
        return False
    
    return requirements[current_step]() 