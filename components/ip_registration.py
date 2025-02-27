import streamlit as st
import json
import asyncio
from utils.logger import add_log
from alphaswarm.tools.story import RegisterIPAsset, IPMetadata, IPType

def ip_registration():
    """IP Asset Registration component"""
    st.markdown('<h2 class="sub-header">Step 3: IP Asset Registration</h2>', unsafe_allow_html=True)
    st.markdown("""
    Register your intellectual property assets on the Story Protocol. This establishes the IP layer.
    """)
    
    # Implement your IP registration UI and logic here
    # Use the existing code from your application
    
    # Don't forget to use unique keys for all interactive elements
    # Example: st.text_input("Title", key="ip_title_input") 