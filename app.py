import streamlit as st
from openai import OpenAI
import requests
import json

# from fpdf import FPDF
from langchain_openai import ChatOpenAI

# 导入 LangChain 消息对象
from langchain_core.messages import SystemMessage, HumanMessage


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
        {
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
        }
        
        ## 限制
        - 仅处理和回答与市场分析紧密相关的用户问题，坚决拒绝回答无关话题。
        - 输出内容必须严格遵循给定的 json 格式进行组织，不得出现任何格式偏差。
        - 所提供的信息和分析必须基于客观事实，切实保证内容准确、合理、可靠。 
        
        ## 信息来源
        - 所依据的数据和信息来自权威的市场研究报告、行业资讯平台等可靠渠道。请在回答中明确标注引用来源。
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
            intent_json = json.loads(intent_text)
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

            # 展示扩展结果并等待用户确认
            if "intent_json" in st.session_state and not st.session_state.confirmed:
                st.subheader("📘 调研方向识别结果（请确认或修改）")
                edited_intent_json = st.json(st.session_state.intent_json)
                for i, q in enumerate(
                    st.session_state.intent_json["expanded_queries"], 1
                ):
                    st.write(f"{i}. {q}")

                # 用户确认按钮
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 确认调研方向,并开始搜索"):
                        st.session_state.confirmed = True
                        st.success("已确认，即将开始检索")
                with col2:
                    if st.button("✏️ 修改调研方向"):
                        del st.session_state.intent_json
                        st.session_state.confirmed = False

            search_query_for_ddg = query

        st.subheader("📘 调研方向识别结果")
        st.json(intent_json)

    # Step 2️⃣ 检索市场信息
    with st.spinner("🔎 正在检索市场数据..."):
        merged_info = search_market_info(search_query_for_ddg)
        if "检索出错" in merged_info:
            st.warning(merged_info)
            st.stop()
        st.success("数据检索完成。")

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
