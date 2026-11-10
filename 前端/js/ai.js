/**
 * AI 问答模块（RAG 检索增强）
 *
 * 前端只负责收集问题与展示结果，检索与生成全在后端完成：
 *   POST /api/ai/ask  →  { code, msg, data: { answer, hits, usage, elapsed, notice } }
 *
 * 两个容易被误解的点，界面上要讲清楚：
 *   1. 勾选「仅检索」时不会调用大模型，零 token 消耗，只是把命中的资料列出来；
 *   2. 模型回答只依据检索到的资料，资料里没有就会拒答——这不是故障，是设计。
 */

const AI_EXAMPLES = {
    empty: '还没有提问。可以直接输入问题，或点上面的示例按钮。',
};

let aiAsking = false;

/** 填充示例问题，不自动发送，留给用户改 */
function fillAIQuestion(text) {
    const box = document.getElementById('aiQuestion');
    if (!box) return;
    box.value = text;
    box.focus();
}

/** 页面加载后查一次模块状态，告知用户当前能否直接对话 */
async function checkAIStatus() {
    const hint = document.getElementById('aiHint');
    if (!hint) return;
    try {
        const res = await apiGet('/ai/status');
        const d = res && res.data;
        if (!d) throw new Error('状态返回为空');
        if (d.model_ready) {
            hint.textContent = `资料库已就绪：${d.doc_count} 个景点，模型 ${d.model}。每次问答约消耗数百 token。`;
            hint.className = 'hint';
        } else {
            hint.textContent = '未配置模型密钥，当前只能使用「仅检索」模式。在 ai_demo/.env 填入 DEEPSEEK_API_KEY 后重启后端即可对话。';
            hint.className = 'hint warn';
        }
    } catch (e) {
        hint.textContent = '无法获取 AI 模块状态，请确认后端服务已启动。';
        hint.className = 'hint warn';
    }
}

/** 主流程：提问 → 渲染答案 → 渲染命中资料 */
async function askAI() {
    if (aiAsking) return;

    const box = document.getElementById('aiQuestion');
    const question = (box.value || '').trim();
    if (!question) {
        box.focus();
        return;
    }

    const btn = document.getElementById('aiAskBtn');
    const resultBox = document.getElementById('aiResult');
    const answerBox = document.getElementById('aiAnswer');
    const noticeBox = document.getElementById('aiNotice');
    const metaBox = document.getElementById('aiMeta');
    const sourceBox = document.getElementById('aiSources');
    const onlyRetrieve = document.getElementById('aiRetrieveOnly').checked;

    aiAsking = true;
    btn.disabled = true;
    btn.textContent = onlyRetrieve ? '检索中...' : '思考中...';
    resultBox.style.display = 'block';
    noticeBox.style.display = 'none';
    metaBox.textContent = '';
    sourceBox.innerHTML = '<p class="hint">检索中...</p>';
    answerBox.className = 'ai-answer pending';
    answerBox.textContent = onlyRetrieve
        ? '正在从资料库检索相关景点...'
        : '正在检索资料并生成回答，通常需要 1~3 秒...';

    try {
        const res = await apiPost('/ai/ask', {
            question: question,
            top_k: 3,
            retrieve_only: onlyRetrieve,
        });

        if (!res || res.code !== 200) {
            throw new Error((res && res.msg) || '接口返回异常');
        }

        renderAIResult(res.data, answerBox, noticeBox, metaBox, sourceBox);
    } catch (e) {
        answerBox.className = 'ai-answer error';
        answerBox.textContent = `请求失败：${e.message}。请确认后端服务已启动（127.0.0.1:8001）。`;
        sourceBox.innerHTML = '';
    } finally {
        aiAsking = false;
        btn.disabled = false;
        btn.textContent = '发送提问';
    }
}

/** 把接口返回的数据渲染到面板上 */
function renderAIResult(data, answerBox, noticeBox, metaBox, sourceBox) {
    const hits = data.hits || [];

    // 答案或检索摘要
    if (data.answer) {
        answerBox.className = 'ai-answer';
        answerBox.innerHTML = formatAnswer(data.answer);
    } else if (hits.length) {
        answerBox.className = 'ai-answer';
        answerBox.textContent = `已检索到 ${hits.length} 条相关资料，见下方列表。`;
    } else {
        answerBox.className = 'ai-answer error';
        answerBox.textContent = '没有检索到相关景点资料。换个说法或直接提景点名会更准。';
    }

    // 降级/说明提示
    if (data.notice) {
        noticeBox.textContent = data.notice;
        noticeBox.style.display = 'block';
    } else {
        noticeBox.style.display = 'none';
    }

    // 元信息：命中数、分段耗时、token
    const el = data.elapsed || {};
    const parts = [`命中 ${hits.length} 条`];
    parts.push(`检索 ${el.retrieve != null ? el.retrieve : '-'} ms`);
    if (el.generate != null) parts.push(`生成 ${Math.round(el.generate)} ms`);
    if (data.usage && data.usage.total_tokens) {
        parts.push(`token ${data.usage.prompt_tokens || 0}+${data.usage.completion_tokens || 0}=${data.usage.total_tokens}`);
    }
    if (data.model) parts.push(data.model);
    metaBox.textContent = parts.join(' · ');

    // 命中资料
    if (!hits.length) {
        sourceBox.innerHTML = '<p class="hint">无命中</p>';
        return;
    }
    sourceBox.innerHTML = hits.map((h, i) => `
        <div class="ai-src">
            <div class="ai-src-head">
                <span class="ai-src-idx">${i + 1}</span>
                <span class="ai-src-name">${escapeHtml(h.name)}</span>
                <span class="ai-src-score">得分 ${h.score}</span>
            </div>
            <div class="ai-src-cat">${escapeHtml(h.category || '')} / ${escapeHtml(h.subcategory || '')}</div>
        </div>
    `).join('');
}

/**
 * 模型会输出 Markdown 粗体（如 **周一闭馆**），直接当纯文本显示会出现一堆星号。
 * 这里只处理粗体这一种最影响观感的标记：先转义防 XSS，再把 **x** 换成 <strong>。
 * 其余 Markdown 语法保持原样，不做完整渲染——够用即可，避免引入第三方库。
 */
function formatAnswer(text) {
    return escapeHtml(text)
        .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
        .replace(/^#{1,6}\s+(.+)$/gm, '<strong>$1</strong>');
}

function escapeHtml(s) {
    return String(s == null ? '' : s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// 回车（Ctrl+Enter 或 Cmd+Enter）直接发送
document.addEventListener('DOMContentLoaded', function () {
    const box = document.getElementById('aiQuestion');
    if (box) {
        box.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                askAI();
            }
        });
    }
    if (typeof switchModule === 'function') {
        checkAIStatus();
    }
});
