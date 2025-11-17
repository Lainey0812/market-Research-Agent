import streamlit as st
import asyncio
import httpx
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


# ======================================
# 工具：解析 JSON
# ======================================
def clean_and_load_json(text):
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        text = text[start:end]
        return json.loads(text)
    except:
        return None


# ======================================
# Step 1：扩写查询
# ======================================
def llm_expand_queries(llm, query):
    prompt = """
        # 角色
        你是一位专业且经验深厚的市场分析专家，凭借扎实的专业知识和丰富的实战经验，为用户深入剖析各类市场问题。
        
        ## 技能
        ### 技能 1: 判断问题类型
        仔细研读用户输入，精确判断问题所属类型，为用户匹配最合适的方向类别，类型涵盖行业趋势、竞品分析、用户画像、投资分析商业模式等各类市场分析相关领域。
        
        ### 2: 数据信息关联
        依据判断出的问题类型，关联与之匹配的各类市场数据信息，为后续分析提供有力支撑。
        
        ### 技能 3: 提取关键词
        从用户输入中精准提炼关键信息，关键词包含但不限于行业、地区、时间、品牌、产品等。若用户未提供时间信息，默认时间为最近一年，即 2025 年；若未提及地区，默认地区为中国。
        
        ### 技能 4: 扩写搜索查询
        围绕提取的关键词，精心扩写出 4 个语义相近但描述更为详尽的搜索查询。这些查询需充分融合用户原始问题以及关键词的相关信息，确保查询更具针对性与全面性。
        
        ## 输出格式
        以 json 格式输出结果，格式如下：
        ```json{
          "intent": "问题类型",  
          "entities": {
            "industry": "行业名称",
            "region": "地区名称",
            "time_range": "时间范围"
          },
          "expanded_queries": [
            "搜索查询 1",
            "搜索查询 2",
            "搜索查询 3",
            "搜索查询 4"
          ]
        }```
        
        ## 限制
        - 仅处理和回答与市场分析紧密相关的用户问题，坚决拒绝回答无关话题。
        - 输出内容必须严格遵循给定的 json 格式进行组织，不得出现任何格式偏差。
        - 请确保输出的格式是json
        """
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"分析主题：{query}"),
    ]
    resp = llm.invoke(messages)
    return clean_and_load_json(resp.content)


# ======================================
# Step 2：并行搜索
# ======================================

SERPER_API_KEY = "9fd7b3cb044ed5a235e8a14a3c72e3e8b7dd2cbc"


async def serper_search(query):
    """Serper Web Search"""
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": 5}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json=payload, headers=headers)
        return r.json()
    print(r.json())


async def serper_news(query):
    """Serper News Search"""
    url = "https://google.serper.dev/news"
    payload = {"q": query, "num": 5}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, json=payload, headers=headers)
        return r.json()


async def run_parallel_search(expanded_queries):
    tasks = []

    for q in expanded_queries:
        tasks.append(serper_search(q))
        tasks.append(serper_news(q))

    raw_results = await asyncio.gather(*tasks)

    # 合并结构化数据 {query: { "web": [...], "news": [...] }}
    merged = {}
    idx = 0

    for q in expanded_queries:
        merged[q] = {"web": raw_results[idx], "news": raw_results[idx + 1]}
        idx += 2

    return merged


# ======================================
# Step 3：市场报告生成
# ======================================
def llm_generate_report(llm, all_data):
    prompt = """
你是一位资深市场研究专家。

输入是多个搜索查询的检索内容，请根据这些数据：

- 汇总行业趋势
- 市场规模变化
- 主要玩家（竞品）
- 用户需求趋势
- 投资方向与商业机会
- 使用可量化的数据
- 输出清晰的行业研究报告结构

请严格输出结构化中文报告。
"""
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(
            content=f"以下是搜索数据：\n{json.dumps(all_data, ensure_ascii=False)}"
        ),
    ]
    return llm.invoke(messages).content


# ======================================
# Streamlit UI
# ======================================

st.title("📊 市场分析 Agent（自动搜索版）")

api_key = st.text_input("OpenAI API Key", type="password")
query = st.text_input("请输入调研主题")
generate_btn = st.button("开始市场分析")

if generate_btn:
    if not api_key or not query:
        st.warning("请输入 API Key 和调研主题")
        st.stop()

    llm = ChatOpenAI(
        api_key=api_key, base_url="https://api.openai.com/v1", model="gpt-4o-mini"
    )

    # =====================
    # Step 1：扩写
    # =====================
    with st.spinner("🧠 正在扩写搜索查询..."):
        intent_json = llm_expand_queries(llm, query)
        print(intent_json)
        st.subheader("📘 扩写结果")
        st.json(intent_json)

    # =====================
    # Step 2：并行搜索
    # =====================
    with st.spinner("🔎 正在并行检索市场信息..."):
        expanded_queries = intent_json["expanded_queries"]
        all_data = asyncio.run(run_parallel_search(expanded_queries))

        st.subheader("📦 原始搜索数据（按 Query 聚合）")
        st.json(all_data)

    # =====================
    # Step 3：生成报告
    # =====================
    with st.spinner("📄 正在生成市场分析报告..."):
        report = llm_generate_report(llm, all_data)

    st.subheader("📊 市场分析报告")
    st.write(report)
