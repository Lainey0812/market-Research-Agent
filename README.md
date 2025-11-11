# Market Research Agent

An AI-powered agent that conducts real-time market research by searching news and online sources,
then summarizes results into a structured market report.

## Features
- User inputs a research topic
- Google search integration via Serper API
- Aggregated and structured summarization via GPT-4
- Web interface built with Streamlit

## Demo
🎯 [Try it here](https://market-agent.streamlit.app)


## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## version records
版本一：完成基本工作流程
用户输入主题 --> 意图识别Agent --> 搜索Agent --> 内容整合Agent --> 报告生成Agent