// ── Digitally Agency — Weather Module ────────────────────────────────────────

const WX_PATHS = {
    sunny: `<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>`,
    cloudy: `<path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>`,
    rainy: `<line x1="16" y1="13" x2="16" y2="21"/><line x1="8" y1="13" x2="8" y2="21"/><line x1="12" y1="15" x2="12" y2="23"/><path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25"/>`,
    stormy: `<path d="M19 16.9A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.7"/><polyline points="13 11 9 17 15 17 11 23"/>`,
    foggy: `<line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="8" x2="21" y2="8"/><line x1="3" y1="16" x2="21" y2="16"/>`,
    snow: `<path d="M20 17.58A5 5 0 0 0 18 8h-1.26A8 8 0 1 0 4 16.25"/><line x1="8" y1="16" x2="8" y2="22"/><line x1="16" y1="16" x2="16" y2="22"/><line x1="12" y1="19" x2="12" y2="25"/>`,
};

const WX_PALETTE = {
    sunny: { hero: 'rgba(245,158,11,.04)', orb: 'rgba(245,158,11,.16)', acc: '#f59e0b' },
    cloudy: { hero: 'rgba(100,116,139,.04)', orb: 'rgba(100,116,139,.11)', acc: '#94a3b8' },
    rainy: { hero: 'rgba(14,165,233,.05)', orb: 'rgba(14,165,233,.17)', acc: '#0ea5e9' },
    stormy: { hero: 'rgba(139,92,246,.05)', orb: 'rgba(139,92,246,.17)', acc: '#a78bfa' },
    foggy: { hero: 'rgba(100,116,139,.04)', orb: 'rgba(100,116,139,.10)', acc: '#94a3b8' },
    snow: { hero: 'rgba(186,230,253,.04)', orb: 'rgba(186,230,253,.13)', acc: '#bae6fd' },
};

const WX_QUIPS = {
    sunny: 'High visibility conditions. Optimal window for scaling top-of-funnel campaigns.',
    cloudy: 'Overcast conditions detected. Search volume and intent often shift during low-light periods.',
    rainy: 'Precipitation active. Screen time and ad engagement typically see a 12-18% lift.',
    stormy: 'Severe weather. High probability of elevated digital consumption and reduced CPA.',
    foggy: 'Low physical visibility. Prime opportunity to dominate search and display share of voice.',
    snow: 'Cold weather parameters met. E-commerce conversion rates trend upward in these conditions.',
};

async function loadWeather(apiBase = '') {
    try {
        // Relying entirely on our backend to detect location via Vercel headers
        const r = await fetch(`${apiBase}/api/weather`);
        const d = await r.json();
        if (d.ok && d.weather) applyWeather(d.weather);
        else throw new Error("Weather API failed");
    } catch (e) {
        console.warn("Weather sync failed:", e);
        applyWeather({ city: 'GLOBAL', temp: '--', condition: 'cloudy', desc: 'Data Syncing', wind: '--' });
    }
}

function applyWeather(wx) {
    const m = WX_PALETTE[wx.condition] || WX_PALETTE.sunny;

    // Hero tint
    const hero = document.getElementById('hero');
    if (hero) hero.style.background = m.hero;

    // Orb color
    const orb = document.getElementById('hero-orb');
    if (orb) orb.style.background = `radial-gradient(circle,${m.orb} 0%,transparent 70%)`;

    // Nav pill
    const pill = document.getElementById('wx-nav');
    if (pill) {
        const navSvg = document.getElementById('wx-nav-svg');
        const navTxt = document.getElementById('wx-nav-txt');
        pill.style.display = 'flex';
        pill.style.background = m.acc + '18';
        pill.style.borderColor = m.acc + '44';
        pill.style.color = m.acc;
        if (navSvg) navSvg.setAttribute('stroke', m.acc);
        if (navTxt) navTxt.textContent = `${wx.city} · ${wx.temp}°C · ${wx.desc || wx.condition}`;
    }

    // Hero strip
    const strip = document.getElementById('wx-strip');
    if (strip) {
        const stripSvg = document.getElementById('wx-strip-svg');
        const city = document.getElementById('wx-city');
        const cond = document.getElementById('wx-cond');
        const quip = document.getElementById('wx-quip');
        const eyebrow = document.getElementById('eyebrow');

        strip.style.display = 'flex';
        if (stripSvg) {
            stripSvg.innerHTML = WX_PATHS[wx.condition] || WX_PATHS.sunny;
            stripSvg.setAttribute('stroke', m.acc);
        }
        if (city) city.textContent = wx.city;
        if (cond) cond.textContent = `· ${wx.temp}°C · ${wx.desc || wx.condition} · ${wx.wind} km/h`;
        if (quip) {
            quip.textContent = WX_QUIPS[wx.condition] || WX_QUIPS.sunny;
            quip.style.borderLeftColor = m.acc + '55';
            quip.style.color = m.acc;
        }

        // Eyebrow
        if (eyebrow) {
            eyebrow.textContent = `// LIVE FROM ${(wx.city || 'YOUR CITY').toUpperCase()} · DIGITAL ECOSYSTEM OPTIMIZED`;
        }
    }
}
