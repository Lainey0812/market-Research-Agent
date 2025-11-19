from agents.utils import clean_and_load_json, llm_client

from typing import Dict, Any


def expand_query_with_prompt(user_input: str) -> Dict[str, Any]:
    """
    使用更严格的 system prompt 扩写并输出 JSON 格式。
    返回 dict with keys: intent, entities, expanded_queries
    """
    client = llm_client()
    system_prompt = """
# 角色
你是一位专业且经验深厚的市场分析专家，凭借扎实的专业知识和丰富的实战经验，为用户深入剖析各类市场问题。

## 技能
- 判断问题类型（行业趋势/竞品分析/用户画像/投资分析等）
- 提取关键词（行业、细分、地区、时间范围、品牌）
- 如果未提供时间，默认 2025；若未提供地区，默认 中国
- 扩写 4 条用于搜索引擎的查询（覆盖：市场规模/趋势、竞争格局、用户需求或技术、投融资/政策）

**严格输出 JSON，不要任何多余文本**。格式：
{
  "intent": "行业趋势",
  "entities": {
    "industry": "xxx",
    "region": "中国",
    "time_range": "2025"
  },
  "expanded_queries": [
    "query1",
    "query2",
    "query3",
    "query4"
  ]
}
"""
    # 调用 chat completions
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    text = resp.choices[0].message.content
    parsed = clean_and_load_json(text)
    return parsed
