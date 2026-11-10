# -*- coding: utf-8 -*-
"""
AI 问答模块（RAG 检索增强）

链路：
    提问 → 从 scenic 表取资料 → 字面检索召回 → 组装约束式 Prompt → 调大模型生成

设计说明：
    - 检索内核放在 services/rag.py，命令行脚本 ai_demo/rag_demo.py 复用同一份实现；
    - 接口层只负责取数据与调度，不掺检索逻辑；
    - 模型调用是阻塞 IO，用 asyncio.to_thread 丢到线程池，不阻塞事件循环；
    - 未配置密钥或模型调用失败时，仍返回检索结果（notice 说明原因），
      保证演示与联调不会因为网络问题白屏。
"""

import asyncio
import logging
import time
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Scenic
from schemas import AIAskRequest, ResponseModel
from services import rag

logger = logging.getLogger("travel_platform.api.ai")
router = APIRouter(prefix="/api/ai", tags=["AI 问答模块"])

# ai_demo/.env 存模型密钥，与代码分离，已在 .gitignore 中排除
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LLM_ENV = PROJECT_ROOT / "ai_demo" / ".env"


@router.post("/ask", summary="RAG 问答")
async def ask(req: AIAskRequest, db: AsyncSession = Depends(get_db)):
    """
    基于景点资料回答问题。

    - **question**：用户问题
    - **top_k**：召回资料条数，默认 3
    - **retrieve_only**：只检索不调用模型，返回资料与 Prompt，零 token 消耗
    """
    t_db = time.perf_counter()
    try:
        rows = (
            await db.execute(
                select(Scenic).where(Scenic.is_deleted == False).order_by(Scenic.id)  # noqa: E712
            )
        ).scalars().all()
    except Exception as e:
        logger.error(f"AI 问答读取景点资料失败：{e}")
        return ResponseModel(code=500, msg=f"读取景点资料失败：{e}").model_dump()

    docs = [rag.to_doc(r) for r in rows]
    t_read = (time.perf_counter() - t_db) * 1000

    cfg = rag.llm_config(LLM_ENV)

    # 检索与模型调用都是阻塞操作，统一放线程池，避免卡住事件循环
    result = await asyncio.to_thread(
        rag.run_rag,
        req.question,
        docs,
        cfg,
        req.top_k,
        req.retrieve_only,
    )

    result["elapsed"]["read_db"] = round(t_read, 2)
    result["doc_count"] = len(docs)
    result["retrieve_only"] = req.retrieve_only
    result["model_ready"] = cfg is not None

    logger.info(
        "AI 问答 | 问题=%s | 命中=%d | 模型=%s | 耗时=%.0fms | token=%s",
        req.question,
        len(result["hits"]),
        result["model"] or "未调用",
        sum(v for k, v in result["elapsed"].items() if isinstance(v, (int, float))),
        result["usage"].get("total_tokens", "-"),
    )

    return ResponseModel(
        data=result,
        msg=result["notice"] or "成功",
    ).model_dump()


@router.get("/status", summary="AI 模块状态")
async def status(db: AsyncSession = Depends(get_db)):
    """查询模型配置与资料库规模，供前端提示「当前是否可直接对话」。"""
    cfg = rag.llm_config(LLM_ENV)
    total = (
        await db.execute(select(Scenic).where(Scenic.is_deleted == False))  # noqa: E712
    ).scalars().all()
    return ResponseModel(
        data={
            "model_ready": cfg is not None,
            "model": cfg["model"] if cfg else None,
            "doc_count": len(total),
        }
    ).model_dump()
