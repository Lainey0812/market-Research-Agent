import httpx
import trafilatura
import pdfplumber
from config import SERPER_API_KEY
import streamlit as st
from typing import Dict, Any
import asyncio


# ---------------------------
# Serper search（异步）
# ---------------------------
async def serper_search(q: str, num: int = 5) -> Dict[str, Any]:
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": q, "num": num}
    async with httpx.AsyncClient(timeout=25) as client:
        resp = await client.post(url, json=payload, headers=headers)
        return resp.json()


# ---------------------------
# 抓取页面全文（同步调用 trafilatura）
# ---------------------------
def fetch_full_content_sync(url: str) -> str:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""
        text = trafilatura.extract(downloaded)
        return text or ""
    except Exception:
        return ""


# 将同步函数包装为异步
async def fetch_full_content(url: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fetch_full_content_sync, url)


# ---------------------------
# PDF 解析（pdfplumber）
# ---------------------------
def extract_texts_from_pdf(file) -> str:
    # file is an UploadedFile from Streamlit
    try:
        text_list = []
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_list.append(page_text)
        return "\n".join(text_list)
    except Exception as e:
        st.error(f"PDF 解析失败：{e}")
        return ""
