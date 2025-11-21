# main.py
"""
Social Media Content Agent — Streamlit app with optional CrewAI integration.

Instructions:
1. Install required libraries:
   - pip install streamlit
   - pip install crewai langchain-groq   # if you plan to use CrewAI + GROQ

2. Set environment variables (example):
   export GROQ_API_KEY="your_groq_api_key"
   export CREW_API_KEY="your_crew_api_key"   # if crew requires a key

3. Run:
   streamlit run main.py
"""

import os
import json
import streamlit as st
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, available_timezones
import random

# ---------- Optional CrewAI + GROQ (safe import) ----------
# Attempt to import Crew SDK; the exact SDK names may vary by version.
try:
    from crewai import Crew, Agent, Task   # adjust imports to your installed Crew SDK
    from langchain_groq import ChatGroq   # optional: if you use langchain-groq
    CREW_AVAILABLE = True
except Exception:
    CREW_AVAILABLE = False

# ---------- Configuration ----------
# Put actual keys into your environment securely; do NOT hardcode in production.
# Example (uncomment and set if you want to set from code):
# os.environ["GROQ_API_KEY"] = "YOUR_GROQ_API_KEY"
# os.environ["CREW_API_KEY"] = "YOUR_CREW_API_KEY"

# ---------- Helper utilities ----------
def ensure_session_keys():
    if "preview" not in st.session_state:
        st.session_state["preview"] = None

def safe_zoneinfo(tz_name: str):
    try:
        if tz_name in available_timezones():
            return ZoneInfo(tz_name)
    except Exception:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return ZoneInfo("UTC")
    return ZoneInfo("UTC")

def iso_to_readable(iso_ts: str):
    try:
        # Keep timezone info if present
        dt = datetime.fromisoformat(iso_ts)
        return dt.strftime("%Y-%m-%d %I:%M %p")
    except Exception:
        return iso_ts

# ---------- Local agents (unchanged) ----------
def ideator_agent(topic):
    words = [w.capitalize() for w in topic.strip().split() if w]
    base = " ".join(words[:3]) if words else "Topic"
    angles = [
        f"Introduction and benefits of {base}",
        f"Practical tips for using {base}",
        f"A short use-case for {base}"
    ]
    hooks = [
        f"You'll love this about {words[0] if words else 'this topic'}!",
        f"Have you ever tried {words[0] if words else 'this'}?",
        f"Try {words[0] if words else 'this'} today!"
    ]
    hashtags = [f"#{w}" for w in words[:3]]
    return {"angles": angles, "hooks": hooks, "hashtags": hashtags}

def copywriter_agent(ideator_out, topic, platforms):
    hook = ideator_out["hooks"][0]
    hashtags = ideator_out["hashtags"]

    short = f"{hook} {topic} — quick summary. {' '.join(hashtags[:2])}"
    medium = f"{hook} A short note about {topic}. Key reasons and a simple CTA. {' '.join(hashtags)}"
    long_text = f"A detailed take on {topic}: {ideator_out['angles'][0]}. Tips: 1) ... 2) ... 3) ..."

    platform_cta = {}
    if platforms:
        for p in platforms:
            if p.lower() == "instagram":
                platform_cta[p] = f"{medium}\n\n{' '.join(hashtags)}"
            elif p.lower() == "twitter":
                platform_cta[p] = f"{short} {' '.join(hashtags)}"
            elif p.lower() == "linkedin":
                platform_cta[p] = f"{long_text}\nCTA: Share your thoughts in the comments. {' '.join(hashtags)}"
            else:
                platform_cta[p] = short
    return platform_cta

def image_agent(topic):
    topic_short = topic if len(topic) <= 30 else topic[:30] + "..."
    prompt = f"High quality photo of '{topic_short}', bright lighting, social-media friendly"
    return prompt

def scheduler_agent(timezone):
    tz = safe_zoneinfo(timezone)
    now = datetime.now(tz)
    schedule = []
    for i, hour in enumerate([10, 13, 19], start=1):
        dt = (now + timedelta(days=i)).replace(hour=hour, minute=0, second=0, microsecond=0)
        schedule.append(dt.isoformat())
    return schedule

# ---------- CrewAI generation function ----------
def crewai_generate(topic, voice, audience, platforms):
    """
    Generate content using CrewAI.

    Expected Crew output format (JSON string) — required for parsing:
    {
      "publisher_preview": {
        "Instagram": "copy...",
        "Twitter": "copy...",
        "LinkedIn": "copy..."
      },
      "image_prompt": "prompt text",
      "schedule": ["2025-11-22T10:00:00+05:30", "2025-11-23T13:00:00+05:30"]
    }

    Notes:
    - The exact Crew SDK methods vary by release. Adjust the Crew initialization
      and run/call method below according to your installed version.
    - If Crew returns free text, make it return JSON (or adapt parsing here).
    """
    if not CREW_AVAILABLE:
        return None

    try:
        # Create Crew client (adjust per SDK)
        crew_client = Crew(api_key=os.environ.get("CREW_API_KEY")) if "CREW_API_KEY" in os.environ else Crew()

        # Compose a strict instruction for Crew to return JSON. Being explicit reduces parsing errors.
        instruction = {
            "task": "generate_social_media_content",
            "instructions": (
                "Return a JSON object (no extra explanation) with keys: publisher_preview, image_prompt, schedule.\n"
                "publisher_preview should be a mapping of platform names to post copy (Instagram, Twitter, LinkedIn).\n"
                "image_prompt should be a short prompt suitable for image generation.\n"
                "schedule should be an array of 3 ISO8601 datetimes (one per next 3 days) in the same timezone as requested.\n"
            ),
            "inputs": {
                "topic": topic,
                "voice": voice,
                "audience": audience,
                "platforms": platforms
            },
            "format": "json"
        }

        # Create a simple Task/Agent run. Adjust to your SDK's pattern.
        # Many crew SDKs accept a prompt string, but we send JSON text for clarity.
        prompt_text = json.dumps(instruction, ensure_ascii=False)
        # Example Task creation (modify if your SDK uses different class names)
        task = Task(name="generate_social_media", prompt=prompt_text, max_tokens=1200)

        # Create a lightweight Agent; set model name as appropriate in your environment
        agent = Agent(name="content_agent", model="gpt-4o-mini")  # replace with actual model id if needed

        # Run the task — SDK may return a dict, list, or custom object.
        # We use crew_client.run(...) as a generic call — adapt to your SDK.
        raw_result = crew_client.run(agent=agent, task=task, timeout=20)

        # raw_result handling depends on SDK: try to extract text
        text_output = ""
        if isinstance(raw_result, dict):
            # common patterns: 'outputs', 'result', etc.
            if "outputs" in raw_result and isinstance(raw_result["outputs"], list) and raw_result["outputs"]:
                first = raw_result["outputs"][0]
                text_output = first.get("text") or first.get("output") or json.dumps(first)
            else:
                # sometimes the SDK returns "result" or "text"
                text_output = raw_result.get("text") or raw_result.get("result") or json.dumps(raw_result)
        elif isinstance(raw_result, str):
            text_output = raw_result
        else:
            # fallback: try str()
            text_output = str(raw_result)

        # Clean output and attempt parse as JSON
        text_output = text_output.strip()
        # If agent wrapped JSON in markdown or backticks, remove them
        if text_output.startswith("```json"):
            # strip code fence
            parts = text_output.split("```")
            if len(parts) >= 2:
                text_output = parts[1].strip()
        if text_output.startswith("```") and text_output.endswith("```"):
            text_output = text_output.strip("`").strip()

        # Try parsing as JSON
        parsed = None
        try:
            parsed = json.loads(text_output)
        except Exception:
            # If parsing fails, try to find first JSON object in the text
            import re
            match = re.search(r"\{(?:.|\n)*\}", text_output)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except Exception:
                    parsed = None

        if not parsed:
            # Unable to parse Crew output as JSON — return None to allow fallback to local agents.
            return None

        # Ensure keys exist and have reasonable defaults
        publisher_preview = parsed.get("publisher_preview", {})
        image_prompt = parsed.get("image_prompt", image_agent(topic))
        schedule = parsed.get("schedule", scheduler_agent("UTC"))
        # If schedule returned without timezone or fewer than 3 items, fill with local default
        if not isinstance(schedule, list) or len(schedule) < 1:
            schedule = scheduler_agent("UTC")

        result = {
            "publisher_preview": publisher_preview,
            "image_prompt": image_prompt,
            "schedule": schedule
        }
        return result

    except Exception as e:
        # Log error to Streamlit so you can debug easily
        st.error(f"CrewAI generation failed: {e}")
        return None

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Social Media Content Agent", layout="wide")
st.title("Social Media Content Agent — Live Multi-platform Preview (CrewAI Integrated)")

ensure_session_keys()

col1, col2 = st.columns([2, 3])

with col1:
    st.header("Input")
    topic = st.text_input("Topic / Brief")
    voice = st.selectbox("Brand Voice", ["Friendly", "Professional", "Bold", "Playful"])
    audience = st.text_input("Target Audience (optional)")
    timezone = st.selectbox("Timezone", ["Asia/Kolkata", "UTC", "US/Eastern"])
    platforms = st.multiselect("Platforms", ["Instagram", "Twitter", "LinkedIn"])
    use_crew = False
    if CREW_AVAILABLE:
        use_crew = st.checkbox("Use CrewAI (optional)", value=False)
        if use_crew:
            st.markdown("**CrewAI:** Using Crew for generation. Ensure CREW_API_KEY/GROQ_API_KEY env vars are set.")
    else:
        st.info("CrewAI not available (SDK not installed). Install crewai & langchain-groq to enable.")

    generate_btn = st.button("Generate Content")

if generate_btn and topic.strip():
    preview_data = None

    # Try CrewAI if requested
    if use_crew and CREW_AVAILABLE:
        preview_data = crewai_generate(topic, voice, audience, platforms)

    # Fallback to local generation if Crew not used or failed
    if preview_data is None:
        ideator_out = ideator_agent(topic)
        publisher_preview = copywriter_agent(ideator_out, topic, platforms)
        image_prompt = image_agent(topic)
        schedule_list = scheduler_agent(timezone)

        preview_data = {
            "topic": topic,
            "voice": voice,
            "audience": audience,
            "platforms": platforms,
            "publisher_preview": publisher_preview,
            "image_prompt": image_prompt,
            "schedule": schedule_list
        }
    else:
        # Fill commonly-missing fields
        preview_data.setdefault("topic", topic)
        preview_data.setdefault("voice", voice)
        preview_data.setdefault("audience", audience)
        preview_data.setdefault("platforms", platforms)
        preview_data.setdefault("publisher_preview", preview_data.get("publisher_preview", {}))
        preview_data.setdefault("image_prompt", preview_data.get("image_prompt", image_agent(topic)))
        preview_data.setdefault("schedule", preview_data.get("schedule", scheduler_agent(timezone)))

    st.session_state["preview"] = preview_data

with col2:
    st.header("Preview")
    preview = st.session_state.get("preview")
    if preview:
        st.markdown(f"### Topic: {preview.get('topic')}")
        st.markdown(f"**Voice:** {preview.get('voice')} | **Audience:** {preview.get('audience') or '—'}")
        st.markdown("### Image Prompt:")
        st.code(preview.get("image_prompt", ""))

        st.markdown("### Recommended Schedule:")
        schedule_list = preview.get("schedule", [])
        if schedule_list:
            for s in schedule_list:
                st.write(f"- {iso_to_readable(s)}")
        else:
            st.write("- No schedule generated.")

        st.markdown("### Platform-specific Preview:")
        platforms_show = preview.get("platforms", []) or []
        publisher_preview = preview.get("publisher_preview", {}) or {}
        if not platforms_show:
            st.warning("No platforms selected. Choose at least one platform to get platform-specific copy.")
        for p in platforms_show:
            st.markdown(f"**{p} Post:**")
            st.write(publisher_preview.get(p, "(no copy generated for this platform)"))
            st.markdown("---")

        st.download_button(
            label="Download preview as JSON",
            data=json.dumps(preview, indent=2, ensure_ascii=False),
            file_name="social_preview.json",
            mime="application/json",
        )
    else:
        st.info("Enter topic and click 'Generate Content' to see platform-specific preview.")
