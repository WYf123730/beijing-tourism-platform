# -*- coding: utf-8 -*-
"""
AI 问答模块（RAG）—— 命令行入口

检索内核已上收到 后端/services/rag.py，网页端 /api/ai/ask 与这个脚本共用同一份实现，
这里只负责：读景点表、拼输出、提供命令行参数。

用法：
    python rag_demo.py "故宫有什么值得看的"                  正常问答
    python rag_demo.py "北京有哪些适合孩子的博物馆" --dry      只跑检索，看命中和 Prompt
    python rag_demo.py "..." --topk 3                       指定召回条数
"""

import argparse
import sys
import time
from pathlib import Path

# Windows 控制台默认不是 UTF-8，先改掉，否则中文会报编码错
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
BACKEND_DIR = PROJECT_DIR / "后端"
BACKEND_ENV = BACKEND_DIR / ".env"      # 数据库连接复用项目原有配置
LLM_ENV = BASE_DIR / ".env"             # 大模型 key 单独存放，不进 git

# 复用后端检索内核，避免同一套打分逻辑维护两份
sys.path.insert(0, str(BACKEND_DIR))
from services.rag import (  # noqa: E402
    build_prompt,
    llm_config,
    retrieve,
    run_rag,
    to_doc,
)


def load_env(path: Path) -> dict:
    """极简 .env 解析。"""
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


def db_config() -> dict:
    cfg = load_env(BACKEND_ENV)
    missing = [k for k in ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME") if k not in cfg]
    if missing:
        raise SystemExit(f"数据库配置缺失：{missing}（应位于 {BACKEND_ENV}）")
    return cfg


def fetch_spots() -> list:
    """从 MySQL 读景点，效果等同于「把资料灌进知识库」这一步。"""
    import pymysql

    cfg = db_config()
    conn = pymysql.connect(
        host=cfg["DB_HOST"],
        port=int(cfg["DB_PORT"]),
        user=cfg["DB_USER"],
        password=cfg["DB_PASSWORD"],
        database=cfg["DB_NAME"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, description, address, category, subcategory,
                       open_time, ticket_price, rating
                FROM scenic
                WHERE is_deleted = 0
                ORDER BY id
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="RAG 问答演示")
    parser.add_argument("question", help="要问的问题")
    parser.add_argument("--topk", type=int, default=3, help="召回条数，默认 3")
    parser.add_argument("--dry", action="store_true", help="只跑检索、打印 Prompt，不调用模型")
    args = parser.parse_args()

    t0 = time.perf_counter()
    rows = fetch_spots()
    docs = [to_doc(r) for r in rows]
    print(f"资料库：{len(docs)} 个景点（读取耗时 {(time.perf_counter() - t0) * 1000:.0f} ms）")

    t1 = time.perf_counter()
    hits = retrieve(args.question, docs, args.topk)
    t_ret = (time.perf_counter() - t1) * 1000

    print(f"\n【检索】耗时 {t_ret:.1f} ms，命中 {len(hits)} 条")
    for h in hits:
        print(f"  · {h['name']}（得分 {h['score']}）")

    messages = build_prompt(args.question, hits)

    if args.dry:
        print("\n" + "=" * 60)
        print("【将发送给模型的 Prompt】")
        print("=" * 60)
        print(f"[system]\n{messages[0]['content']}\n")
        print(f"[user]\n{messages[1]['content']}")
        return

    cfg = llm_config(LLM_ENV)
    if not cfg:
        raise SystemExit(
            f"未找到 DEEPSEEK_API_KEY。\n"
            f"请在 {LLM_ENV} 里填一行：DEEPSEEK_API_KEY=sk-xxxx\n"
            f"（只想看检索效果可以加 --dry，不调用模型）"
        )

    t2 = time.perf_counter()
    result = run_rag(args.question, docs, cfg, args.topk)
    t_gen = (time.perf_counter() - t2) * 1000

    if not result["answer"]:
        raise SystemExit(result["notice"] or "模型未返回内容")

    usage = result["usage"]
    print("\n" + "=" * 60)
    print(f"【回答】模型 {cfg['model']}　耗时 {t_gen:.0f} ms")
    print("=" * 60)
    print(result["answer"])
    print("-" * 60)
    print(
        f"token：输入 {usage.get('prompt_tokens', '?')} / "
        f"输出 {usage.get('completion_tokens', '?')} / "
        f"合计 {usage.get('total_tokens', '?')}"
    )


if __name__ == "__main__":
    main()
