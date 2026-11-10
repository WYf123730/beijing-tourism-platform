# -*- coding: utf-8 -*-
"""
检索效果评估（不调用大模型，零成本，秒级跑完）

为什么要单独做这个：RAG 出问题时，八成不是模型不会答，而是第一步就没捞到对的资料。
所以要先能量化「检索召回」这一环，再谈 Prompt 好不好、模型行不行。

指标（recall@k）：对每个问题，标准答案里的景点是否出现在召回的 k 条结果中。
    问题偏事实型（问门票、问时间）——检索对了，模型照着抄就行
    问题偏语义型（问场景、问氛围）——字面匹配会漏，这是换向量的依据

用法：
    python eval_retrieval.py
    python eval_retrieval.py --topk 5
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag_demo import fetch_spots, retrieve, to_doc  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# (问题, 该命中的景点名, 类型)
CASES = [
    # 事实型：问题里有明确的景点名，字面检索应当稳
    ("故宫门票多少钱，几点开门", "故宫博物院", "事实型"),
    ("恭王府以前是谁的府邸", "恭王府", "事实型"),
    ("颐和园开放到几点", "颐和园", "事实型"),
    ("天安门广场在哪", "天安门广场", "事实型"),
    ("八达岭长城评分多少", "八达岭长城", "事实型"),
    ("798 艺术区有什么", "798艺术区", "事实型"),
    # 类别型：没有景点名，靠分类词表把口语映射到子类
    ("北京有哪些博物馆推荐", "国家博物馆", "类别型"),
    ("想爬山看自然风景", "香山公园", "类别型"),
    ("带孩子去哪个公园合适", "北京动物园", "类别型"),
    ("想逛胡同吃小吃", "南锣鼓巷", "类别型"),
    ("想去看长城", "八达岭长城", "类别型"),
    # 语义型：没有关键词，只有意图——字面检索的短板就在这里
    ("周末想找个能放松一下的地方", "古北水镇", "语义型"),
    ("想感受一下皇家气派", "故宫博物院", "语义型"),
    ("想找个地方安静看一下午书", "国家图书馆", "语义型"),
]


def main():
    parser = argparse.ArgumentParser(description="检索召回率评估")
    parser.add_argument("--topk", type=int, default=3)
    args = parser.parse_args()

    docs = [to_doc(r) for r in fetch_spots()]
    print(f"资料库 {len(docs)} 条，top_k = {args.topk}\n")

    stat = {}
    wrong = []
    for question, expect, kind in CASES:
        hits = retrieve(question, docs, args.topk)
        names = [h["name"] for h in hits]
        ok = expect in names
        stat.setdefault(kind, [0, 0])
        stat[kind][1] += 1
        if ok:
            stat[kind][0] += 1
        else:
            wrong.append((kind, question, expect, names))
        print(f"{'✓' if ok else '✗'} [{kind}] {question}")
        print(f"    期望：{expect}　实际：{names if names else '（无命中）'}")

    print("\n" + "=" * 56)
    total_ok = total = 0
    for kind in ("事实型", "类别型", "语义型"):
        if kind in stat:
            ok, n = stat[kind]
            total_ok += ok
            total += n
            print(f"{kind}　{ok}/{n}　{ok / n * 100:.0f}%")
    print(f"合计　　{total_ok}/{total}　{total_ok / total * 100:.0f}%")
    print("=" * 56)

    if wrong:
        print("\n未命中明细（这些就是下一步要改的地方）：")
        for kind, q, expect, names in wrong:
            print(f"  · [{kind}] {q}")
            print(f"    期望 {expect}，实际 {names if names else '无命中'}")


if __name__ == "__main__":
    main()
