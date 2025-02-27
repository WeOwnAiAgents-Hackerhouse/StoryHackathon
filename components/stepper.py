import streamlit as st

def display_stepper(steps, current_step):
    """
    Display a custom stepper component using HTML/CSS
    
    Args:
        steps: List of step names
        current_step: Current step index (0-based)
    """
    # Calculate step width for positioning
    step_count = len(steps)
    step_width = 100 / (step_count - 1) if step_count > 1 else 100
    
    # Build the complete HTML including CSS in one string
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
        z-index: 2;
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
        z-index: 1;
    }
    </style>
    <div class="stepper-container">
    """
    
    # Add each step
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
    
    # Close the container div
    html += "</div>"
    
    # Add connecting lines separately (after all steps are added)
    html += """<style>"""
    for i in range(step_count - 1):
        line_color = "#4CAF50" if i < current_step else "#9E9E9E"
        left_pos = (i * step_width) + 15
        html += f"""
        .stepper-container:after {{
            content: "";
            position: absolute;
            left: {left_pos}%;
            width: {step_width}%;
            height: 2px;
            background-color: {line_color};
            top: 15px;
            z-index: 1;
        }}
        """
    html += """</style>"""
    
    # Render the complete HTML in a single call
    st.markdown(html, unsafe_allow_html=True)

def navigation_buttons():
    """
    Display navigation buttons for moving between steps
    Ensures state is preserved when navigating
    """
    from utils.session import next_step, prev_step
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.current_step > 0:
            if st.button("Previous Step", key="prev_step_button"):
                # Show notification
                st.toast(f"Moving back to: {st.session_state.steps[st.session_state.current_step-1]}")
                # Move to previous step
                prev_step()
                # Force a rerun to update the UI immediately
                st.rerun()

    with col3:
        if st.session_state.current_step < len(st.session_state.steps) - 1:
            if st.button("Next Step", key="next_step_button"):
                # Show notification
                st.toast(f"Moving to: {st.session_state.steps[st.session_state.current_step+1]}")
                # Move to next step
                next_step()
                # Force a rerun to update the UI immediately
                st.rerun()

def display_stepper_native(steps, current_step):
    """
    Display a stepper using Streamlit's native components
    
    Args:
        steps: List of step names
        current_step: Current step index (0-based)
    """
    # Create a container for the stepper
    stepper_container = st.container()
    
    with stepper_container:
        # Create columns for each step
        cols = st.columns(len(steps))
        
        # Display each step
        for i, (col, step) in enumerate(zip(cols, steps)):
            with col:
                # Determine step status
                if i < current_step:
                    status = "✅"  # Completed
                    color = "green"
                elif i == current_step:
                    status = f"**{i+1}**"  # Active
                    color = "blue"
                else:
                    status = str(i+1)  # Inactive
                    color = "gray"
                
                # Display step number and name
                st.markdown(f"<div style='text-align: center; color: {color};'>{status}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align: center; font-size: 12px; color: {color};'>{step}</div>", unsafe_allow_html=True)
        
        # Display progress bar
        progress = current_step / (len(steps) - 1) if len(steps) > 1 else 1.0
        st.progress(progress) 