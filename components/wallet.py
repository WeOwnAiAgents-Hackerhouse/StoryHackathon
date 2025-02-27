import streamlit as st
import json
import asyncio
from utils.logger import add_log
from utils.session import save_form_data, get_form_data

def wallet_setup():
    """Wallet setup and connection component"""
    st.markdown('<h2 class="sub-header">Step 1: Wallet Connection</h2>', unsafe_allow_html=True)
    st.markdown("""
    Connect your wallet to interact with the Story Protocol. This establishes the TCP connection layer.
    """)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    # Get saved form data
    form_data = get_form_data('wallet')
    
    with col1:
        st.markdown('<h3 class="sub-header">Network Selection</h3>', unsafe_allow_html=True)
        
        network = st.selectbox(
            "Network", 
            ["testnet", "mainnet"], 
            index=0 if form_data.get('network') != 'mainnet' else 1,
            key="network_select"
        )
        
        rpc_url = st.text_input(
            "Story Protocol RPC URL", 
            value=form_data.get('rpc_url', "https://aeneid.storyrpc.io"), 
            key="rpc_url_input"
        )
        
        wallet_address = st.text_input(
            "Wallet Address", 
            value=form_data.get('wallet_address', st.session_state.wallet_address), 
            key="wallet_address_input"
        )
        
        private_key = st.text_input(
            "Private Key (optional)", 
            type="password", 
            key="private_key_input"
        )
        
        # Save form data as user inputs values
        save_form_data('wallet', {
            'network': network,
            'rpc_url': rpc_url,
            'wallet_address': wallet_address
        })
        
        if st.button("Connect Wallet", key="connect_wallet_button"):
            try:
                # Simulate wallet connection
                st.session_state.wallet_address = wallet_address
                st.session_state.wallet_balance = 10.0  # Sample balance
                st.session_state.wallet_connected = True
                st.session_state.network = network
                
                # Initialize Story Protocol API without wallet_address
                from alphaswarm.services.story import StoryProtocolAPI
                st.session_state.story_api = StoryProtocolAPI(
                    network=network,
                    rpc_url=rpc_url  # Removed wallet_address
                )
                
                add_log(f"Wallet connected: {wallet_address[:6]}...{wallet_address[-4:]}")
                st.success(f"Wallet connected successfully! Balance: {st.session_state.wallet_balance} ETH")
            
            except Exception as e:
                add_log(f"Error connecting wallet: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")
    
    with col2:
        st.markdown('<h3 class="sub-header">Wallet Information</h3>', unsafe_allow_html=True)
        
        if st.session_state.wallet_connected:
            st.markdown(f"""
            **Address**: {st.session_state.wallet_address}  
            **Balance**: {st.session_state.wallet_balance} ETH  
            **Network**: {st.session_state.network}
            
            ✅ Wallet is connected and ready for transactions
            """)
        else:
            st.info("Please connect your wallet to proceed with the ATCP/IP workflow")
    
    st.markdown('</div>', unsafe_allow_html=True) 