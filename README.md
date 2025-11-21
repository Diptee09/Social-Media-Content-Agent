# Social Media Content Agent (CrewAI + Streamlit)
**प्रोजेक्ट (मराठी मध्ये) — Full example repo**

हा प्रोजेक्ट एक prototype आहे ज्यात:
- CrewAI वापरून multi-agent system (Researcher, Copywriter, HashtagGen, VisualDesigner)
- Streamlit frontend (`streamlit_app.py`) जे user कडून brief घेते आणि crew kickoff करतो
- Agent collaboration visualization app (`streamlit_agent_viz.py`)
- YAML configs, simple `main.py` आणि sample instrumentation (trace write)

## फायलींची रचना
```
social-agent/
├─ src/social_agent/
│  ├─ crew.py
│  ├─ main.py
│  ├─ config/
│  │  ├─ agents.yaml
│  │  ├─ tasks.yaml
├─ streamlit_app.py
├─ streamlit_agent_viz.py
├─ requirements.txt
├─ .env.example
└─ README.md
```

## सुरुवात कशी करावी
1. virtualenv तयार करा आणि activate करा.
2. `pip install -r requirements.txt`
3. `.env` फाईल मध्ये तुमचे API keys (`OPENAI_API_KEY`, इ.) भरून ठेवा.
4. Streamlit ऍप चालवा:
   - `streamlit run streamlit_app.py`
   - किंवा visualization चालवा: `streamlit run streamlit_agent_viz.py`

> लक्षात ठेवा: हा एक उदाहरण प्रोजेक्ट आहे. वास्तविक production वापरासाठी API integration, error handling, आणि सुरक्षा घालावी लागेल.

