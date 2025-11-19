from agents.utils import safe_truncate, llm_client
from typing import List


# 生成报告（主函数）
# ---------------------------
def generate_market_report_from_corpus(
    query: str, corpus: str, word_limit: int = 1500
) -> str:
    client = llm_client()
    # 为控制 token，截取合适长度
    corpus_short = safe_truncate(corpus, 25000)  # 依据模型限制调节
    system_prompt = """
你是拥有 10 年以上经验的资深市场分析专家（Senior Market Analyst）。
请基于给定的语料与用户主题撰写一份专业市场调研报告，要求：
- 结构清晰（行业概览 / 市场规模与增长 / 主要参与者 / 用户需求 / 机会与风险 / 结论与建议）
- 有因果分析，不只是罗列事实
- 输出 Markdown 格式，总字数控制在 1200-1500 字
"""
    user_message = (
        f"主题：{query}\n\n参考资料（语料已合并）：\n{corpus_short}\n\n请输出报告。"
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.25,
    )
    return resp.choices[0].message.content


# ---------------------------
# 竞品对比矩阵生成
# ---------------------------
def generate_competitor_matrix(corpus: str) -> str:
    client = llm_client()
    prompt = f"""
基于以下语料，请提取出主要竞争对手（公司名），并为每家生成一行对比信息，列为：
企业 | 产品策略 | 核心卖点 | 商业模式 | 优势 | 劣势

语料：
{safe_truncate(corpus, 8000)}

请以 Markdown 表格形式返回（包含表头）。
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是市场分析师，擅长竞品分析"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    return resp.choices[0].message.content


# ---------------------------
# 多轮追问（模型建议 & 用户补充）
# ---------------------------
def propose_followup_questions(report_text: str) -> List[str]:
    client = llm_client()
    prompt = f"""
你是市场分析师。阅读下面报告，并提出 1-3 个最关键的后续澄清或补充问题（只输出问题本身）。
报告：
{safe_truncate(report_text, 6000)}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "你是市场分析师"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=200,
    )
    text = resp.choices[0].message.content.strip()
    # 简单分行拆成列表
    qs = [line.strip("- ").strip() for line in text.splitlines() if line.strip()]
    return qs
