"""AI 统一客户端 — 支持 OpenAI/Claude/Gemini/DeepSeek/Local."""
import json
import logging
from typing import Any

log = logging.getLogger(__name__)

SUPPORTED_PROVIDERS = ["openai", "claude", "gemini", "deepseek", "local", "none"]


class AIClient:
    """可插拔 AI 客户端，封装多模型后端的统一调用接口."""

    def __init__(self, provider: str = "none", api_key: str = "", model: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "none":
            return
        # 延迟导入，避免依赖缺失
        try:
            if self.provider == "openai":
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            elif self.provider == "claude":
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            elif self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
            elif self.provider == "deepseek":
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
            elif self.provider == "local":
                self._client = None  # 通过 ollama 等本地服务
        except ImportError as e:
            log.warning(f"AI 提供商 {self.provider} 的 SDK 未安装: {e}")
            self._client = None

    def analyze_news(self, title: str, content: str) -> dict:
        """分析单条新闻的情绪和类别.

        Returns: {"sentiment": "positive/neutral/negative", "score": 0-100,
                   "category": "利好/利空/中性", "summary": str, "key_points": list}
        """
        if self.provider == "none" or self._client is None:
            return _default_news_result(title, content)
        return self._call_llm("news_sentiment", title=title, content=content)

    def identify_catalyst(self, announcement: dict) -> dict:
        """识别公告是否为催化剂.

        Returns: {"is_catalyst": bool, "type": str or None,
                   "confidence": 0-100, "impact_level": "高/中/低",
                   "expiration_days": int, "reasoning": str}
        """
        if self.provider == "none" or self._client is None:
            return _default_catalyst_result(announcement)
        return self._call_llm("catalyst_detection", announcement=announcement)

    def generate_thesis(self, score_card: dict) -> str:
        """生成投资逻辑（150-300 字自然语言）."""
        if self.provider == "none" or self._client is None:
            return _default_thesis(score_card)
        result = self._call_llm("thesis_generation", score_card=score_card)
        return result.get("thesis", "") if isinstance(result, dict) else str(result)

    def assess_risk(self, stock_data: dict) -> list[str]:
        """生成风险提示列表."""
        if self.provider == "none" or self._client is None:
            return _default_risks(stock_data)
        result = self._call_llm("risk_assessment", stock_data=stock_data)
        return result.get("risks", []) if isinstance(result, dict) else []

    def analyze_batch_news(self, news_list: list[dict]) -> list[dict]:
        """批量分析新闻（一次 API 调用处理多条）."""
        results = []
        for news in news_list:
            result = self.analyze_news(news.get("title", ""), news.get("content", ""))
            result["url"] = news.get("url", "")
            results.append(result)
        return results

    def _call_llm(self, task: str, **kwargs) -> dict:
        """统一 LLM 调用入口，各后端适配."""
        try:
            if self.provider in ("openai", "deepseek"):
                return self._call_openai(task, **kwargs)
            elif self.provider == "claude":
                return self._call_claude(task, **kwargs)
        except Exception as e:
            log.error(f"LLM 调用失败: {e}")
        return {}

    def _call_openai(self, task: str, **kwargs) -> dict:
        if self._client is None:
            return {}
        try:
            prompt_text = json.dumps({"task": task, "data": kwargs}, ensure_ascii=False, default=str)
            response = self._client.chat.completions.create(
                model=self.model or "gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是A股投资分析助手，返回结构化JSON。"},
                    {"role": "user", "content": prompt_text},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {}

    def _call_claude(self, task: str, **kwargs) -> dict:
        if self._client is None:
            return {}
        try:
            prompt_text = json.dumps({"task": task, "data": kwargs}, ensure_ascii=False, default=str)
            response = self._client.messages.create(
                model=self.model or "claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt_text + "\n\n请返回JSON格式结果。"}],
            )
            text = response.content[0].text
            # 提取 JSON
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            return {}
        except Exception:
            return {}


def _default_news_result(title: str, content: str) -> dict:
    """无 AI 时的默认新闻分析（基于关键词规则）."""
    positive_words = ["预增", "增长", "突破", "中标", "签约", "回购", "增持", "利好", "分红", "扭亏"]
    negative_words = ["预减", "亏损", "减持", "处罚", "诉讼", "立案", "退市", "减值", "暴雷"]

    text = title + content
    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)

    if pos_count > neg_count:
        sentiment, category, score = "positive", "利好", 65.0
    elif neg_count > pos_count:
        sentiment, category, score = "negative", "利空", 25.0
    else:
        sentiment, category, score = "neutral", "中性", 50.0

    return {
        "sentiment": sentiment,
        "score": score,
        "category": category,
        "summary": title[:80] if title else "(无摘要)",
        "key_points": [],
    }


def _default_catalyst_result(announcement: dict) -> dict:
    title = announcement.get("title", "")
    keywords = {
        "业绩预增": ["预增", "业绩预告", "大幅增长"],
        "回购": ["回购", "股份回购"],
        "增持": ["增持", "员工持股"],
        "并购重组": ["重组", "并购", "收购", "借壳"],
        "重大订单": ["中标", "签约", "合同", "订单"],
        "政策利好": ["政策", "补贴", "扶持"],
    }
    for ctype, kws in keywords.items():
        if any(kw in title for kw in kws):
            return {
                "is_catalyst": True, "type": ctype, "confidence": 60.0,
                "impact_level": "中", "expiration_days": 90, "reasoning": f"标题关键词匹配: {ctype}",
            }
    return {"is_catalyst": False, "type": None, "confidence": 0.0, "impact_level": "无", "expiration_days": 0, "reasoning": ""}


def _default_thesis(score_card: dict) -> str:
    code = score_card.get("code", "未知")
    name = score_card.get("name", "未知")
    final = score_card.get("final_score", 0)
    return f"{name}({code})综合得分{final:.1f}分。具体投资逻辑请接入LLM后生成。"


def _default_risks(stock_data: dict) -> list[str]:
    return ["市场系统性风险", "个股流动性风险", "信息不对称风险"]


_ai_client: AIClient | None = None


def get_ai_client(provider: str = "none", api_key: str = "", model: str = "") -> AIClient:
    global _ai_client
    if _ai_client is None or _ai_client.provider != provider:
        _ai_client = AIClient(provider, api_key, model)
    return _ai_client
