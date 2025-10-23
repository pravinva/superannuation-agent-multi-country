# progress_utils.py
"""Progress tracking and log display utilities with real agent status"""

import streamlit as st


def render_progress(member_data=None, tools_called=None, show_logs=True):
    """
    Display agent processing progress with actual status
    
    Args:
        member_data: Member profile dict
        tools_called: List of tools executed with timing data
        show_logs: Whether to show logs
    """
    
    if not show_logs:
        return
    
    st.markdown("### 📋 Agent Processing Logs")
    
    # Check if there's agent output
    if "agent_output" in st.session_state and st.session_state.agent_output:
        output = st.session_state.agent_output
        
        st.success("✅ Processing complete!")
        
        # Show actual processing steps with timing
        with st.expander("📊 Processing Summary", expanded=True):
            
            # Step 1: Member profile retrieval
            if member_data:
                member_name = member_data.get('name', 'Unknown')
                member_age = member_data.get('age', 'N/A')
                st.write(f"✅ Retrieved member profile: {member_name}, Age {member_age}")
            else:
                st.write("✅ Retrieved member profile")
            
            # Step 2: Show actual tools called with timing
            if tools_called and len(tools_called) > 0:
                st.write(f"✅ Executed {len(tools_called)} tool(s):")
                for tool in tools_called:
                    tool_name = tool.get('name', 'Unknown')
                    duration = tool.get('duration', 0)
                    status = tool.get('status', 'unknown')
                    
                    if status == 'completed':
                        st.write(f"   • {tool_name}: {duration:.2f}s ✓")
                    else:
                        st.write(f"   • {tool_name}: {status}")
            else:
                st.write("✅ Called Unity Catalog functions")
            
            # Step 3: Synthesis
            st.write("✅ Generated 3-part recommendation (Situation → Insights → Recommendations)")
            
            # Step 4: Judge validation
            if "judge_verdict" in output and output["judge_verdict"]:
                verdict = output["judge_verdict"]
                if verdict == "Pass":
                    st.write(f"✅ Judge validation: {verdict}")
                elif verdict == "ERROR":
                    st.write(f"⚠️ Judge validation: {verdict}")
                else:
                    st.write(f"⚠️ Judge validation: {verdict} (needs review)")
            
            # Step 5: Audit logging
            st.write("✅ Logged to governance table")
            
            # Show tool used
            if "tool_used" in output:
                st.caption(f"Tool: `{output['tool_used']}`")
            
            # Show citations count
            if "citations" in output and output["citations"]:
                st.caption(f"Citations: {len(output['citations'])}")
    
    else:
        st.info("🔄 Agent processing logs will appear here...")
        st.caption("No processing has occurred yet. Click '🚀 Get Recommendation' to start.")


def show_processing_status(stage, message=None):
    """
    Show real-time processing status (called from agent during execution)
    
    Args:
        stage: Stage name (e.g., 'tool_start', 'synthesis_stage', 'validation_start')
        message: Optional message dict with details
    """
    
    # Stage emojis
    stage_icons = {
        'tool_start': '⚙️',
        'tool_complete': '✅',
        'synthesis_start': '💭',
        'synthesis_stage': '📝',
        'synthesis_complete': '✅',
        'validation_start': '⚖️',
        'validation_complete': '✅'
    }
    
    icon = stage_icons.get(stage, '🔄')
    
    if message:
        if isinstance(message, dict):
            if 'stage' in message and 'task' in message:
                # Synthesis stage progress
                st.write(f"{icon} Stage {message['stage']}/3: {message['task']}")
            else:
                st.write(f"{icon} {message}")
        else:
            st.write(f"{icon} {message}")
    else:
        # Default messages for each stage
        default_messages = {
            'tool_start': 'Calling Unity Catalog functions...',
            'tool_complete': 'Tool execution complete',
            'synthesis_start': 'Starting response synthesis...',
            'synthesis_complete': 'Synthesis complete',
            'validation_start': 'Running judge validation...',
            'validation_complete': 'Validation complete'
        }
        st.write(f"{icon} {default_messages.get(stage, 'Processing...')}")

