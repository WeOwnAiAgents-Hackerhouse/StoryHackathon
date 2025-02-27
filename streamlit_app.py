import streamlit as st
import json
import os
import asyncio
from datetime import datetime
import pandas as pd
import plotly.express as px
from typing import Dict, List, Optional, Any

# Import necessary AlphaSwarm components
from alphaswarm.agent.agent import AlphaSwarmAgent
from alphaswarm.tools.story import (
    QueryStoryIPAssets, RegisterIPAsset, GetIPAssetDetails, 
    CreateLicenseTerms, AttachLicenseTerms, MintLicenseToken, 
    EstimateIPAssetValue, MakeOffer, RespondToOffer, ClaimRoyalty,
    IPAsset, IPMetadata, IPType
)
from alphaswarm.services.story import StoryProtocolAPI
from examples.agents.story_multi_agent_example import (
    ValuationAgent, BuyerAgent, SellerAgent, NegotiationAgent, CoordinatorAgent
)


# Define functions for navigation
def next_step():
    if st.session_state.current_step < len(st.session_state.steps) - 1:
        st.session_state.current_step += 1

def prev_step():
    if st.session_state.current_step > 0:
        st.session_state.current_step -= 1


# Define the display_stepper function BEFORE it's called
def display_stepper(steps, current_step):
    """Display a custom stepper component using HTML/CSS"""
    
    html = """
    <style>
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin: 20px 0;
        position: relative;
    }
    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        z-index: 1;
    }
    .step-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .step-text {
        text-align: center;
        font-size: 12px;
        max-width: 100px;
    }
    .step-line {
        position: absolute;
        top: 15px;
        height: 2px;
        z-index: 0;
    }
    </style>
    <div class="stepper-container">
    """
    
    step_width = 100 / (len(steps) - 1) if len(steps) > 1 else 100
    
    for i, step in enumerate(steps):
        # Determine step color
        if i < current_step:
            circle_color = "#4CAF50"  # Completed - green
        elif i == current_step:
            circle_color = "#2196F3"  # Active - blue
        else:
            circle_color = "#9E9E9E"  # Inactive - gray
        
        # Add step circle and text
        html += f"""
        <div class="step">
            <div class="step-circle" style="background-color: {circle_color};">{i+1}</div>
            <div class="step-text">{step}</div>
        </div>
        """
        
        # Add connecting line (except for the last step)
        if i < len(steps) - 1:
            line_color = "#4CAF50" if i < current_step else "#9E9E9E"
            html += f"""
            <div class="step-line" style="left: {(i * step_width) + 15}%; width: {step_width}%; background-color: {line_color};"></div>
            """
    
    html += "</div>"
    return html  # Return HTML instead of directly rendering it
    """Display a custom stepper component using HTML/CSS"""
    
    html = """
    <style>
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin: 20px 0;
        position: relative;
    }
    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        z-index: 1;
    }
    .step-circle {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .step-text {
        text-align: center;
        font-size: 12px;
        max-width: 100px;
    }
    .step-line {
        position: absolute;
        top: 15px;
        height: 2px;
        z-index: 0;
    }
    </style>
    <div class="stepper-container">
    """
    
    step_width = 100 / (len(steps) - 1) if len(steps) > 1 else 100
    
    for i, step in enumerate(steps):
        # Determine step color
        if i < current_step:
            circle_color = "#4CAF50"  # Completed - green
        elif i == current_step:
            circle_color = "#2196F3"  # Active - blue
        else:
            circle_color = "#9E9E9E"  # Inactive - gray
        
        # Add step circle and text
        html += f"""
        <div class="step">
            <div class="step-circle" style="background-color: {circle_color};">{i+1}</div>
            <div class="step-text">{step}</div>
        </div>
        """
        
        # Add connecting line (except for the last step)
        if i < len(steps) - 1:
            line_color = "#4CAF50" if i < current_step else "#9E9E9E"
            html += f"""
            <div class="step-line" style="left: {(i * step_width) + 15}%; width: {step_width}%; background-color: {line_color};"></div>
            """
    
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# Helper function for logging
def add_log(message, level="info"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.log_messages.append({
        "timestamp": timestamp,
        "level": level,
        "message": message
    })

# StepperBar class for step-by-step navigation
class StepperBar:
    def __init__(self, steps, current_step=0, orientation='horizontal', 
                 active_color='#2196F3', completed_color='#4CAF50', inactive_color='#9E9E9E'):
        self.steps = steps
        self.current_step = current_step
        self.orientation = orientation
        self.active_color = active_color
        self.completed_color = completed_color
        self.inactive_color = inactive_color
    
    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
    
    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
    
    def go_to_step(self, step_index):
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
    
    def display(self):
        if self.orientation == 'horizontal':
            self._display_horizontal()
        else:
            self._display_vertical()
    
    def _display_horizontal(self):
        html = f"""
        <style>
        .stepper-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
            margin: 20px 0;
        }}
        .step {{
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 1;
        }}
        .step-circle {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .step-line {{
            position: absolute;
            top: 15px;
            height: 2px;
            z-index: 0;
        }}
        .step-text {{
            text-align: center;
            font-size: 12px;
            max-width: 100px;
        }}
        </style>
        <div class="stepper-container">
        """
        
        step_width = 100 / (len(self.steps) - 1) if len(self.steps) > 1 else 100
        
        for i, step in enumerate(self.steps):
            # Determine step color
            if i < self.current_step:
                circle_color = self.completed_color
            elif i == self.current_step:
                circle_color = self.active_color
            else:
                circle_color = self.inactive_color
            
            # Add step circle and text
            html += f"""
            <div class="step">
                <div class="step-circle" style="background-color: {circle_color};">{i+1}</div>
                <div class="step-text">{step}</div>
            </div>
            """
            
            # Add connecting line (except for the last step)
            if i < len(self.steps) - 1:
                line_color = self.completed_color if i < self.current_step else self.inactive_color
                html += f"""
                <div class="step-line" style="left: {(i * step_width) + 15}%; width: {step_width}%; background-color: {line_color};"></div>
                """
        
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
    
    def _display_vertical(self):
        html = f"""
        <style>
        .stepper-container-vertical {{
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            width: 100%;
            margin: 20px 0;
        }}
        .step-vertical {{
            display: flex;
            align-items: center;
            position: relative;
            width: 100%;
            margin-bottom: 20px;
        }}
        .step-circle-vertical {{
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-weight: bold;
            margin-right: 15px;
        }}
        .step-line-vertical {{
            position: absolute;
            left: 15px;
            width: 2px;
            z-index: 0;
            background-color: #ccc;
        }}
        .step-text-vertical {{
            font-size: 14px;
        }}
        </style>
        <div class="stepper-container-vertical">
        """
        
        for i, step in enumerate(self.steps):
            # Determine step color
            if i < self.current_step:
                circle_color = self.completed_color
            elif i == self.current_step:
                circle_color = self.active_color
            else:
                circle_color = self.inactive_color
            
            # Add step circle and text
            html += f"""
            <div class="step-vertical">
                <div class="step-circle-vertical" style="background-color: {circle_color};">{i+1}</div>
                <div class="step-text-vertical">{step}</div>
            </div>
            """
            
            # Add connecting line (except for the last step)
            if i < len(self.steps) - 1:
                line_color = self.completed_color if i < self.current_step else self.inactive_color
                line_height = 40  # Height between steps
                html += f"""
                <div class="step-line-vertical" style="top: {(i * line_height) + 30}px; height: {line_height}px; background-color: {line_color};"></div>
                """
        
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

# Set page configuration
st.set_page_config(
    page_title="AlphaSwarm ATCP/IP Studio",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        color: #1E88E5;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .sub-header {
        color: #0D47A1;
        font-weight: bold;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .log-info {
        color: #007bff;
    }
    .log-warning {
        color: #ffa500;
    }
    .log-error {
        color: #dc3545;
    }
    .log-success {
        color: #28a745;
    }
    .navigation-buttons {
        display: flex;
        justify-content: space-between;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)
if 'network' not in st.session_state:
    st.session_state.network = "testnet"
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
if 'ip_asset_id' not in st.session_state:
    st.session_state.ip_asset_id = None
if 'license_terms_id' not in st.session_state:
    st.session_state.license_terms_id = None
if 'negotiation_id' not in st.session_state:
    st.session_state.negotiation_id = None
if 'transaction_id' not in st.session_state:
    st.session_state.transaction_id = None
if 'coordinator' not in st.session_state:
    st.session_state.coordinator = None
if 'story_api' not in st.session_state:
    st.session_state.story_api = None
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
if 'royalties' not in st.session_state:
    st.session_state.royalties = []
if 'ip_assets' not in st.session_state:
    st.session_state.ip_assets = []
if 'wallet_address' not in st.session_state:
    st.session_state.wallet_address = ""
if 'wallet_balance' not in st.session_state:
    st.session_state.wallet_balance = 0
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'wallet_connected' not in st.session_state:
    st.session_state.wallet_connected = False
if 'steps' not in st.session_state:
    st.session_state.steps = ["Wallet Setup", "Agent Configuration", "IP Registration", "License Creation", "Negotiations", "Monitoring", "Analytics"]



# Define steps for the stepper
steps = [
    "Wallet Setup", 
    "Agent Configuration", 
    "IP Registration", 
    "License Creation", 
    "Negotiations", 
    "Monitoring", 
    "Analytics"
]

# Create stepper bar
stepper = StepperBar(steps, st.session_state.current_step)

# Header
st.markdown('<h1 class="main-header">AlphaSwarm ATCP/IP Studio</h1>', unsafe_allow_html=True)
st.markdown("Create, configure, and deploy agent swarms following the ATCP/IP architecture")

# Display stepper bar
display_stepper(steps, st.session_state.current_step)

# Sidebar for configuration and logs
with st.sidebar:
    st.markdown('<h2 class="sub-header">Configuration</h2>', unsafe_allow_html=True)
    
    # Network selection
    network = st.selectbox(
    "Network", 
    ["testnet", "mainnet"],
    key="network_select"
    )

    
    if network != st.session_state.network:
        st.session_state.network = network
        if st.session_state.story_api:
            st.session_state.story_api = StoryProtocolAPI(network=network)
            add_log(f"Network changed to {network}")
    
    # Initialize Story Protocol API
    if st.button("Initialize API"):
        try:
            st.session_state.story_api = StoryProtocolAPI(network=network)
            add_log(f"Initialized Story Protocol API on {network}")
            st.success(f"Successfully initialized Story Protocol API on {network}")
        except Exception as e:
            add_log(f"Error initializing API: {str(e)}", level="error")
            st.error(f"Error: {str(e)}")
    
    # Display contract addresses if API is initialized
    if st.session_state.story_api:
        with st.expander("Contract Addresses"):
            try:
                if hasattr(st.session_state.story_api, 'addresses'):
                    network = st.session_state.network
                    if network in st.session_state.story_api.addresses:
                        if 'core' in st.session_state.story_api.addresses[network]:
                            st.write("IP Asset Registry:", 
                                    st.session_state.story_api.addresses[network]['core'].get('IPAssetRegistry', 'N/A'))
                            st.write("License Registry:", 
                                    st.session_state.story_api.addresses[network]['core'].get('LicenseRegistry', 'N/A'))
                            st.write("Dispute Module:", 
                                    st.session_state.story_api.addresses[network]['core'].get('DisputeModule', 'N/A'))
                            st.write("Royalty Policy LAP:", 
                                    st.session_state.story_api.addresses[network]['core'].get('RoyaltyPolicyLAP', 'N/A'))
            except Exception as e:
                st.write("Error displaying contract addresses:", str(e))
    
    # System Status
    st.markdown("### System Status")
    
    status_items = [
        ("Wallet Setup", st.session_state.wallet_address != ""),
        ("Agent Configuration", st.session_state.agents_configured),
        ("IP Registration", st.session_state.ip_registered),
        ("License Creation", st.session_state.license_created),
        ("License Attachment", st.session_state.license_attached),
        ("Negotiation", st.session_state.negotiation_started),
        ("Transaction Finalized", st.session_state.transaction_finalized)
    ]
    
    for item, status in status_items:
        if status:
            st.markdown(f"✅ {item}")
        else:
            st.markdown(f"⚪ {item}")
    
    # Activity Log
    st.markdown("### Activity Log")
    log_filter = st.selectbox(
    "Filter", 
    ["All", "Info", "Warning", "Error", "Success"],
    key="log_filter_select"
    )

    
    log_container = st.container()
    
    with log_container:
        filtered_logs = st.session_state.log_messages
        if log_filter != "All":
            filtered_logs = [log for log in filtered_logs if log["level"].lower() == log_filter.lower()]
        
        for log in filtered_logs:
            level = log["level"]
            timestamp = log["timestamp"]
            message = log["message"]
            
            css_class = f"log-{level.lower()}"
            st.markdown(f"<div class='{css_class}'><small>{timestamp}</small><br>{message}</div>", unsafe_allow_html=True)
    
    if st.button("Clear Log"):
        st.session_state.log_messages = []
        st.experimental_rerun()

# Main content based on current step
if st.session_state.current_step == 0:
    # Step 1: Wallet Setup
    st.markdown('<h2 class="sub-header">Step 1: Wallet Setup</h2>', unsafe_allow_html=True)
    st.markdown("""
    Connect your wallet to interact with Story Protocol. This will be used for all transactions and IP registrations.
    """)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="sub-header">Wallet Configuration</h3>', unsafe_allow_html=True)
    
    wallet_address = st.text_input("Wallet Address", value=st.session_state.wallet_address if st.session_state.wallet_address else "0x123456789abcdef123456789abcdef123456789a")
    
    if st.button("Connect Wallet"):
        try:
            # In a real app, this would connect to a real wallet
            # For demo purposes, we'll just store the address
            st.session_state.wallet_address = wallet_address
            
            # Simulate fetching balance
            if st.session_state.network == "testnet":
                st.session_state.wallet_balance = 10.0  # Demo balance for testnet
            else:
                st.session_state.wallet_balance = 2.5   # Demo balance for mainnet
            
            add_log(f"Wallet connected: {wallet_address}")
            st.success(f"Wallet connected successfully! Balance: {st.session_state.wallet_balance} ETH")
        except Exception as e:
            add_log(f"Error connecting wallet: {str(e)}", level="error")
            st.error(f"Error: {str(e)}")
    
    if st.session_state.wallet_address:
        st.markdown(f"""
        <div style="margin-top: 20px; padding: 10px; background-color: #e8f4f8; border-radius: 5px;">
            <h4>Wallet Information</h4>
            <p><strong>Address:</strong> {st.session_state.wallet_address}</p>
            <p><strong>Balance:</strong> {st.session_state.wallet_balance} ETH</p>
            <p><strong>Network:</strong> {st.session_state.network}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 1:
    # Step 2: Agent Configuration
    st.markdown('<h2 class="sub-header">Step 2: Agent Configuration</h2>', unsafe_allow_html=True)
    st.markdown("""
    Configure your agent swarm following the ATCP/IP architecture. Each agent has a specialized role:
    - **Valuation Agent**: Analyzes and values IP assets
    - **Buyer Agent**: Represents potential licensees
    - **Seller Agent**: Represents IP owners
    - **Negotiation Agent**: Facilitates negotiations between buyers and sellers
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.current_step > 0:
            if st.button("Previous Step"):
                prev_step()

    with col3:
        if st.session_state.current_step < len(st.session_state.steps) - 1:
            if st.button("Next Step"):
                next_step()    
        if st.button("Configure Agent Swarm", disabled=not st.session_state.wallet_address):
            try:
                # Initialize agents
                valuation_agent = ValuationAgent()
                buyer_agent = BuyerAgent()
                seller_agent = SellerAgent()
                negotiation_agent = NegotiationAgent()
                
                # Initialize coordinator
                coordinator = CoordinatorAgent(
                    valuation_agent=valuation_agent,
                    buyer_agent=buyer_agent,
                    seller_agent=seller_agent,
                    negotiation_agent=negotiation_agent,
                    network=st.session_state.network
                )
                
                st.session_state.coordinator = coordinator
                st.session_state.agents_configured = True
                
                add_log("Agent swarm configured successfully")
                st.success("Agent swarm configured successfully!")
            except Exception as e:
                add_log(f"Error configuring agents: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")

elif st.session_state.current_step == 2:
    # Step 3: IP Registration
    st.markdown('<h2 class="sub-header">Step 3: IP Registration</h2>', unsafe_allow_html=True)
    st.markdown("""
    Register your intellectual property assets on Story Protocol. This establishes ownership and enables licensing and monetization.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">IP Metadata</h3>', unsafe_allow_html=True)
        
        title = st.text_input("Title", value="AI-Generated Artwork")
        description = st.text_area("Description", value="A beautiful landscape generated by an AI model")
        ip_type = st.selectbox(
    "IP Type", 
    ["Art", "Music", "Literature", "Code", "Other"],
    key="ip_type_select"
        )

        
        st.markdown('<h4>Attributes</h4>', unsafe_allow_html=True)
        attr_key1 = st.text_input("Attribute 1 Key", value="Model")
        attr_value1 = st.text_input("Attribute 1 Value", value="Stable Diffusion XL")
        
        attr_key2 = st.text_input("Attribute 2 Key", value="Prompt")
        attr_value2 = st.text_input("Attribute 2 Value", value="A serene mountain landscape with a lake at sunset")
        
        st.markdown('<h4>Creator Information</h4>', unsafe_allow_html=True)
        creator_name = st.text_input("Creator Name", value="AI Artist")
        creator_address = st.text_input("Creator Address", value=st.session_state.wallet_address)
        creator_share = st.slider("Contribution Percentage", 0, 100, 100)
        
        tags = st.text_input("Tags (comma separated)", value="ai, landscape, art")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Content Upload</h3>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Upload Content", type=["png", "jpg", "jpeg", "gif", "mp3", "mp4", "pdf", "txt"])
        
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Uploaded Content", use_column_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Registration Preview</h3>', unsafe_allow_html=True)
        
        if st.button("Generate Metadata Preview"):
            attributes = [
                {"key": attr_key1, "value": attr_value1},
                {"key": attr_key2, "value": attr_value2}
            ]
            
            creators = [
                {"name": creator_name, "address": creator_address, "contributionPercent": creator_share}
            ]
            
            tags_list = [tag.strip() for tag in tags.split(",")]
            
            metadata = {
                "title": title,
                "description": description,
                "ipType": ip_type,
                "attributes": attributes,
                "creators": creators,
                "tags": tags_list
            }
            
            st.json(metadata)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("Register IP Asset", disabled=not st.session_state.agents_configured):
        try:
            attributes = [
                {"key": attr_key1, "value": attr_value1},
                {"key": attr_key2, "value": attr_value2}
            ]
            
            creators = [
                {"address": creator_address, "share": creator_share}
            ]
            
            tags_list = [tag.strip() for tag in tags.split(",")]
            
            # Create IP metadata
            metadata = IPMetadata(
                title=title,
                description=description,
                ipType=IPType(ip_type),
                attributes=attributes,
                creators=creators,
                tags=tags_list
            )
            
            # Register IP asset
            register_tool = RegisterIPAsset(client=st.session_state.story_api)
            register_result = asyncio.run(register_tool.forward(
                metadata=json.dumps(metadata.__dict__, default=lambda o: o.value if isinstance(o, IPType) else o),
                owner_address=creator_address,
                network=st.session_state.network
            ))
            
            register_json = json.loads(register_result)
            
            if "ipId" in register_json:
                st.session_state.ip_asset_id = register_json["ipId"]
                st.session_state.ip_registered = True
                
                add_log(f"IP asset registered with ID: {st.session_state.ip_asset_id}")
                st.success(f"IP asset registered successfully! Asset ID: {st.session_state.ip_asset_id}")
            else:
                add_log(f"Error registering IP asset: {register_json.get('message', 'Unknown error')}", level="error")
                st.error(f"Error: {register_json.get('message', 'Unknown error')}")
        
        except Exception as e:
            add_log(f"Error registering IP asset: {str(e)}", level="error")
            st.error(f"Error: {str(e)}")

elif st.session_state.current_step == 3:
    # Step 4: License Creation
    st.markdown('<h2 class="sub-header">Step 4: License Creation</h2>', unsafe_allow_html=True)
    st.markdown("""
    Create and manage license terms for your IP assets. This defines how others can use your IP and how you'll be compensated.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Create License Terms</h3>', unsafe_allow_html=True)
        
        minting_fee = st.text_input("Minting Fee (ETH)", value="0.05")
        commercial_rev_share = st.slider("Commercial Revenue Share (%)", 0, 100, 10)
        
        # Convert percentage to basis points (1% = 100 basis points)
        commercial_rev_share_bp = commercial_rev_share * 100
        
        royalty_policy = st.text_input(
            "Royalty Policy Address (optional)", 
            value=""
        )
        
        if st.button("Create License Terms", disabled=not st.session_state.ip_registered):
            try:
                # Create license terms
                license_terms_tool = CreateLicenseTerms(client=st.session_state.story_api)
                license_terms_result = asyncio.run(license_terms_tool.forward(
                    minting_fee=minting_fee,
                    commercial_rev_share=commercial_rev_share_bp,
                    royalty_policy=royalty_policy,
                    network=st.session_state.network
                ))
                
                license_terms_json = json.loads(license_terms_result)
                
                if "licenseTermsId" in license_terms_json:
                    st.session_state.license_terms_id = license_terms_json["licenseTermsId"]
                    st.session_state.license_created = True
                    
                    add_log(f"License terms created with ID: {st.session_state.license_terms_id}")
                    st.success(f"License terms created successfully! Terms ID: {st.session_state.license_terms_id}")
                else:
                    add_log(f"Error creating license terms: {license_terms_json.get('message', 'Unknown error')}", level="error")
                    st.error(f"Error: {license_terms_json.get('message', 'Unknown error')}")
            
            except Exception as e:
                add_log(f"Error creating license terms: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Attach License Terms</h3>', unsafe_allow_html=True)
        
        ip_id = st.text_input("IP Asset ID", value=st.session_state.ip_asset_id if st.session_state.ip_asset_id else "")
        license_terms_id = st.text_input("License Terms ID", value=st.session_state.license_terms_id if st.session_state.license_terms_id else "")
        
        # Get license template address safely
        license_template = st.text_input(
            "License Template Address (optional)",
            value=""
        )
        
        if st.button("Attach License Terms", disabled=not st.session_state.license_created):
            try:
                # Attach license terms
                attach_tool = AttachLicenseTerms(client=st.session_state.story_api)
                attach_result = asyncio.run(attach_tool.forward(
                    ip_id=ip_id,
                    license_terms_id=license_terms_id,
                    license_template=license_template,
                    network=st.session_state.network
                ))
                
                attach_json = json.loads(attach_result)
                
                if attach_json.get("status") == "success":
                    st.session_state.license_attached = True
                    
                    add_log(f"License terms attached to IP asset {ip_id}")
                    st.success("License terms attached successfully!")
                else:
                    add_log(f"Error attaching license terms: {attach_json.get('message', 'Unknown error')}", level="error")
                    st.error(f"Error: {attach_json.get('message', 'Unknown error')}")
            
            except Exception as e:
                add_log(f"Error attaching license terms: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 4:
    # Step 5: Negotiations
    st.markdown('<h2 class="sub-header">Step 5: Negotiations</h2>', unsafe_allow_html=True)
    st.markdown("""
    Facilitate negotiations between buyers and sellers for IP licensing. The agent swarm handles the negotiation process automatically.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Start Negotiation</h3>', unsafe_allow_html=True)
        
        asset_id = st.text_input("IP Asset ID (Negotiation)", value=st.session_state.ip_asset_id if st.session_state.ip_asset_id else "")
        buyer_address = st.text_input("Buyer Address", value="0xBuYeR123456789abcdef0123456789abcdef")
        seller_address = st.text_input("Seller Address", value=st.session_state.wallet_address)
        
        if st.button("Start Negotiation", disabled=not st.session_state.license_attached or not st.session_state.agents_configured):
            try:
                # Start negotiation
                negotiation_response = asyncio.run(st.session_state.coordinator.start_negotiation(
                    asset_id=asset_id,
                    buyer_address=buyer_address,
                    seller_address=seller_address
                ))
                
                negotiation_result = json.loads(negotiation_response)
                
                if "negotiation_id" in negotiation_result:
                    st.session_state.negotiation_id = negotiation_result["negotiation_id"]
                    st.session_state.negotiation_started = True
                    
                    add_log(f"Negotiation started with ID: {st.session_state.negotiation_id}")
                    st.success(f"Negotiation started successfully! Negotiation ID: {st.session_state.negotiation_id}")
                else:
                    add_log(f"Error starting negotiation: {negotiation_result.get('message', 'Unknown error')}", level="error")
                    st.error(f"Error: {negotiation_result.get('message', 'Unknown error')}")
            
            except Exception as e:
                add_log(f"Error starting negotiation: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Process Offer</h3>', unsafe_allow_html=True)
        
        negotiation_id = st.text_input("Negotiation ID", value=st.session_state.negotiation_id if st.session_state.negotiation_id else "")
        offer_amount = st.text_input("Offer Amount (ETH)", value="0.4")
        
        if st.button("Process Offer", disabled=not st.session_state.negotiation_started):
            try:
                # Process offer
                offer_response = asyncio.run(st.session_state.coordinator.process_offer(
                    negotiation_id=negotiation_id,
                    offer_amount=offer_amount
                ))
                
                add_log(f"Offer processed: {offer_amount} ETH")
                st.success("Offer processed successfully!")
                st.json(offer_response)
            
            except Exception as e:
                add_log(f"Error processing offer: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Finalize Transaction</h3>', unsafe_allow_html=True)
        
        accepted_price = st.text_input("Accepted Price (ETH)", value="0.45")
        
        if st.button("Finalize Transaction", disabled=not st.session_state.negotiation_started):
            try:
                # Finalize transaction
                transaction_response = asyncio.run(st.session_state.coordinator.finalize_transaction(
                    negotiation_id=negotiation_id,
                    accepted_price=accepted_price
                ))
                
                st.session_state.transaction_finalized = True
                st.session_state.transaction_id = json.loads(transaction_response).get("transaction_id")
                
                add_log(f"Transaction finalized at {accepted_price} ETH")
                st.success("Transaction finalized successfully!")
                st.json(transaction_response)
            
            except Exception as e:
                add_log(f"Error finalizing transaction: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 5:
    # Step 6: Monitoring
    st.markdown('<h2 class="sub-header">Step 6: Monitoring</h2>', unsafe_allow_html=True)
    st.markdown("""
    Monitor your IP assets, licenses, negotiations, and transactions. Track royalty payments and dispute resolutions.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">IP Assets</h3>', unsafe_allow_html=True)
        
        if st.button("Refresh IP Assets"):
            try:
                # Query IP assets
                query_tool = QueryStoryIPAssets(client=st.session_state.story_api)
                assets_result = asyncio.run(query_tool.forward(
                    owner_address=st.session_state.wallet_address,
                    network=st.session_state.network
                ))
                
                assets_json = json.loads(assets_result)
                
                if "assets" in assets_json:
                    st.session_state.ip_assets = assets_json["assets"]
                    add_log(f"Retrieved {len(st.session_state.ip_assets)} IP assets")
                else:
                    add_log(f"Error retrieving IP assets: {assets_json.get('message', 'Unknown error')}", level="error")
            
            except Exception as e:
                add_log(f"Error retrieving IP assets: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")
        
        if st.session_state.ip_assets:
            for asset in st.session_state.ip_assets:
                st.markdown(f"""
                **Asset ID**: {asset.get('id')}  
                **Title**: {asset.get('title')}  
                **Type**: {asset.get('type')}  
                **Creation Date**: {asset.get('creation_date')}
                """)
                st.markdown("---")
        else:
            st.info("No IP assets found")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Transactions</h3>', unsafe_allow_html=True)
        
        if st.button("Refresh Transactions"):
            # In a real app, you would query transactions from the blockchain
            # For this example, we'll just use the transaction we created
            if st.session_state.transaction_id:
                transaction = {
                    "id": st.session_state.transaction_id,
                    "asset_id": st.session_state.ip_asset_id,
                    "buyer": "0xBuYeR123456789abcdef0123456789abcdef",
                    "seller": st.session_state.wallet_address,
                    "price": float(accepted_price),
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "completed"
                }
                
                if transaction not in st.session_state.transactions:
                    st.session_state.transactions.append(transaction)
                
                add_log(f"Retrieved {len(st.session_state.transactions)} transactions")
        
        if st.session_state.transactions:
            for tx in st.session_state.transactions:
                st.markdown(f"""
                **Transaction ID**: {tx.get('id')}  
                **Asset ID**: {tx.get('asset_id')}  
                **Price**: {tx.get('price')} ETH  
                **Date**: {tx.get('date')}  
                **Status**: {tx.get('status')}
                """)
                st.markdown("---")
        else:
            st.info("No transactions found")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Royalties section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="sub-header">Royalties</h3>', unsafe_allow_html=True)
    
    if st.button("Check Royalties"):
        # In a real app, you would query royalties from the blockchain
        # For this example, we'll create a sample royalty
        if st.session_state.transaction_id and st.session_state.ip_asset_id:
            royalty = {
                "id": f"roy_{st.session_state.transaction_id}",
                "asset_id": st.session_state.ip_asset_id,
                "amount": float(accepted_price) * 0.1,  # 10% royalty
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "pending"
            }
            
            if royalty not in st.session_state.royalties:
                st.session_state.royalties.append(royalty)
            
            add_log(f"Retrieved {len(st.session_state.royalties)} royalties")
    
    if st.session_state.royalties:
        for roy in st.session_state.royalties:
            st.markdown(f"""
            **Royalty ID**: {roy.get('id')}  
            **Asset ID**: {roy.get('asset_id')}  
            **Amount**: {roy.get('amount')} ETH  
            **Date**: {roy.get('date')}  
            **Status**: {roy.get('status')}
            """)
            
            if roy.get('status') == "pending":
                if st.button(f"Claim Royalty {roy.get('id')}"):
                    try:
                        # Claim royalty
                        claim_tool = ClaimRoyalty(client=st.session_state.story_api)
                        claim_result = asyncio.run(claim_tool.forward(
                            ip_id=roy.get('asset_id'),
                            recipient=st.session_state.wallet_address,
                            network=st.session_state.network
                        ))
                        
                        claim_json = json.loads(claim_result)
                        
                        if claim_json.get("status") == "success":
                            # Update royalty status
                            roy['status'] = "claimed"
                            add_log(f"Royalty {roy.get('id')} claimed successfully")
                            st.success(f"Royalty {roy.get('id')} claimed successfully")
                        else:
                            add_log(f"Error claiming royalty: {claim_json.get('message', 'Unknown error')}", level="error")
                            st.error(f"Error: {claim_json.get('message', 'Unknown error')}")
                    
                    except Exception as e:
                        add_log(f"Error claiming royalty: {str(e)}", level="error")
                        st.error(f"Error: {str(e)}")
            
            st.markdown("---")
    else:
        st.info("No royalties found")
    
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_step == 6:
    # Step 7: Analytics
    st.markdown('<h2 class="sub-header">Step 7: Analytics</h2>', unsafe_allow_html=True)
    st.markdown("""
    Analyze your IP assets, transactions, and royalties. Track performance and trends.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Transaction Overview</h3>', unsafe_allow_html=True)
        
        if not st.session_state.transactions:
            st.info("No transaction data available for visualization")
        else:
            df_transactions = pd.DataFrame(st.session_state.transactions)
            
            # Create a bar chart of transaction values
            if 'price' in df_transactions.columns:
                fig = px.bar(df_transactions, x='id', y='price', title="Transaction Values (ETH)")
                st.plotly_chart(fig, use_container_width=True)
            
            # Transaction status breakdown
            if 'status' in df_transactions.columns:
                status_counts = df_transactions['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                fig = px.pie(status_counts, values='Count', names='Status', title="Transaction Status Breakdown")
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Royalty Analysis</h3>', unsafe_allow_html=True)
        
        if not st.session_state.royalties:
            st.info("No royalty data available for visualization")
        else:
            df_royalties = pd.DataFrame(st.session_state.royalties)
            
            # Convert date to datetime
            df_royalties['date'] = pd.to_datetime(df_royalties['date'])
            
            # Sort by date
            df_royalties = df_royalties.sort_values('date')
            
            # Create a line chart of royalties over time
            fig = px.line(df_royalties, x='date', y='amount', title="Royalties Over Time (ETH)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Royalties by asset
            fig = px.pie(df_royalties, values='amount', names='asset_id', title="Royalties by Asset")
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Combined analytics section
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h3 class="sub-header">IP Asset Performance</h3>', unsafe_allow_html=True)
    
    if not st.session_state.ip_assets or not st.session_state.transactions:
        st.info("Insufficient data for IP asset performance analysis")
    else:
        # Create a combined dataframe with asset and transaction data
        assets_df = pd.DataFrame(st.session_state.ip_assets)
        transactions_df = pd.DataFrame(st.session_state.transactions)
        
        # Merge on asset ID to get performance metrics
        if 'id' in assets_df.columns and 'asset_id' in transactions_df.columns:
            performance_df = pd.merge(
                assets_df, 
                transactions_df.groupby('asset_id').agg({
                    'price': ['sum', 'mean', 'count']
                }).reset_index(),
                left_on='id', 
                right_on='asset_id',
                how='left'
            )
            
            performance_df.columns = [
                'id', 'title', 'type', 'creation_date', 'owner',
                'asset_id', 'total_value', 'average_value', 'transaction_count'
            ]
            
            # Create a scatter plot of total value vs. transaction count
            fig = px.scatter(
                performance_df, 
                x='transaction_count', 
                y='total_value',
                size='average_value',
                color='type',
                hover_name='title',
                title="IP Asset Performance"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Navigation buttons
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.session_state.current_step > 0:
        if st.button("Previous Step"):
            st.session_state.stepper.prev_step()
            st.session_state.current_step = st.session_state.stepper.current_step

with col3:
    if st.session_state.current_step < len(st.session_state.steps) - 1:
        if st.button("Next Step"):
            next_step()

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


# Sidebar for logs and status
# Update sidebar system status section
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
    log_filter = st.selectbox("Filter", ["All", "Info", "Warning", "Error", "Success"])
    
    log_container = st.container()
    
    with log_container:
        filtered_logs = st.session_state.log_messages
        if log_filter != "All":
            filtered_logs = [log for log in filtered_logs if log["level"].lower() == log_filter.lower()]
        
        for log in filtered_logs:
            level = log["level"]
            timestamp = log["timestamp"]
            message = log["message"]
            
            css_class = f"log-{level.lower()}"
            st.markdown(f"<div class='{css_class}'><small>{timestamp}</small><br>{message}</div>", unsafe_allow_html=True)
    
    if st.button("Clear Log"):
        st.session_state.log_messages = []