# streamlit_agent_viz.py
# Visualization app for multi-agent collaboration (PyVis + Streamlit)
import streamlit as st
from pyvis.network import Network
import pandas as pd
from datetime import datetime
from dateutil import parser
import uuid
import json
import tempfile
import os
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="Agents Collaboration Viz", layout="wide")
st.title("Multiple Agents Collaboration Visualisation (Prototype)")

def now_iso():
    return datetime.now().astimezone().isoformat()

def make_event(frm, to, task, content, metadata=None):
    return {
        "id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "from": frm,
        "to": to,
        "task": task,
        "content": content,
        "metadata": metadata or {}
    }

def sample_trace():
    t = []
    t.append(make_event("User", "Researcher", "brief", "Topic: Solar Backpack launch", {}))
    time.sleep(0.02)
    t.append(make_event("Researcher", "Copywriter", "research", "3 hooks: portability, eco, charging", {"source":"web"}))
    time.sleep(0.02)
    t.append(make_event("Copywriter", "HashtagGen", "ideation", "Short caption draft A", {}))
    time.sleep(0.02)
    t.append(make_event("HashtagGen", "Copywriter", "hashtags", "#solar #backpack #ecotravel", {}))
    time.sleep(0.02)
    t.append(make_event("Copywriter", "VisualDesigner", "visuals", "Image prompt: person hiking with solar backpack", {}))
    time.sleep(0.02)
    t.append(make_event("VisualDesigner", "Copywriter", "visuals_done", "Image url /local/path/image1.png", {}))
    return t

def build_network(trace):
    net = Network(height="600px", width="100%", directed=True)
    net.barnes_hut()
    agents = set()
    for e in trace:
        agents.add(e["from"])
        agents.add(e["to"])
    for a in agents:
        net.add_node(a, label=a, title=a, shape='dot', size=20)
    edge_map = {}
    for e in trace:
        key = (e["from"], e["to"])
        if key not in edge_map:
            edge_map[key] = {"count": 0, "last": None, "tasks": []}
        edge_map[key]["count"] += 1
        edge_map[key]["last"] = e
        edge_map[key]["tasks"].append(e["task"])
    for (frm, to), info in edge_map.items():
        label = f"{info['count']} msgs\n{','.join(info['tasks'][-2:])}"
        title = ""
        last = info["last"]
        if last:
            ts = last["timestamp"]
            snippet = (last["content"][:140] + "...") if len(last["content"])>140 else last["content"]
            title = f"Last @ {ts}\n{snippet}"
        net.add_edge(frm, to, value=info["count"], title=title, label=label)
    net.set_options("""
    var options = {
      "nodes": {
        "font": {"size": 14}
      },
      "edges": {
        "arrows": {"to": {"enabled": true}},
        "smooth": {"enabled": true}
      },
      "physics": {
        "hierarchicalRepulsion": {"nodeDistance": 120}
      }
    }
    """)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    path = tmp.name
    net.show(path)
    return path

col1, col2 = st.columns([1,1])
with col1:
    use_sample = st.checkbox("Use simulated sample trace", value=True)
    uploaded = st.file_uploader("Upload trace JSON (optional)", type=["json"])
    refresh = st.button("Render visualization")

with col2:
    if use_sample and not uploaded:
        trace = sample_trace()
    else:
        if uploaded:
            raw = uploaded.read()
            try:
                trace = json.loads(raw)
            except Exception:
                st.error("Invalid JSON uploaded.")
                trace = []
        else:
            trace = []
    if trace:
        df = pd.DataFrame(trace)
        try:
            df["ts_parsed"] = df["timestamp"].apply(lambda x: parser.isoparse(x))
            df = df.sort_values("ts_parsed")
        except Exception:
            pass
        st.dataframe(df[["timestamp","from","to","task","content"]].rename(columns={
            "from":"From","to":"To","task":"Task","content":"Content","timestamp":"Timestamp"
        }))

if refresh:
    if not trace:
        st.warning("No trace to render.")
    else:
        with st.spinner("Building interactive network..."):
            html_path = build_network(trace)
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            components.html(html, height=650, scrolling=True)
            try:
                os.remove(html_path)
            except:
                pass
