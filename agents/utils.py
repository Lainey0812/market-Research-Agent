import json
from typing import List, Dict, Any
from config import OPENAI_API_KEY, OPENAI_BASE_URL
from openai import OpenAI


# ---------------------------
# LLM 扩写函数（使用 OpenAI 客户端）
# ---------------------------
def llm_client():
    return OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


# ---------------------------
# 公共工具函数
# ---------------------------
def clean_and_load_json(text: str) -> Dict[str, Any]:
    """
    从模型输出中抽取首个 JSON 对象并解析。容错处理。
    """
    if not text:
        return {}
    try:
        # 尝试直接解析
        return json.loads(text)
    except Exception:
        # 取第一个 { ... } 段
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
    return {}


def safe_truncate(s: str, limit: int = 4000) -> str:
    return s if len(s) <= limit else s[:limit]


# 简单文本合并去重
def merge_and_dedupe_texts(items: List[str]) -> str:
    seen = set()
    out_lines = []
    for t in items:
        for line in t.splitlines():
            l = line.strip()
            if not l:
                continue
            if l in seen:
                continue
            seen.add(l)
            out_lines.append(l)
    return "\n".join(out_lines)
