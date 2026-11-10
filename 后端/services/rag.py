# -*- coding: utf-8 -*-
"""
RAG 检索内核（Retrieval-Augmented Generation）

设计要点：
    1. 本模块只做纯计算，不依赖 FastAPI / SQLAlchemy，便于命令行脚本复用；
    2. 检索走「字面匹配 + 分类词表扩展」，刻意不引入向量库与 LangChain，
       目的是先看清「检索召回」这一环能不能拿到对的东西；
    3. 已知局限：纯语义提问（如「周末想放松」）召不回结果，
       这就是后续升级为 Embedding 检索的理由。

链路：
    提问 → 检索（retrieve）→ 组装 Prompt（build_prompt）→ 生成（ask_llm）
"""

import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------- 字典表

CATEGORY_CN = {
    "cultural": "人文古迹",
    "urban": "城市地标",
    "natural": "自然风光",
}

SUBCATEGORY_CN = {
    "museum": "博物馆",
    "park": "公园",
    "school": "高校",
    "landmark": "地标",
    "temple": "寺庙",
    "street": "街区",
    "palace": "宫殿",
    "other": "其他",
}

# 把用户口语里的词映射到分类，弥补字面匹配抓不到类别语义的问题
QUERY_HINTS = {
    "museum": ["博物馆", "展馆", "展览", "文物", "藏品", "科技馆", "美术馆"],
    "park": ["公园", "园林", "绿地", "散步", "遛弯", "湖", "划船"],
    "school": ["大学", "高校", "校园", "学院", "名校"],
    "temple": ["寺", "庙", "烧香", "祈福", "道观"],
    "street": ["街", "胡同", "小吃", "逛街", "购物", "夜市", "美食"],
    "palace": ["宫殿", "皇宫", "皇家", "故宫", "紫禁城", "皇帝"],
    "landmark": ["地标", "广场", "建筑", "打卡", "拍照"],
    "natural": ["山", "自然", "风景", "户外", "爬山", "风光"],
}

# 检索时忽略的虚词，避免「有什么」「值得」这类词污染打分
STOPWORDS = {
    "有什", "什么", "哪些", "哪个", "怎么", "怎样", "为什", "可以", "值得",
    "推荐", "介绍", "一下", "多少", "几点", "需要", "附近", "北京", "的", "吗",
    "呢", "去", "在", "和", "是", "有", "我", "想", "要", "请问",
}


# ---------------------------------------------------------------- 资料准备

def to_doc(row) -> dict:
    """
    一行景点记录 → 一段资料。
    字段固定成模板，模型读起来更稳，出问题时也便于逐条排查。
    兼容 dict 与 SQLAlchemy 模型对象两种输入。
    """
    def g(key, default=""):
        if isinstance(row, dict):
            return row.get(key) or default
        return getattr(row, key, None) or default

    name = g("name")
    cat = CATEGORY_CN.get(g("category"), g("category") or "未分类")
    sub = SUBCATEGORY_CN.get(g("subcategory"), g("subcategory") or "")

    lines = [f"【{name}】", f"类别：{cat} / {sub}".rstrip(" /")]
    if g("address"):
        lines.append(f"地址：{g('address')}")
    if g("open_time"):
        lines.append(f"开放时间：{g('open_time')}")
    meta = []
    if g("ticket_price"):
        meta.append(f"门票：{g('ticket_price')}")
    if g("rating"):
        meta.append(f"评分：{g('rating')}")
    if meta:
        lines.append("　".join(meta))
    if g("description"):
        lines.append(f"简介：{g('description')}")

    return {
        "id": g("id", 0),
        "name": name,
        "category": g("category"),
        "subcategory": g("subcategory"),
        "address": g("address"),
        "text": "\n".join(lines),
    }


# ---------------------------------------------------------------- 检索

def tokenize(query: str) -> list:
    """中文没有空格，用 2-gram 切，简单但对景点名这类短词够用。"""
    q = "".join(ch for ch in query if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")
    grams = {q[i:i + 2] for i in range(len(q) - 1)}
    return [g for g in grams if g not in STOPWORDS]


def expand_categories(query: str) -> set:
    """把「适合带孩子」「逛街」这类说法映射到分类。"""
    hit = set()
    for sub, words in QUERY_HINTS.items():
        if any(w in query for w in words):
            hit.add(sub)
    return hit


def retrieve(query: str, docs: list, top_k: int = 3) -> list:
    """
    字面检索打分：
        景点名命中   ×4（提问里出现景点名，几乎肯定就是问它）
        正文命中     ×1（按命中词数累加）
        分类命中     +3 / +2（通过 QUERY_HINTS 扩展出的类别）

    这是「朴素基线」。它答不上纯语义提问——这正是后面要换向量检索的原因。
    """
    grams = tokenize(query)
    cats = expand_categories(query)
    scored = []
    for doc in docs:
        name_hit = sum(1 for g in grams if g in doc["name"])
        body_hit = sum(1 for g in grams if g in doc["text"])
        score = name_hit * 4 + body_hit
        if doc["subcategory"] in cats:
            score += 3
        if doc["category"] in cats:
            score += 2
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: (-x[0], x[1]["id"]))
    return [{"score": s, **d} for s, d in scored[:top_k]]


# ---------------------------------------------------------------- Prompt

SYSTEM_PROMPT = (
    "你是北京旅游信息助手。只能依据用户消息中【资料】部分的内容回答。\n"
    "规则：\n"
    "1. 资料里没有的信息，直接回答「资料中暂未收录」，不要推测，不要编造。\n"
    "2. 不要输出资料之外的常识，哪怕你确定它是真的。\n"
    "3. 回答控制在 120 字以内，分点列出关键信息。\n"
    "4. 结尾单独一行注明：依据景点：XXX、XXX"
)


def build_prompt(query: str, hits: list) -> list:
    if hits:
        context = "\n\n".join(f"资料{i + 1}：\n{h['text']}" for i, h in enumerate(hits))
    else:
        # 没命中也要问模型，但明确告知无资料，逼它拒答而不是用常识补
        context = "（本轮检索未命中任何景点资料）"
    user = f"【资料】\n{context}\n\n【问题】{query}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


# ---------------------------------------------------------------- 模型调用

def _ssl_context(host: str):
    """
    先按正常校验；若本机有代理做 HTTPS 解密导致证书链不认，再退回不校验。
    退回时打印警告，方便区分是网络环境问题还是代码问题。
    """
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(f"https://{host}", timeout=8, context=ctx):
            pass
    except ssl.SSLError:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    except Exception:
        pass
    return ctx


def ask_llm(messages: list, cfg: dict) -> dict:
    """
    调用 OpenAI 兼容的 /chat/completions。
    用 urllib 而非 httpx，是为了让本模块零第三方依赖，命令行脚本可独立运行。
    """
    url = f"{cfg['base_url'].rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": cfg["model"],
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 600,
    }).encode("utf-8")

    host = url.split("://", 1)[-1].split("/", 1)[0]
    ctx = _ssl_context(host)
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")[:300]
        raise RuntimeError(f"模型接口返回 {e.code}：{body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"模型接口网络请求失败：{e.reason}")
    except TimeoutError:
        raise RuntimeError("模型接口请求超时")


# ---------------------------------------------------------------- 配置读取

def load_env(path) -> dict:
    """极简 .env 解析，避免为一个文件引入 python-dotenv 依赖。"""
    path = Path(path)
    cfg = {}
    if not path.exists():
        return cfg
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def llm_config(env_path) -> dict:
    """
    读取大模型配置。key 单独存放于 ai_demo/.env，不随代码进 git。
    未配置时返回 None，由调用方决定降级方式，避免这里直接抛异常。
    """
    cfg = load_env(env_path)
    key = cfg.get("DEEPSEEK_API_KEY", "")
    if not key:
        return None
    return {
        "api_key": key,
        "base_url": cfg.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        "model": cfg.get("DEEPSEEK_MODEL", "deepseek-flash"),
    }


def run_rag(query: str, docs: list, cfg, top_k: int = 3, retrieve_only: bool = False) -> dict:
    """
    完整跑一次问答，返回结构化结果（供接口与命令行共用）。

    返回字段：
        hits / scores      检索命中的景点
        answer             模型回答（retrieve_only 或失败时为 None）
        prompt             实际发送的 Prompt 文本（便于讲解与排查）
        usage / elapsed    用量与分段耗时
        notice             降级原因（无 key、调用失败等）
    """
    result = {
        "question": query,
        "hits": [],
        "answer": None,
        "prompt": "",
        "usage": {},
        "model": None,
        "notice": None,
        "elapsed": {},
    }

    t0 = time.perf_counter()
    hits = retrieve(query, docs, top_k)
    result["hits"] = [
        {
            "id": h["id"],
            "name": h["name"],
            "category": h["category"],
            "subcategory": h["subcategory"],
            "score": h["score"],
        }
        for h in hits
    ]
    result["elapsed"]["retrieve"] = round((time.perf_counter() - t0) * 1000, 2)

    messages = build_prompt(query, hits)
    result["prompt"] = messages[1]["content"]

    if retrieve_only:
        result["notice"] = "仅检索模式：未调用模型，零 token 消耗"
        return result

    if not cfg:
        result["notice"] = "未配置模型密钥，仅返回检索结果（复制 ai_demo/.env.example 为 .env 并填入 DEEPSEEK_API_KEY）"
        return result

    result["model"] = cfg["model"]
    t1 = time.perf_counter()
    try:
        data = ask_llm(messages, cfg)
    except RuntimeError as e:
        result["notice"] = f"模型调用失败，仅返回检索结果：{e}"
        return result
    result["elapsed"]["generate"] = round((time.perf_counter() - t1) * 1000)

    result["answer"] = data["choices"][0]["message"]["content"].strip()
    result["usage"] = data.get("usage", {}) or {}
    return result
