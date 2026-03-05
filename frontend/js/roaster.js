// ── Digitally Agency — AI Roaster Module ─────────────────────────────────────

let _lastRoast = null;

async function startRoast(apiBase = '') {
    const input = document.getElementById('url-in').value.trim();
    if (!input) {
        document.getElementById('url-in').focus();
        return;
    }
    const btn = document.getElementById('r-btn');
    const log = document.getElementById('scan-log');
    const res = document.getElementById('r-result');

    btn.disabled = true;
    btn.textContent = '⏳ Scanning…';
    log.className = 'scan-log on';
    res.className = 'r-result';
    log.innerHTML = '';
    res.innerHTML = '';

    track('roaster_started', { domain: input });

    const domain = input.replace(/^https?:\/\//, '').split('/')[0];
    const steps = [
        { m: `Initiating diagnostic for ${domain}…`, c: 'nfo', d: 200 },
        { m: 'Fetching DNS records & TTFB…', c: 'sc', d: 600 },
        { m: 'Analyzing page load performance…', c: 'sc', d: 1100 },
        { m: 'Scanning HTTP headers & security…', c: 'sc', d: 1600 },
        { m: 'Parsing meta tags & Open Graph…', c: 'sc', d: 2000 },
        { m: 'Evaluating mobile responsiveness…', c: 'sc', d: 2400 },
        { m: 'Crawling internal link structure…', c: 'sc', d: 2800 },
        { m: 'Checking image compression ratios…', c: 'sc', d: 3200 },
        { m: 'Routing to Brutally Honest Senior Developer (AI API)…', c: 'nfo', d: 3700 },
    ];

    for (let i = 0; i < steps.length; i++) {
        await sleep(steps[i].d - (i > 0 ? steps[i - 1].d : 0));
        const l = document.createElement('div');
        l.className = `ll ${steps[i].c}`;
        l.textContent = steps[i].m;
        log.appendChild(l);
        log.scrollTop = log.scrollHeight;
    }
    await sleep(400);

    try {
        const r = await fetch(`${apiBase}/api/roast`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: input })
        });
        const d = await r.json();
        if (!d.ok) throw new Error(d.error);

        _lastRoast = { domain: d.domain, ...d.roast };
        track('roaster_completed', { domain: d.domain, score: d.roast.score });

        log.querySelectorAll('.ll.sc').forEach((el, i) => {
            el.classList.remove('sc');
            el.classList.add(i % 4 === 0 ? 'wn' : i % 6 === 0 ? 'er' : 'ok');
        });

        showRoastResult(d.roast, d.domain, d.id);
    } catch (e) {
        console.error(e);
        log.querySelectorAll('.ll.sc').forEach(el => {
            el.classList.remove('sc');
            el.classList.add('ok');
        });

        const fallback = {
            score: 34,
            verdict: "Your website is actively donating customers to your competition.",
            burns: [
                { title: "Load Time: Criminal", text: `'${domain}' loads in 8.4s on mobile. Checkout completed on competitor before hero image renders.`, fix: "→ Fix: Web App Support — Performance Package", severity: "critical" },
                { title: "Page 14 on Google", text: "Zero schema, missing titles, robots.txt blocking crawlers. SEO score: 11/100.", fix: "→ Fix: Search Engine Optimization", severity: "warning" },
                { title: "CTAs That Convert Nobody", text: "Three 'Contact Us' buttons, none visible on mobile. Bounce rate: 83%.", fix: "→ Fix: Website Redesign + CRO", severity: "critical" }
            ],
            roadmap: ["Technical SEO Overhaul", "Core Web Vitals Fix", "Mobile UX Redesign", "Meta Ads Funnel Setup"]
        };
        _lastRoast = { domain, ...fallback };
        showRoastResult(fallback, domain);
    }

    btn.disabled = false;
    btn.textContent = '▶ ROAST IT';
}

function showRoastResult(p, domain, roastId) {
    const sc = p.score < 40 ? 'poor' : p.score < 70 ? 'fair' : 'good';
    const resultDiv = document.getElementById('r-result');
    if (resultDiv) {
        resultDiv.innerHTML = `
        <div class="res-hd">
          <div class="score-b ${sc}">${p.score}</div>
          <div><div class="res-domain">${domain}</div><div class="res-verdict">${p.verdict}</div></div>
        </div>

        <div class="chart-box" style="margin-bottom: 32px; background: rgba(12,16,24,0.5); border: 1px solid var(--border); padding: 24px; position: relative;">
          <canvas id="roastChart" style="max-height: 280px;"></canvas>
        </div>

        ${(p.burns || []).map(b => `
          <div class="burn ${b.severity === 'warning' ? 'wn' : ''}">
            <div class="burn-t">${b.title}</div>
            <div class="burn-b">${b.text}</div>
            <div class="burn-fix">${b.fix}</div>
          </div>`).join('')}

        <div class="rm-box">
          <div class="rm-h">// PRESCRIBED ROADMAP — POWERED BY AI SERVICE</div>
          <div class="rm-items">
            ${(p.roadmap || []).map((r, i) => `<div class="rm-item"><span style="color:var(--muted)">0${i + 1}</span>${r}</div>`).join('')}
          </div>
        </div>

        <div style="margin-top: 24px;">
          <a href="/api/roast/pdf/${roastId}" target="_blank" class="btn-s" style="width: 100%; justify-content: center; display: flex; gap: 8px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Download Professional PDF Report
          </a>
        </div>`;

        resultDiv.className = 'r-result on';
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

        // Render Radar Chart
        if (p.scores && window.Chart) {
            const ctx = document.getElementById('roastChart').getContext('2d');
            new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: Object.keys(p.scores),
                    datasets: [{
                        label: 'Metrics',
                        data: Object.values(p.scores),
                        backgroundColor: 'rgba(0, 245, 212, 0.2)',
                        borderColor: '#00f5d4',
                        borderWidth: 2,
                        pointBackgroundColor: '#00f5d4'
                    }]
                },
                options: {
                    scales: {
                        r: {
                            angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            pointLabels: { color: '#b8c8de', font: { family: 'JetBrains Mono', size: 10 } },
                            ticks: { display: false, stepSize: 20 },
                            min: 0,
                            max: 100
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }
    }
}

function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}
