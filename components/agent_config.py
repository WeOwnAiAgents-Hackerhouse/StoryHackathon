import streamlit as st
import json
import asyncio
from utils.logger import add_log

def agent_configuration():
    """Agent configuration component"""
    st.markdown('<h2 class="sub-header">Step 2: Agent Configuration</h2>', unsafe_allow_html=True)
    st.markdown("""
    Configure your agent swarm. Define the agents' capabilities, models, and parameters. This establishes the ATCP layer.
    """)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h3 class="sub-header">Model Selection</h3>', unsafe_allow_html=True)
        
        coordinator_model = st.selectbox(
            "Coordinator Agent Model", 
            ["gpt-4", "claude-3", "gemini-pro"],
            key="coordinator_model_select"
        )
        
        valuation_model = st.selectbox(
            "Valuation Agent Model", 
            ["gpt-4", "claude-3", "gemini-pro"],
            key="valuation_model_select"
        )
        
        negotiation_model = st.selectbox(
            "Negotiation Agent Model", 
            ["gpt-4", "claude-3", "gemini-pro"],
            key="negotiation_model_select"
        )
        
        buyer_model = st.selectbox(
            "Buyer Agent Model", 
            ["gpt-4", "claude-3", "gemini-pro"],
            key="buyer_model_select"
        )
        
        seller_model = st.selectbox(
            "Seller Agent Model", 
            ["gpt-4", "claude-3", "gemini-pro"],
            key="seller_model_select"
        )
    
    with col2:
        st.markdown('<h3 class="sub-header">Agent Parameters</h3>', unsafe_allow_html=True)
        
        temperature = st.slider("Temperature", 0.0, 1.0, 0.7, key="temperature_slider")
        max_tokens = st.slider("Max Tokens", 100, 4000, 2000, key="max_tokens_slider")
        api_key = st.text_input("LLM API Key", type="password", key="api_key_input")
        
        if st.button("Configure Agents"):
            try:
                # Import agent classes
                from examples.agents.story_multi_agent_example import (
                    ValuationAgent, BuyerAgent, SellerAgent, NegotiationAgent, CoordinatorAgent
                )
                
                # Configure agents
                valuation_agent = ValuationAgent(
                    model=valuation_model,
                    temperature=temperature,
                    api_key=api_key
                )
                
                buyer_agent = BuyerAgent(
                    model=buyer_model,
                    temperature=temperature,
                    api_key=api_key
                )
                
                seller_agent = SellerAgent(
                    model=seller_model,
                    temperature=temperature,
                    api_key=api_key
                )
                
                negotiation_agent = NegotiationAgent(
                    model=negotiation_model,
                    temperature=temperature,
                    api_key=api_key
                )
                
                # Configure coordinator agent
                st.session_state.coordinator = CoordinatorAgent(
                    model=coordinator_model,
                    valuation_agent=valuation_agent,
                    buyer_agent=buyer_agent,
                    seller_agent=seller_agent,
                    negotiation_agent=negotiation_agent,
                    story_api=st.session_state.story_api,
                    temperature=temperature,
                    api_key=api_key
                )
                
                st.session_state.agents_configured = True
                
                add_log("Agent swarm configured successfully")
                st.success("Agent swarm configured successfully!")
            
            except Exception as e:
                add_log(f"Error configuring agents: {str(e)}", level="error")
                st.error(f"Error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.agents_configured:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 class="sub-header">Agent Swarm Status</h3>', unsafe_allow_html=True)
        
        st.markdown(f"""
        ✅ **Coordinator Agent**: Configured with {coordinator_model}  
        ✅ **Valuation Agent**: Configured with {valuation_model}  
        ✅ **Buyer Agent**: Configured with {buyer_model}  
        ✅ **Seller Agent**: Configured with {seller_model}  
        ✅ **Negotiation Agent**: Configured with {negotiation_model}
        
        The agent swarm is ready to assist with IP asset management.
        """)
        
        st.markdown('</div>', unsafe_allow_html=True) 