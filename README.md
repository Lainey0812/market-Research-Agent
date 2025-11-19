# AI市场调研助理Market Research Agent
一个基于 Streamlit + 大模型（如 Gemini / OpenAI 等） 实现的轻量级市场分析助手
通过「自动扩写 → 搜索 → 生成报告」的链式推理方式，实现全流程市场洞察生成。

## 🚀 项目简介
本项目旨在帮助产品经理、市场分析师快速获取市场信息。通过对用户输入的调研主题进行理解、搜索、整理与报告生成，实现「从提问到市场报告」的全流程自动化。

## 功能特性
1. 🧠 自动扩写意图：将你的简短调研需求扩写为更结构化的问题描述
2. 🔍 实时网络搜索：自动调用搜索接口抓取外部信息
3. 📄 生成结构化分析报告：包含 SWOT、竞争格局、潜在机会等
4. 💻 Streamlit UI：可直接部署到任何 Streamlit 环境或 cloud 平台


## 动态演示GIF
![Demo GIF](./assets/市场分析agent.gif)



## 如何本地运行

```
https://github.com/Lainey0812/market-Research-Agent
cd market-Research-Agent
pip install -r requirements.txt
streamlit run app.py
```
环境变量


产品理解力（项目背景、用户痛点）

技术架构理解（数据流、模型调用逻辑）

落地能力（Demo、截图、部署链接）

## 产品背景
### 需求来源
在产品调研或市场研究场景中，手动搜索与整理资料的成本高、效率低。希望通过AI自动完成以下工作：
1. 识别用户想调研的主题（如“新能源汽车行业”）
2，收集相关新闻、市场动态、竞争信息等
3. 整理成标准化调研报告


## 🧩 系统架构

![architecture](./assets/architecture.png)

主要流程：
1. 用户输入调研主题（如“新能源汽车趋势”）
2. 意图识别Agent判断分析方向（产业、竞品、消费者）
3. 调用搜索Agent从Google/新闻获取数据
4. 聚合内容并交由大模型生成标准报告

## 产品流程图 （后续修改）
                ┌──────────────────────────┐
                │        用户输入（主题）     │
                └────────────┬─────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   意图识别模块（LLM）   │
                    │ - 识别调研方向          │
                    │ - 输出结构化参数(JSON)   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   信息检索模块         │
                    │ - 调用Serper/News API │
                    │ - 聚合多渠道数据       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   内容整合模块         │
                    │ - 去重与关键信息提取   │
                    │ - 格式化成摘要块       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   报告生成模块（LLM）  │
                    │ - 生成结构化报告        │
                    │ - 输出Markdown/PDF      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   前端展示层（Streamlit） │
                    │ - 用户输入框 / 报告展示   │
                    │ - 下载按钮 / 加载状态     │
                    └────────────────────────────┘


## 技术架构
- 前端：Streamlit（用户交互界面）
- 后端：Langchain + OpenAI API
- 检索：DuckDuckGo / NewsAPI /Serper API
- 报告生成：LLM结构化Prompt输出
- 输出格式：Markdown + PDF导出

## 产品功能


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


## 结果展示
主题：新能源车市场趋势

行业概述：全球新能源汽车市场持续增长，中国市场占比超过60%...

主要趋势：随着智能驾驶技术发展，新能源车企向高端化转型...

竞争格局：特斯拉、比亚迪、小鹏占据主导地位...

market-research-agent/
│
├── app.py # Streamlit主程序
├── requirements.txt
├── README.md # 项目说明（作品集展示重点）
├── assets/
│ ├── architecture.png # 架构流程图（你刚生成的）
│ └── ui-demo.png # 界面截图
└── docs/
└── product_doc.pdf # 产品文档 or 调研报告样例