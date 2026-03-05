// ── Digitally Agency — Ticker Module ─────────────────────────────────────────

function loadStocks() {
  // Previously we loaded fake stocks. Now we only build the performance ticker.
  buildPerformanceTicker();
}

function buildPerformanceTicker() {
  const benchmarks = [
    { label: 'AVG_CPC', val: '$1.24', up: true },
    { label: 'META_CPM', val: '$8.72', up: false },
    { label: 'SEO_GROWTH', val: '+14.2%', up: true },
    { label: 'AVG_CTR', val: '2.8%', up: true },
    { label: 'LCP_TARGET', val: '≤1.5s', up: false },
    { label: 'ROAS_Q3', val: '4.8x', up: true },
    { label: 'CPA_AUDIT', val: '-22%', up: true },
    { label: 'ENG_RATE', val: '6.4%', up: true },
  ];

  const bmHtml = benchmarks.map(b =>
    `<span class="ti"><span class="ti-sym">${b.label}</span><span class="${b.up ? 'ti-up' : 'ti-dn'}">${b.up ? '▲' : '▼'} ${b.val}</span></span>`
  ).join('');

  // We use CSS marquee for smooth scrolling, so we duplicate the content to ensure it loops seamlessly without a gap.
  const all = bmHtml + bmHtml;

  const rail = document.getElementById('ticker-rail');
  if (rail) {
    rail.innerHTML = all;
    // The CSS animation '.marquee' will handle the scrolling
    rail.classList.add('marquee-rail');
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
