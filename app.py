import streamlit as st
import time
import os
from datetime import datetime

# Prevent TensorFlow (DeepFace) from hoarding entire system memory
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
try:
    import tensorflow as tf
    gpus = tf.config.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
except Exception:
    pass

from chat_analyzer import ChatSafetyAnalyzer

# Page configuration
st.set_page_config(page_title="SafeNest Safety Dashboard", page_icon="🛡️", layout="wide")

# Initialize models in session state so they only load once
if "analyzer" not in st.session_state:
    with st.spinner("Initializing AI Models... (This might take a minute)"):
        st.session_state.analyzer = ChatSafetyAnalyzer()

if "logs" not in st.session_state:
    st.session_state.logs = []

# Top Header
st.title("🛡️ SafeNest Real-Time Safety Dashboard")
st.markdown("Live monitoring for **Text, Context, and Visual Threat Detection** using Llama-3, ToxicBERT, and Hugging Face.")

# Layout
col1, col2 = st.columns([1, 1.5])

# --- SIDEBAR: REPORTING CENTER ---
with st.sidebar:
    st.header("📊 Reporting Center")
    st.markdown("Extract safety data for audits and investigations.")
    
    from db_manager import db
    from reporting_utils import generate_csv_report, generate_pdf_report
    
    st.subheader("Current Session")
    if st.session_state.logs:
        # Convert session logs (list of dicts) to list of lists for CSV
        csv_data = []
        for log in st.session_state.logs:
            csv_data.append([log['time'], log['type'], log['input'], ", ".join(log['issues'])])
        
        csv_bytes = generate_csv_report(csv_data, ["Time", "Type", "Input", "Issues"])
        st.download_button(
            label="Download Session CSV",
            data=csv_bytes,
            file_name=f"session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_session_csv"
        )
    else:
        st.caption("No session logs available yet.")

    st.markdown("---")
    st.subheader("Historical Database")
    if st.button("Generate DB Reports"):
        with st.spinner("Fetching data..."):
            db_data = db.get_all_alerts()
            if db_data:
                # 1. CSV
                db_csv = generate_csv_report(db_data, ["Timestamp", "Type", "Trigger", "Confidence", "Reason"])
                st.download_button(
                    label="📥 Download All History (CSV)",
                    data=db_csv,
                    file_name=f"db_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_db_csv"
                )
                
                # 2. PDF
                try:
                    db_pdf = generate_pdf_report(db_data)
                    st.download_button(
                        label="📄 Download All History (PDF)",
                        data=db_pdf,
                        file_name=f"safety_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        key="download_db_pdf"
                    )
                except Exception as e:
                    st.error(f"PDF Generation Error: {e}")
            else:
                st.warning("No alerts found in the database.")

    st.markdown("---")
    st.info("💡 **Tip:** Use the PDF report for formal safety audits.")

# --- COLUMN 1: LIVE SIMULATOR ---
    with col1:
        st.header("📲 Live Chat Stream")
        st.markdown("Simulate a child/volunteer session below.")
        
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("Type a message to simulate:", placeholder="e.g. Call me at 555-123-1234 or keep this a secret.")
            submit_btn = st.form_submit_button("Send to Stream")
            
    # --- LOGIC: Process Input BEFORE UI Rendering to avoid lag in Sidebar ---
    if submit_btn and user_input:
        # Run Analysis
        is_safe, issues = st.session_state.analyzer.analyze_message(user_input)
        
        # Log it
        timestamp = datetime.now().strftime("%H:%M:%S")
        if is_safe:
            st.session_state.logs.insert(0, {
                "time": timestamp,
                "input": user_input,
                "type": "SAFE",
                "issues": ["Message Clean"]
            })
        else:
            st.session_state.logs.insert(0, {
                "time": timestamp,
                "input": user_input,
                "type": "ALERT",
                "issues": issues
            })
        st.rerun() # Refresh to ensure all components see the new log

    with col1:
        # Render simulated chat history visually
        st.subheader("Chat History")
        import re
        def strip_ansi(text):
            return re.sub(r'\x1b\[[0-9;?]*[mK]', '', str(text))

        for log in st.session_state.logs[:5]: # Show last 5 messages in chat
            if log["type"] == "SAFE":
                st.info(f"**user**: {log['input']}")
            else:
                st.error(f"**user**: {log['input']}")
                for issue in log.get("issues", []):
                    st.caption(f"⚠️ {strip_ansi(issue)}")

# --- COLUMN 2: COMMAND CENTER DASHBOARD ---
with col2:
    db_status = db.is_connected()
    status_color = "green" if db_status else "red"
    status_text = "ONLINE" if db_status else "OFFLINE (Live View Only)"
    
    st.header("🚨 Unified Safety Alerts Log")
    st.markdown(f"**Database Status:** :{status_color}[{status_text}]")
    
    # 1. LIVE SESSION ALERTS (High Priority)
    session_alerts = [log for log in st.session_state.logs if log['type'] == "ALERT"]
    if session_alerts:
        st.subheader("🔥 Active Session Alerts")
        for alert in session_alerts:
            with st.expander(f"🔴 LIVE: {alert['type']} at {alert['time']}", expanded=True):
                st.write(f"**Trigger:** `{alert['input']}`")
                st.error(f"**Reason:** {', '.join(alert['issues'])}")
                if alert.get('frame_image'):
                    try:
                        import base64
                        from PIL import Image
                        from io import BytesIO
                        img_bytes = base64.b64decode(alert['frame_image'])
                        img = Image.open(BytesIO(img_bytes))
                        st.image(img, caption="Visual Evidence", use_container_width=True)
                    except: pass

    st.markdown("---")
    st.subheader("📜 Historical Database Records")
    
    # Fetch from POSTGRESQL
    from db_manager import db
    conn = db.get_connection()
    alerts = []
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("SELECT timestamp, alert_type, trigger_text, confidence_score, reason, frame_image FROM safety_alerts ORDER BY timestamp DESC LIMIT 20")
            rows = cur.fetchall()
            for row in rows:
                alerts.append({
                    "time": row[0].strftime("%H:%M:%S"),
                    "type": row[1],
                    "input": row[2],
                    "confidence": float(row[3]),
                    "reason": row[4],
                    "frame_image": row[5] if len(row) > 5 else None
                })
        except Exception as e:
            st.error(f"DB Fetch Error: {e}")
        finally:
            conn.close()

    if len(alerts) == 0:
        st.success("✅ System Database is secure. No active alerts.")
    else:
        st.error(f"⚠️ {len(alerts)} ALERTS DETECTED IN DATABASE")
        
        for alert in alerts:
            with st.expander(f"[{alert['time']}] {alert['type']} ALERT", expanded=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**Triggering Data:** `{alert['input']}`")
                    st.warning(f"**Reason:** {alert['reason']}")
                with c2:
                    st.metric(label="AI Confidence", value=f"{alert['confidence'] * 100:.1f}%")
                if alert.get('frame_image'):
                    try:
                        import base64
                        from PIL import Image
                        from io import BytesIO
                        img_bytes = base64.b64decode(alert['frame_image'])
                        img = Image.open(BytesIO(img_bytes))
                        st.image(img, caption="Alert Trigger Frame", use_container_width=True)
                    except Exception as e:
                        pass

# --- VIDEO SECTION SUMMARY ---
st.markdown("---")

def log_visual_alert(alert_type, trigger, confidence, reason, b64_img=None):
    """Callback to log visual alerts to session state for immediate display."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {
        "time": timestamp,
        "input": trigger,
        "type": "ALERT",
        "issues": [f"{alert_type}: {reason}"],
        "frame_image": b64_img
    })
st.header("📹 Video & Audio Drag-and-Drop Analysis")
st.markdown("Upload a session recording to automatically extract transcription and visual safety metrics directly to the database.")

uploaded_file = st.file_uploader("Upload Session Video (.mp4)", type=["mp4"])

if uploaded_file is not None:
    if st.button("Start AI Video Analysis"):
        with st.spinner("Preparing Video... Please wait, this takes time."):
            with open("temp_uploaded_video.mp4", "wb") as f:
                f.write(uploaded_file.getbuffer())
                
        st.markdown("### 📡 Live Feed Analysis")
        live_col1, live_col2 = st.columns(2)
        with live_col1:
            st.caption("Live Visual Check")
            video_feed = st.empty()
        with live_col2:
            st.caption("Live Audio Transcription (Scrollable)")
            transcript_container = st.container(height=400)
            
        def update_transcript(text, is_safe=True, issues=[]):
            with transcript_container:
                if not is_safe:
                    flags_text = " | ".join(issues)
                    st.error(f"❌ {text}\n\n**↳ FLAGGED:** {flags_text}")
                else:
                    st.info(f"✅ {text}")
            
        def update_frame(rgb_frame):
            video_feed.image(rgb_frame, channels="RGB")

        from video_analyzer import VideoSafetyAnalyzer
        import os
        
        # Start Analyzer, passing the cached Text model AND the visual callback!
        v_analyzer = VideoSafetyAnalyzer(
            text_analyzer=st.session_state.analyzer,
            visual_alert_callback=log_visual_alert
        )
        
        # 1. Audio
        audio_file = v_analyzer.extract_audio("temp_uploaded_video.mp4")
        if audio_file:
            v_analyzer.analyze_audio_segment(audio_file, log_callback=update_transcript)
            try:
                os.remove(audio_file)
            except: pass
            
        # 2. Video
        v_analyzer.analyze_video_frames("temp_uploaded_video.mp4", frame_callback=update_frame)
        
        st.success("✅ Video Analysis Complete! ALERTS have been injected into your Database.")
        time.sleep(1.5)
        st.rerun() # Refresh page to show new database logs
