# streamlit_app.py
import streamlit as st
import json
import subprocess
from pathlib import Path

st.set_page_config(page_title="Social Media Content Agent", layout="wide")
st.title("Social Media Content Agent — CrewAI + Streamlit (Prototype)")

with st.form("brief_form"):
    topic = st.text_input("Topic / Brief", "Solar Backpack Launch")
    platforms = st.multiselect("Platforms", ["instagram", "x/twitter", "facebook", "linkedin"], default=["instagram"])
    tone = st.selectbox("Tone", ["friendly", "professional", "playful", "informative"])
    submitted = st.form_submit_button("Generate Content")

if submitted:
    st.info("Kicking off crew (local prototype).")
    # This runs the sample main which attempts to kickoff the crew.
    proc = subprocess.Popen(["python", "src/social_agent/main.py"])
    st.write("Crew started (PID: {})".format(proc.pid))

    out_file = Path("output/social_package.json")
    import time
    timeout = 30
    start = time.time()
    placeholder = st.empty()
    while time.time() - start < timeout:
        if out_file.exists():
            with open(out_file, encoding='utf-8') as f:
                data = json.load(f)
            placeholder.success("Content package ready!")
            st.json(data)
            st.download_button("Download package (JSON)", json.dumps(data, ensure_ascii=False, indent=2), file_name="social_package.json")
            break
        else:
            placeholder.info("Waiting for crew to finish...")
            time.sleep(1)
    else:
        st.error("Timed out waiting for the crew. Check logs.")
