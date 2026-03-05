// ── Digitally Agency — Ticker Module ─────────────────────────────────────────

let _lastStocks = [];

async function loadStocks(apiBase = '') {
  try {
    const r = await fetch(`${apiBase}/api/stocks`);
    const d = await r.json();
    if (d.ok && d.stocks && d.stocks.length) {
      _lastStocks = d.stocks;
      buildTicker(d.stocks);
    }
  } catch (e) {
    console.warn('Stocks fetch failed, using fallback');
    buildTicker(_lastStocks.length ? _lastStocks : [
      {sym:'META',price:611.20,change:1.8,up:true},
      {sym:'GOOGL',price:177.45,change:-0.6,up:false},
      {sym:'MSFT',price:413.90,change:0.5,up:true},
      {sym:'NVDA',price:885.00,change:2.9,up:true},
      {sym:'AMZN',price:194.80,change:0.3,up:true},
      {sym:'AAPL',price:228.10,change:-0.4,up:false},
    ]);
  }
}

function buildTicker(stocks) {
  const benchmarks = [
    {label:'AVG_CPC',   val:'$2.41',  up:true},
    {label:'META_CPM',  val:'$8.72',  up:false},
    {label:'SEO_GROWTH',val:'+14.2%', up:true},
    {label:'AVG_CTR',   val:'2.1%',   up:true},
    {label:'LCP_TARGET',val:'≤2.5s',  up:false},
  ];
  const stockHtml = stocks.map(s => {
    const up = s.up !== undefined ? s.up : s.change >= 0;
    const sign = up ? '+' : '';
    return `<span class="ti">
      <span class="ti-sym">${s.sym}</span>
      <span class="ti-price">$${(+s.price).toFixed(2)}</span>
      <span class="${up ? 'ti-up' : 'ti-dn'}">${up ? '▲' : '▼'} ${sign}${(+s.change).toFixed(2)}%</span>
    </span>`;
  }).join('');
  
  const bmHtml = benchmarks.map(b =>
    `<span class="ti"><span class="ti-sym">${b.label}</span><span class="${b.up ? 'ti-up' : 'ti-dn'}">${b.val}</span></span>`
  ).join('');
  
  const now = new Date().toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit', timeZone:'Asia/Kolkata'});
  const tsHtml = `<span class="ti"><span style="color:var(--border2);font-size:10px;letter-spacing:1px">IST ${now}</span></span>`;

  const all = stockHtml + bmHtml + tsHtml;
  const rail = document.getElementById('ticker-rail');
  if (rail) {
    rail.innerHTML = all + all;   // doubled for seamless loop
    rail.style.animation = 'none';
    rail.offsetHeight;
    rail.style.animation = '';
  }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const tickerOuter = document.getElementById('ticker-outer');
    const tickerRail = document.getElementById('ticker-rail');
    if (tickerOuter && tickerRail) {
        tickerOuter.addEventListener('mouseenter', () => tickerRail.classList.add('paused'));
        tickerOuter.addEventListener('mouseleave', () => tickerRail.classList.remove('paused'));
    }
});
