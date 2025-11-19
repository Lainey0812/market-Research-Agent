from agents.utils import clean_and_load_json, merge_and_dedupe_texts, llm_client
from agents.searcher import (
    extract_texts_from_pdf,
    serper_search,
    fetch_full_content,
)
from agents.report_maker import (
    generate_market_report_from_corpus,
    propose_followup_questions,
    generate_competitor_matrix,
)
import streamlit as st
import asyncio
from agents.writer import expand_query_with_prompt
from typing import List, Dict, Any
from openai import OpenAI

# ---------------------------
# 页面基础设置
# ---------------------------
st.set_page_config(page_title="Market Intelligence Agent", layout="wide")
st.title("📊 市场分析 Agent")
# ---------------------------
# session state 初始化
# ---------------------------
if "expanded_queries" not in st.session_state:
    st.session_state.expanded_queries = []
if "final_queries" not in st.session_state:
    st.session_state.final_queries = []
if "collected_texts" not in st.session_state:
    st.session_state.collected_texts = ""  # 合并的语料
if "report" not in st.session_state:
    st.session_state.report = ""
if "history" not in st.session_state:
    st.session_state.history = []  # 用于多轮的问答记录


# ---------------------------
# UI：输入 & 扩写 & 编辑
# ---------------------------
st.sidebar.header("1) 输入 & 扩写")
user_query = st.sidebar.text_input(
    "调研主题 / 问题（示例：电动汽车市场趋势）", value=""
)
col1, col2 = st.sidebar.columns([1, 1])
with col1:
    if st.sidebar.button("生成扩写 Query"):
        if not user_query.strip():
            st.sidebar.warning("请输入调研主题")
        else:
            parsed = expand_query_with_prompt(user_query)
            eqs = parsed.get("expanded_queries") or []
            # 保底
            if not eqs:
                eqs = [
                    f"{user_query} 市场规模 2025 中国",
                    f"{user_query} 竞争格局 主要厂商",
                    f"{user_query} 用户画像 需求痛点",
                    f"{user_query} 投融资 政策 机会 风险",
                ]
            st.session_state.expanded_queries = eqs
            st.session_state.final_queries = list(eqs)
            st.sidebar.success("扩写完成，请在下方编辑或确认")

with col2:
    if st.sidebar.button("重新生成（清空已编辑）"):
        st.session_state.expanded_queries = []
        st.session_state.final_queries = []
        st.sidebar.info("已清空，重新输入后再生成")

# 显示并允许用户修改 final queries
st.sidebar.markdown("### 编辑 / 确认搜索 Query（可修改）")
if st.session_state.expanded_queries:
    tmp = []
    for i, q in enumerate(st.session_state.expanded_queries):
        new_q = st.sidebar.text_input(f"Query {i+1}", value=q, key=f"editable_q_{i}")
        tmp.append(new_q)
    # 用户可以确认修改后的 queries
    if st.sidebar.button("确认使用这些 Query 开始搜索"):
        st.session_state.final_queries = tmp
        st.sidebar.success("已确认，准备开始搜集数据")
else:
    st.sidebar.info("先点击 “生成扩写 Query” 以自动生成候选")

# ---------------------------
# UI：PDF 上传 & 粘贴文本（背景资料）
# ---------------------------
st.sidebar.header("2) 背景资料（可选）")
uploaded = st.sidebar.file_uploader(
    "上传行业报告（PDF），可上传多份", type=["pdf"], accept_multiple_files=True
)
pasted_text = st.sidebar.text_area(
    "或粘贴内部资料（如：行业片段/公司资料/数据表）", height=150
)

if uploaded:
    pdf_texts = []
    for f in uploaded:
        pdf_texts.append(extract_texts_from_pdf(f))
    joined_pdf_text = "\n\n".join(pdf_texts)
    if joined_pdf_text.strip():
        # 合并到全局语料
        st.session_state.collected_texts += "\n\n[PDF BACKGROUND]\n" + joined_pdf_text
        st.sidebar.success(f"已解析 {len(uploaded)} 个 PDF，并加入背景语料")

if pasted_text and st.sidebar.button("将粘贴内容加入语料"):
    st.session_state.collected_texts += "\n\n[PASTE BACKGROUND]\n" + pasted_text
    st.sidebar.success("粘贴内容已加入背景语料")

# ---------------------------
# 开始并行搜索并抓取全文（主按钮）
# ---------------------------
st.header("3) 搜索并抓取网页全文")
if st.button("开始搜索并抓取（使用已确认的 Query）"):
    if not st.session_state.final_queries:
        st.warning("请先生成并确认搜索 Query（侧边栏）")
    else:
        queries = st.session_state.final_queries

        async def run_all_search_and_fetch(queries_list):
            per_query_results = {}  # {query: [ {title, link, snippet, content}, ... ]}
            # 并行搜索每个 query 的 SERPER (顺序发起 search 请求，但每个 query 内并行抓取页面)
            for q in queries_list:
                st.write(f"🔍 搜索：{q}")
                search_res = await serper_search(q, num=5)
                organic = search_res.get("organic", []) or []
                tasks = []
                urls = []
                for item in organic:
                    link = item.get("link")
                    if link:
                        urls.append(link)
                        tasks.append(fetch_full_content(link))
                contents = []
                if tasks:
                    # 并行抓取该 query 的所有网页
                    contents = await asyncio.gather(*tasks)
                results_for_q = []
                for item, content in zip(organic, contents):
                    results_for_q.append(
                        {
                            "title": item.get("title"),
                            "link": item.get("link"),
                            "snippet": item.get("snippet"),
                            "content": content or "",
                        }
                    )
                per_query_results[q] = results_for_q
            return per_query_results

        with st.spinner("正在并行检索并抓取网页全文，请稍候..."):
            try:
                per_query_results = asyncio.run(run_all_search_and_fetch(queries))
            except Exception as e:
                st.error(f"检索失败：{e}")
                per_query_results = {}

        # 合并并去重（把每条网页正文加入全局语料）
        all_texts = []
        for q, items in per_query_results.items():
            st.write(f"结果：{q} 共 {len(items)} 条")
            for it in items:
                if it.get("content"):
                    all_texts.append(it["content"])
                else:
                    # fallback 用 snippet
                    snippet = it.get("snippet") or ""
                    if snippet:
                        all_texts.append(snippet)
        merged_text = merge_and_dedupe_texts(all_texts)
        # 将背景资料（PDF/粘贴）也包含进来
        if st.session_state.collected_texts:
            merged_text = st.session_state.collected_texts + "\n\n" + merged_text

        st.session_state.collected_texts = merged_text
        st.success(f"抓取并合并完成，合并后语料长度：{len(merged_text)} 字符")
        # 展示预览
        st.subheader("语料预览（前 3000 字）")
        st.text(merged_text[:3000])

# ---------------------------
# UI：生成报告、显示竞品矩阵、多轮追问
# ---------------------------


st.header("4) 生成报告 & 多轮补充")

colA, colB = st.columns([2, 1])
with colA:
    if st.button("生成初始市场分析报告"):
        if not st.session_state.collected_texts:
            st.warning("请先检索并合并语料（第3步）或上传/粘贴背景资料")
        else:
            with st.spinner("正在生成报告...（可能需要 20-60 秒）"):
                report_text = generate_market_report_from_corpus(
                    user_query, st.session_state.collected_texts
                )
                st.session_state.report = report_text
                st.success("报告已生成")
                st.subheader("📘 报告预览")
                st.markdown(report_text)

with colB:
    if st.button("生成竞品对比矩阵（Markdown）"):
        if not st.session_state.collected_texts:
            st.warning("请先准备语料")
        else:
            with st.spinner("生成竞品矩阵..."):
                matrix_md = generate_competitor_matrix(st.session_state.collected_texts)
                st.session_state.matrix_md = matrix_md
                st.success("竞品矩阵已生成")
                st.markdown(matrix_md)

# 多轮追问：模型建议问题并允许用户回答以更新报告
if st.session_state.report:
    st.subheader("🔄 多轮补充与追问")
    suggested_questions = propose_followup_questions(st.session_state.report)
    if suggested_questions:
        st.info("模型建议补充的问题（可从中选择或自行输入）：")
        for q in suggested_questions:
            st.write(f"- {q}")
    add_q = st.text_input("或者输入你希望补充的问题：", value="")
    user_answer = st.text_area(
        "在下方输入你的补充资料或回答（将用于更新报告）：", height=150
    )
    if st.button("将补充内容合并并更新报告"):
        if not user_answer.strip():
            st.warning("请先输入补充内容或回答")
        else:
            # 将用户补充加入语料
            st.session_state.collected_texts += (
                f"\n\n[USER_SUPPLEMENT]\nQuestion: {add_q}\nAnswer: {user_answer}"
            )
            with st.spinner("正在基于补充内容更新报告..."):
                updated = generate_market_report_from_corpus(
                    user_query, st.session_state.collected_texts
                )
                st.session_state.report = updated
                st.success("报告已更新")
                st.markdown(updated)

# 最后显示历史（简单记录）
st.sidebar.header("操作记录")
st.sidebar.write(f"已生成 report 长度：{len(st.session_state.report)} 字符")
if "matrix_md" in st.session_state:
    st.sidebar.write("已生成竞品矩阵")
