import streamlit as st
from openai import OpenAI
import requests
import json
import re
from duckduckgo_search import DDGS

# from fpdf import FPDF
from langchain_openai import ChatOpenAI
import os

# 导入 LangChain 消息对象
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.utilities import GoogleSerperAPIWrapper

os.environ["SERPER_API_KEY"] = "9fd7b3cb044ed5a235e8a14a3c72e3e8b7dd2cbc"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
# ========== 基础配置 ==========
st.set_page_config(page_title="AI 市场调研助理", layout="wide")
st.title("🧠 AI 市场调研助理 ")
st.markdown("让 AI 帮你快速完成行业趋势、竞争格局、消费者洞察等市场调研任务。")
base_url = "https://yinli.one/v1"
# api_key = ("sk-LigUlIOoxblNRsIW83Ivom303rVkgteWazFVDe4JldylDkPU",)
# ========== 输入区 ==========
# 【重要修改 2：提示用户输入 API Key】
api_key = st.text_input("请输入你的 API Key：", type="password")
query = st.text_input("请输入调研主题（例如：新能源车市场趋势）")
generate_btn = st.button("🚀 开始生成报告")


# ========== 功能函数 (保持不变) ==========
def search_market_info(query: str):
    """使用 DuckDuckGo 免费接口进行信息检索"""
    st.info("🔍 正在搜索市场数据...")
    try:
        # 注意：ddg-api.herokuapp.com 接口可能不稳定，但此处沿用原代码
        res = requests.get(
            f"https://ddg-api.herokuapp.com/search?q={query}&max_results=8"
        )
        data = res.json()
        if isinstance(data, list):
            merged_text = "\n\n".join([f"• {r['title']}\n{r['snippet']}" for r in data])
            return merged_text
        return "未找到相关结果。"
    except Exception as e:
        st.error(f"检索出错：{e}")
        return "检索出错，无法获取外部数据。"


def save_as_pdf(text, filename="market_report.pdf"):
    """将报告内容导出为 PDF"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)
    pdf.output(filename)
    return filename


def clean_and_load_json(text_output: str):
    """尝试从 LLM 的输出中提取并加载 JSON"""
    text_output = re.sub(r"[\u200b-\u200f\uFEFF\xa0]", "", text_output)
    # Step 1: 尝试匹配```json ... ```代码块中的内容
    match = re.search(
        r"```(?:json)?\s*(\{[\s\S]*?\})\s*```",
        text_output,
        re.DOTALL | re.IGNORECASE,  # DOTALL 让 . 匹配换行符
    )

    if not match:
        match = re.search(r"(\{[\s\S]*?\})", text_output.strip())
        if not match:
            raise ValueError("未能找到有效的 JSON 代码块或裸 JSON 结构。")

    # 提取代码块中的纯 JSON 字符串
    json_string = match.group(1).strip()

    # 步骤 2: 进行 JSON 解析
    # 注意：我们假设提取出的 json_string 是干净的
    return json.loads(json_string)


def search_ddg(query, max_results=5):
    try:
        results = DDGS().text(query, max_results=max_results)
        texts = [r["body"] for r in results]
        return "\n".join(texts)
    except Exception as e:
        return f"DDG 搜索失败：{e}"


# ========== 主流程 ==========
if generate_btn:
    if not api_key or not query:
        st.warning("⚠️ 请输入 API Key 和 调研主题")
        st.stop()

        # 创建 LangChain Chat 模型实例（基线温度为 0，可在生成报告时调整）
    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        temperature=0.2,  # 随机性：0（确定性）~1（创造性）
        model="gpt-4o-mini",
    )

    # Step 1️⃣ 调研方向识别
    with st.spinner("🧠 正在识别调研方向..."):
        # 完整的 System Prompt
        system_prompt_content = """
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

        # 定义 LangChain 消息列表
        intent_messages = [
            SystemMessage(content=system_prompt_content),
            HumanMessage(content=f"请分析这个主题：{query}"),
        ]

        # 使用 LangChain 的 .invoke() 方法进行调用
        intent_resp = llm.invoke(intent_messages)
        intent_text = intent_resp.content.strip()

        try:
            intent_json = clean_and_load_json(intent_text)
            if len(intent_json.get("expanded_queries", [])) < 2:
                raise ValueError("expanded_queries 数量不足")
            # 从 expanded_queries 中获取第一个查询用于 Step 2 的搜索
            # search_query_for_ddg = intent_json["expanded_queries"][0]
        except Exception as e:
            st.error(f"⚠️ JSON解析失败，模型未返回正确的结构化数据。错误：{e}")
            # 失败时使用默认值
            intent_json = {
                "intent": "行业趋势",
                "entities": {"industry": query, "region": "中国", "time_range": "2025"},
                "expanded_queries": [f"{query}市场规模分析", f"{query}最新发展情况"],
            }

            st.session_state.intent_json = intent_json
            st.session_state.confirmed = False  # 初始化确认状态
        if "final_queries" not in st.session_state:
            st.session_state.final_queries = intent_json["expanded_queries"]
            st.divider()

            # Step 2️⃣ 用户确认/修改搜索关键词
            st.subheader("🔍 搜索关键词确认与修改")
            st.markdown(
                "模型已为您生成以下搜索关键词。您可以直接**确认**进行搜索，或在文本框中**修改**后点击**重新生成**。"
            )
            # 1. 展示和编辑区域
            # 将列表转换成带编号的字符串，方便用户编辑
            queries_text = "\n".join(st.session_state.final_queries)
            # 使用 text_area 允许用户编辑，并存储在 session state 的临时变量中
            edited_queries_text = st.text_area(
                "📝 请确认或修改关键词",
                value=queries_text,
                height=200,
                key="edited_queries_text",  # 确保 Streamlit 能够跟踪状态
            )

            # 用户确认按钮
            col1, col2 = st.columns(2)
            with col1:
                confirm_btn = st.button(
                    "🚀 确认无误，开始搜索", use_container_width=True
                )
                if confirm_btn:
                    st.session_state.confirmed = True

            with col2:
                if st.button("✏️ 修改调研方向"):
                    del st.session_state.intent_json
                    st.session_state.confirmed = False

            search_query_for_ddg = query

        st.subheader("📘 调研方向识别结果")
        st.json(intent_json)

    # # Step 2️⃣ 检索市场信息
    with st.spinner("🔎 正在检索市场数据..."):
        search_wrapper = GoogleSerperAPIWrapper()
        # 调用 results() 方法获取原始结构化数据
        raw_data = search_wrapper.results(query, num=5)  # 明确指定 num=5
        # 提取前 N 条结果（例如前 3 条）
        num_results_needed = 3
        if "organic" in raw_data:
            # Serper 的主要搜索结果在 'organic' 键中
            top_results = raw_data["organic"][:num_results_needed]

            print(f"✅ 成功获取 {len(top_results)} 条结构化搜索结果：{top_results}")
    for i, result in enumerate(top_results):
        print(f"--- 结果 {i+1} ---")
        print(f"标题: {result.get('title')}")
        print(f"摘要: {result.get('snippet')[:100]}...")  # 打印摘要前100字符
        print(f"链接: {result.get('link')}")
    else:
        print("❌ 搜索失败或结果为空。")
#     st.success("数据检索完成。")

# Step 3️⃣ 生成报告
# with st.spinner("🧾 正在生成市场报告..."):

#     report_prompt = f"""
#     你是一位专业的市场分析顾问，请根据以下资料，为主题“{query}”生成一份结构化市场调研报告，格式如下：
#     ---
#     ## 行业概述
#     ...
#     ## 主要趋势
#     ...
#     ## 竞争格局
#     ...
#     ## 用户洞察
#     ...
#     ## 总结与建议
#     ...
#     ---
#     以下是参考资料：
#     {merged_info}
#     """

#     # 定义生成报告的消息列表
#     report_messages = [
#         SystemMessage(
#             content="你是一位专业的市场分析顾问，专注于生成结构严谨、内容深入的市场调研报告。"
#         ),
#         HumanMessage(content=report_prompt),
#     ]

#     # 调整温度以获得更具创造性的报告
#     llm.temperature = 0.5
#     report_resp = llm.invoke(report_messages)
#     report_text = report_resp.content.strip()

#     st.success("✅ 报告生成完成")
#     st.subheader("📄 市场调研报告")
#     st.markdown(report_text)

#     # Step 4️⃣ 导出功能
#     st.download_button(
#         label="💾 下载报告（Markdown）",
#         data=report_text,
#         file_name="market_report.md",
#         mime="text/markdown",
#     )

#     # 导出 PDF
#     pdf_path = save_as_pdf(report_text)
#     with open(pdf_path, "rb") as f:
#         st.download_button(
#             label="📄 下载报告（PDF）",
#             data=f,
#             file_name="market_report.pdf",
#             mime="application/pdf",
#         )
