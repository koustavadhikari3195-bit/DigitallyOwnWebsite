// ── Digitally Agency — Main Module ──────────────────────────────────────────

const API = ''; // empty = same origin (Flask serves both)

// ── ANALYTICS ───────────────────────────────────────────────────────────────
function track(event, data = {}) {
    console.log(`[Analytics] Event: ${event}`, data);
    // If Umami or Plausible script is loaded, call their tracking function
    if (window.umami && typeof window.umami.track === 'function') {
        window.umami.track(event, data);
    } else if (window.plausible && typeof window.plausible === 'function') {
        window.plausible(event, { props: data });
    }
}

// ── CURSOR ───────────────────────────────────────────────────────────────────
function initCursor() {
    const cur = document.getElementById('cur');
    const curR = document.getElementById('cur-r');
    if (!cur || !curR) return;

    let mx = 0, my = 0, rx = 0, ry = 0;

    document.addEventListener('mousemove', e => {
        mx = e.clientX;
        my = e.clientY;
        cur.style.left = mx + 'px';
        cur.style.top = my + 'px';
    });

    (function loop() {
        rx += (mx - rx) * 0.12;
        ry += (my - ry) * 0.12;
        curR.style.left = rx + 'px';
        curR.style.top = ry + 'px';
        requestAnimationFrame(loop);
    })();

    document.querySelectorAll('a, button, input, select, textarea').forEach(el => {
        el.addEventListener('mouseenter', () => {
            curR.style.width = '48px';
            curR.style.height = '48px';
            curR.style.opacity = '0.8';
        });
        el.addEventListener('mouseleave', () => {
            curR.style.width = '32px';
            curR.style.height = '32px';
            curR.style.opacity = '0.5';
        });
    });
}

// ── REVEAL ───────────────────────────────────────────────────────────────────
function initReveals() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((e, i) => {
            if (e.isIntersecting) {
                setTimeout(() => e.target.classList.add('vis'), i * 60);
            }
        });
    }, { threshold: 0.08 });

    document.querySelectorAll('.rv').forEach(r => observer.observe(r));
}

// ── STACK ────────────────────────────────────────────────────────────────────
function initStack() {
    const tools = ['Python', 'n8n Automation', 'Meta Business Suite', 'Google Analytics 4', 'React.js', 'WordPress', 'Shopify', 'Ahrefs', 'Semrush', 'Figma', 'Vercel', 'Cloudflare', 'Zapier', 'HubSpot', 'TypeScript', 'Next.js', 'MongoDB', 'Grok AI'];
    const dot = `<svg width="5" height="5" viewBox="0 0 5 5"><circle cx="2.5" cy="2.5" r="2" fill="var(--border2)"/></svg>`;
    const rail = document.getElementById('stack-rail');
    if (rail) {
        rail.innerHTML = [...tools, ...tools].map(n => `<span class="stack-item">${dot}${n}</span>`).join('');
    }
}

// ── LEAD FORM ────────────────────────────────────────────────────────────────
async function submitLead() {
    const btn = document.getElementById('submit-btn');
    const payload = {
        name: document.getElementById('f-name').value.trim(),
        email: document.getElementById('f-email').value.trim(),
        service: document.getElementById('f-service').value,
        budget: document.getElementById('f-budget').value,
        website: document.getElementById('f-url').value.trim(),
        message: document.getElementById('f-msg').value.trim(),
    };
    if (!payload.name || !payload.email) {
        alert('Name and email are required.');
        return;
    }
    btn.textContent = 'Sending…';
    btn.disabled = true;
    try {
        await fetch(`${API}/api/lead`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        track('lead_submitted', { service: payload.service });
        document.getElementById('form-msg').style.display = 'block';
        btn.style.display = 'none';
    } catch (e) {
        btn.textContent = '→ Send Strategy Request';
        btn.disabled = false;
    }
}

// ── LOCAL CLOCK ──────────────────────────────────────────────────────────────
function updateLocalClock() {
    const clockTxt = document.getElementById('clock-txt');
    if (!clockTxt) return;

    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });

    clockTxt.textContent = timeString;
}

// ── BOOT ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initCursor();
    initReveals();
    initStack();
    updateLocalClock();

    // Run immediately if present
    if (typeof loadStocks === 'function' && document.getElementById('ticker-rail')) loadStocks(API);
    if (typeof loadWeather === 'function' && document.getElementById('wx-strip')) loadWeather(API);

    // Run when HTMX dynamically injects them
    document.body.addEventListener('htmx:afterSettle', (e) => {
        if (typeof loadStocks === 'function' && document.getElementById('ticker-rail') && !window._stocksLoaded) {
            loadStocks(API);
            window._stocksLoaded = true;
        }
        if (typeof loadWeather === 'function' && document.getElementById('wx-strip') && !window._weatherLoaded) {
            loadWeather(API);
            window._weatherLoaded = true;
        }
    });

    setInterval(() => {
        if (typeof loadStocks === 'function') loadStocks(API);
    }, 3 * 60 * 1000);

    setInterval(() => {
        if (typeof loadWeather === 'function') loadWeather(API);
    }, 10 * 60 * 1000);

    setInterval(updateLocalClock, 1000); // Tick every second
});

