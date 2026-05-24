const btn      = document.getElementById('analyze-btn');
const spinner  = document.getElementById('spinner');
const results  = document.getElementById('results');

btn.addEventListener('click', async () => {
    const symbol = document.getElementById('symbol-input').value.trim().toUpperCase();
    if (!symbol) return;

    // show spinner, hide old results
    spinner.classList.remove('hidden');
    results.classList.add('hidden');
    btn.disabled = true;

    try {
        const res  = await fetch(`/agent/analyze?symbol=${symbol}`);
        const data = await res.json();

        renderStrategy(data.strategy   || {});
        renderTechnical(data.technical_analysis || {});
        renderSentiment(data.news_sentiment     || {});
        renderCorrelation(data.correlation      || {});

        results.classList.remove('hidden');
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        spinner.classList.add('hidden');
        btn.disabled = false;
    }
});

/* ── STRATEGY ─────────────────────────────── */
function renderStrategy(s) {
    const action    = s.action     || 'WAIT';
    const conf      = s.confidence ? (s.confidence * 100).toFixed(0) + '%' : '—';
    const entry     = s.entry_zone || '—';
    const thesis    = s.thesis     || '—';
    const risks     = s.risks      || '—';
    const cls       = { BUY: 'action-buy', WAIT: 'action-wait', AVOID: 'action-avoid' }[action] || 'action-wait';

    document.getElementById('strategy-card').innerHTML = `
        <h2>Strategy</h2>
        <div class="action-badge ${cls}">${action}</div>
        <div class="metrics">
            <div class="metric"><span class="label">Confidence</span><span class="value">${conf}</span></div>
            <div class="metric"><span class="label">Entry Zone</span><span class="value">${entry}</span></div>
        </div>
        <p style="margin-top:16px; color:#ccc; line-height:1.6">${thesis}</p>
        <p style="margin-top:8px; color:#888; font-size:0.85rem">⚠️ ${risks}</p>
    `;
}

/* ── TECHNICAL ────────────────────────────── */
function renderTechnical(t) {
    const l = t.latest  || {};
    const s = t.signals || {};

    const pill = (val) => {
        const map = { bullish: 'bullish', bearish: 'bearish', uptrend: 'bullish', downtrend: 'bearish', overbought: 'bearish', oversold: 'bullish' };
        const cls = map[val] || 'neutral';
        return `<span class="pill pill-${cls}">${val || '—'}</span>`;
    };

    document.getElementById('technical-card').innerHTML = `
        <h2>Technical Analysis</h2>
        <div class="metrics">
            <div class="metric"><span class="label">Price</span><span class="value">$${Number(l.close).toLocaleString()}</span></div>
            <div class="metric"><span class="label">RSI(14)</span><span class="value">${Number(l.rsi_14).toFixed(1)} ${pill(s.rsi_zone)}</span></div>
            <div class="metric"><span class="label">MACD</span><span class="value">${pill(s.macd_cross)}</span></div>
            <div class="metric"><span class="label">Trend</span><span class="value">${pill(s.trend)}</span></div>
            <div class="metric"><span class="label">Bollinger</span><span class="value">${pill(s.bb_position)}</span></div>
        </div>
    `;
}

/* ── SENTIMENT ────────────────────────────── */
function renderSentiment(n) {
    const signal = n.signal || 'neutral';
    const score  = n.combined_score !== undefined ? n.combined_score.toFixed(3) : '—';
    const crypto = (n.crypto_headlines || []).slice(0, 3);
    const macro  = (n.macro_headlines  || []).slice(0, 3);

    const headlineHtml = (list) => list.map(h => `
        <li>
            <span>${h.headline}</span>
            <span class="pill pill-${h.score > 0.05 ? 'bullish' : h.score < -0.05 ? 'bearish' : 'neutral'}">${h.score > 0 ? '+' : ''}${h.score}</span>
        </li>
    `).join('');

    document.getElementById('sentiment-card').innerHTML = `
        <h2>News & Sentiment</h2>
        <div class="metrics" style="margin-bottom:16px">
            <div class="metric"><span class="label">Signal</span><span class="value"><span class="pill pill-${signal}">${signal}</span></span></div>
            <div class="metric"><span class="label">Score</span><span class="value">${score}</span></div>
            <div class="metric"><span class="label">Crypto</span><span class="value">${n.crypto_score ?? '—'}</span></div>
            <div class="metric"><span class="label">Macro</span><span class="value">${n.macro_score ?? '—'}</span></div>
        </div>
        <ul class="headline-list">${headlineHtml(crypto)}${headlineHtml(macro)}</ul>
    `;
}

/* ── CORRELATION ──────────────────────────── */
function renderCorrelation(c) {
    const bar = (val) => {
        const pct = Math.abs(val * 100).toFixed(0);
        const col = Math.abs(val) > 0.8 ? '#ef4444' : Math.abs(val) > 0.5 ? '#f59e0b' : '#22c55e';
        return `<div style="background:#2a2a3a;border-radius:4px;height:8px;width:100%;margin-top:4px">
                    <div style="width:${pct}%;background:${col};height:8px;border-radius:4px"></div>
                </div>`;
    }
}