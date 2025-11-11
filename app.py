import streamlit as st
import requests
import json
from openai import OpenAI
from fpdf import FPDF

# ========== 基础配置 ==========
st.set_page_config(page_title="AI 市场调研助理", layout="wide")
st.title("🧠 AI 市场调研助理")
st.markdown("让 AI 帮你快速完成行业趋势、竞争格局、消费者洞察等市场调研任务。")

# ========== 输入区 ==========
api_key = st.text_input("请输入你的 OpenAI API Key：", type="password")
query = st.text_input("请输入调研主题（例如：新能源车市场趋势）")

generate_btn = st.button("🚀 开始生成报告")

# ========== 功能函数 ==========
def search_market_info(query: str):
    """使用 DuckDuckGo 免费接口进行信息检索"""
    st.info("🔍 正在搜索市场数据...")
    try:
        res = requests.get(f"https://ddg-api.herokuapp.com/search?q={query}&max_results=8")
        data = res.json()
        if isinstance(data, list):
            merged_text = "\n\n".join([f"• {r['title']}\n{r['snippet']}" for r in data])
            return merged_text
        return "未找到相关结果。"
    except Exception as e:
        return f"检索出错：{e}"

def save_as_pdf(text, filename="market_report.pdf"):
    """将报告内容导出为 PDF"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)
    pdf.output(filename)
    return filename

# ========== 主流程 ==========
if generate_btn:
    if not api_key or not query:
        st.warning("⚠️ 请输入 API Key 和 调研主题")
        st.stop()

    client = OpenAI(api_key=api_key)

    # Step 1️⃣ 调研方向识别
    with st.spinner("🧠 正在识别调研方向..."):
        intent_prompt = f"""
        你是一位市场研究专家，请分析以下主题并输出JSON格式的调研方向信息：
        {{
          "topic": "主要研究主题",
          "focus": "主要调研方向（如行业趋势、竞争格局、消费者分析等）",
          "keywords": ["关键词1", "关键词2", "关键词3"]
        }}
        用户输入：{query}
        """
        intent_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": intent_prompt}]
        )
        intent_text = intent_resp.choices[0].message.content.strip()
        try:
            intent_json = json.loads(intent_text)
        except:
            intent_json = {"topic": query, "focus": "行业趋势", "keywords": [query]}
        st.subheader("📘 调研方向识别结果")
        st.json(intent_json)

    # Step 2️⃣ 检索市场信息
    with st.spinner("🔎 正在检索市场数据..."):
        merged_info = search_market_info(query)

    # Step 3️⃣ 生成报告
    with st.spinner("🧾 正在生成市场报告..."):
        report_prompt = f"""
        你是一位专业的市场分析顾问，请根据以下资料，为主题“{query}”生成一份结构化市场调研报告，格式如下：
        ---
        ## 行业概述
        ...
        ## 主要趋势
        ...
        ## 竞争格局
        ...
        ## 用户洞察
        ...
        ## 总结与建议
        ...
        ---
        以下是参考资料：
        {merged_info}
        """
        report_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": report_prompt}],
            temperature=0.5
        )
        report_text = report_resp.choices[0].message.content.strip()

        st.success("✅ 报告生成完成")
        st.subheader("📄 市场调研报告")
        st.markdown(report_text)

        # Step 4️⃣ 导出功能
        st.download_button(
            label="💾 下载报告（Markdown）",
            data=report_text,
            file_name="market_report.md",
            mime="text/markdown"
        )

        # 导出 PDF
        pdf_path = save_as_pdf(report_text)
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="📄 下载报告（PDF）",
                data=f,
                file_name="market_report.pdf",
                mime="application/pdf"
            )

