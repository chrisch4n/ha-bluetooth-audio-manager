// Radiostream Preset Memory – Custom Card für Home Assistant
// Typ: custom:radiostream-preset-card
// 19.11.2026 (Claude, auf Wunsch des Nutzers): Presets und Senderwahl der drei Boxen im Stil des
// RS-970-Receivers (custom:radiostream-receiver-card). Nutzt die Template-Selects
// select.radiostream_preset_1..10 und select.radiosender_<box> (Paket radiostream.yaml).

const RSP_PLAYERS = [
  { id: '87_5', label: '87.5' },
  { id: '97_0', label: '97.0' },
  { id: '105_9', label: '105.9' },
];

class RadiostreamPresetCard extends HTMLElement {
  setConfig(config) {
    this._config = Object.assign({ title: 'Radiostream', model: 'RS-970' }, config || {});
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this._built = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) this._build();
    this._update();
  }

  getCardSize() { return 8; }
  getGridOptions() { return { columns: 'full' }; }

  _st(id) { return this._hass && this._hass.states[id] ? this._hass.states[id] : null; }
  _short(name) { return (name || '').replace(/^Radio Bob!\s*/i, '').replace(/^RADIO BOB\s*-\s*/i, ''); }
  _select(entity, option) {
    if (this._hass) this._hass.callService('select', 'select_option', { entity_id: entity, option });
  }

  _build() {
    const slots = [];
    for (let n = 1; n <= 10; n++) {
      slots.push(`<label class="slot" data-n="${n}"><span class="num">${n}</span>` +
        `<select data-e="select.radiostream_preset_${n}" aria-label="Preset ${n}"></select>` +
        `<span class="air"></span></label>`);
    }
    const boxes = RSP_PLAYERS.map(p =>
      `<div class="box" data-p="${p.id}">` +
      `<div class="bhead"><span class="led"></span><span class="freq">${p.label}</span><span class="unit">MHz</span></div>` +
      `<select data-e="select.radiosender_${p.id}" aria-label="Sender ${p.label}"></select>` +
      `<div class="btitle"></div></div>`).join('');

    this.shadowRoot.innerHTML = `
      <style>${RadiostreamPresetCard.styles}</style>
      <ha-card>
        <div class="chassis">
          <div class="head">
            <div class="brand">${this._config.title}<small>Preset Memory · ${this._config.model}</small></div>
            <div class="badges"><span>10 Station Memory</span><span>3 Zone</span></div>
          </div>
          <div class="window">
            <div class="vfd">
              <div class="inds">
                <span class="ind i-mem on">MEMORY</span>
                <span class="ind i-air">ON AIR</span>
                <span class="ind i-cnt on"></span>
              </div>
              <div class="grid">${slots.join('')}</div>
            </div>
          </div>
          <div class="strip"><span>Senderauswahl</span></div>
          <div class="boxes">${boxes}</div>
        </div>
      </ha-card>`;

    this.shadowRoot.querySelectorAll('select').forEach(s => {
      s.addEventListener('change', () => {
        this._select(s.dataset.e, s.value);
        s.blur();
      });
    });
    this._built = true;
  }

  _fill(s, st) {
    const o = st && Array.isArray(st.attributes.options) ? st.attributes.options : [];
    const sig = o.join('|');
    if (s._sig !== sig) {
      s.innerHTML = '';
      o.forEach(name => {
        const el = document.createElement('option');
        el.value = name;
        el.textContent = this._short(name) || name;
        s.appendChild(el);
      });
      s._sig = sig;
    }
    const cur = st ? st.state : '';
    if (this.shadowRoot.activeElement !== s && s.value !== cur) s.value = cur;
    s.disabled = !st;
    s.title = cur;
    return o.length;
  }

  _update() {
    if (!this._built || !this._hass) return;
    const root = this.shadowRoot;
    const onAir = {};
    let stations = 0;
    RSP_PLAYERS.forEach(p => {
      const sel = this._st(`select.radiosender_${p.id}`);
      const mp = this._st(`media_player.musik_radiostream_${p.id}`);
      const box = root.querySelector(`.box[data-p="${p.id}"]`);
      const state = mp ? mp.state : 'unavailable';
      const playing = state === 'playing';
      box.querySelector('.led').className = 'led ' + (playing ? 'green' : (state === 'unavailable' ? 'red' : 'amber'));
      stations = Math.max(stations, this._fill(box.querySelector('select'), sel));
      let title = mp && mp.attributes.media_title ? mp.attributes.media_title : '';
      if (title.includes(': ')) title = title.split(': ').slice(1).join(': ');
      const t = playing ? title : (state === 'unavailable' ? 'NO LINK' : 'STANDBY');
      const tEl = box.querySelector('.btitle');
      if (tEl.textContent !== t) tEl.textContent = t;
      tEl.title = t;
      box.classList.toggle('playing', playing);
      box.classList.toggle('dead', state === 'unavailable');
      if (sel && playing) (onAir[sel.state] = onAir[sel.state] || []).push(p.label);
    });

    let live = 0;
    root.querySelectorAll('.slot').forEach(slot => {
      const st = this._st(`select.radiostream_preset_${slot.dataset.n}`);
      this._fill(slot.querySelector('select'), st);
      const air = st ? (onAir[st.state] || []) : [];
      slot.querySelector('.air').textContent = air.join(' · ');
      slot.classList.toggle('live', air.length > 0);
      slot.classList.toggle('live2', air.length > 1);
      if (air.length) live++;
    });
    root.querySelector('.i-air').classList.toggle('on', live > 0);
    root.querySelector('.i-cnt').textContent = stations ? `ST ${stations}` : 'ST –';
  }
}

RadiostreamPresetCard.styles = `
  :host { display:block; padding:10px 10px 24px; box-sizing:border-box; }
  ha-card { background:none; box-shadow:none; border:none; overflow:visible; }
  .chassis {
    --vfd:#63f2e4; --vfd-glow:rgba(99,242,228,.65); --amber:#ffa23a; --red:#ff4d3d; --print:#b9b4a6; --gold:#cbb57c;
    position:relative; max-width:620px; margin:0 auto; padding:14px 16px 18px; border-radius:6px;
    background:
      repeating-linear-gradient(0deg, rgba(255,255,255,.028) 0 1px, rgba(0,0,0,.05) 1px 2px, transparent 2px 3px),
      linear-gradient(180deg, #2c2c2f 0%, #1b1b1d 45%, #111113 100%);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.22), inset 0 -1px 0 rgba(0,0,0,.8), inset 0 0 0 1px #000, 0 12px 24px rgba(0,0,0,.5);
    font-family: Antonio, 'Arial Narrow', 'Roboto Condensed', sans-serif; color:var(--print);
  }
  .chassis::before, .chassis::after { content:''; position:absolute; bottom:-10px; width:56px; height:10px;
    background:linear-gradient(#060607,#232325); border-radius:0 0 6px 6px; box-shadow:0 3px 5px rgba(0,0,0,.5); }
  .chassis::before { left:30px; }
  .chassis::after { right:30px; }

  .head { display:flex; justify-content:space-between; align-items:flex-end; gap:10px; }
  .brand { font-size:21px; letter-spacing:3px; text-transform:uppercase; color:var(--gold); line-height:1.05; }
  .brand small { display:block; font-size:10px; letter-spacing:2.5px; color:var(--print); opacity:.85; margin-top:3px; }
  .badges { display:flex; flex-wrap:wrap; justify-content:flex-end; gap:4px; }
  .badges span { font-size:8.5px; letter-spacing:1.2px; text-transform:uppercase; padding:1px 5px; white-space:nowrap;
    border:1px solid rgba(185,180,166,.55); border-radius:2px; }

  .window { margin-top:10px; padding:5px; border-radius:5px; background:#050506;
    box-shadow: inset 0 2px 5px #000, 0 1px 0 rgba(255,255,255,.09); }
  .vfd { position:relative; padding:8px 10px 10px; border-radius:3px; overflow:hidden;
    background:linear-gradient(180deg,#07110f,#030807); color:var(--vfd); text-shadow:0 0 6px var(--vfd-glow);
    font-family:'Courier New', ui-monospace, monospace; text-transform:uppercase; }
  .vfd::after { content:''; position:absolute; inset:0; pointer-events:none;
    background:linear-gradient(115deg, rgba(255,255,255,.06) 0 26%, transparent 26.5%); }
  .inds { display:flex; align-items:center; gap:9px; font-family: Antonio, 'Arial Narrow', sans-serif; font-size:10.5px; letter-spacing:1.3px; }
  .ind { opacity:.14; transition:opacity .3s ease; white-space:nowrap; }
  .ind.on { opacity:1; }
  .i-air { color:var(--amber); text-shadow:0 0 6px rgba(255,162,58,.7); }
  .i-cnt { margin-left:auto; }

  .grid { display:grid; grid-template-columns:1fr 1fr; grid-template-rows:repeat(5,auto); grid-auto-flow:column; gap:2px 14px; margin-top:8px; }
  .slot { position:relative; display:flex; align-items:center; gap:6px; min-width:0; height:30px; border-bottom:1px dashed rgba(99,242,228,.16); }
  .num { flex:0 0 18px; text-align:right; font-family: Antonio, 'Arial Narrow', sans-serif; font-size:15px; opacity:.55; }
  .slot.live .num { opacity:1; color:var(--amber); text-shadow:0 0 6px rgba(255,162,58,.7); }
  .slot select { flex:1; min-width:0; }
  .slot.live select { padding-right:52px; background-position:right 4px center; }
  .slot.live2 select { padding-right:82px; }
  .air { position:absolute; right:18px; top:50%; transform:translateY(-50%); pointer-events:none;
    font-family: Antonio, 'Arial Narrow', sans-serif; font-size:9px; letter-spacing:.8px; color:var(--amber);
    text-shadow:0 0 5px rgba(255,162,58,.6); background:#050d0b; padding-left:4px; }

  select { height:28px; font-family:inherit; font-size:13px; font-weight:700; letter-spacing:1px; text-transform:uppercase;
    color:var(--vfd); text-shadow:0 0 6px var(--vfd-glow); color-scheme:dark; background:transparent; border:none; outline:none;
    padding:0 18px 0 2px; cursor:pointer; -webkit-appearance:none; appearance:none; text-overflow:ellipsis; white-space:nowrap;
    background:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='5'%3E%3Cpath d='M0 0l4 5 4-5z' fill='%2363f2e4'/%3E%3C/svg%3E") no-repeat right 4px center; }
  select:focus { color:#fff; }
  select:disabled { opacity:.3; cursor:default; }
  option { background:#07110f; color:var(--vfd); text-transform:none; }

  .strip { display:flex; align-items:center; gap:8px; margin:16px 0 8px; font-size:9.5px; letter-spacing:1.5px; text-transform:uppercase; }
  .strip::before, .strip::after { content:''; flex:1; height:1px; background:rgba(185,180,166,.35); }
  .strip span { opacity:.85; }

  .boxes { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; }
  .box { min-width:0; padding:7px 8px 6px; border-radius:3px;
    background:linear-gradient(180deg,#3d3d41,#232326 55%,#18181a);
    box-shadow: inset 0 1px 0 rgba(255,255,255,.18), inset 0 -1px 0 rgba(0,0,0,.7), 0 0 0 1px #000, 0 2px 3px rgba(0,0,0,.6); }
  .box.playing { box-shadow: inset 0 1px 0 rgba(255,255,255,.18), inset 0 -3px 0 var(--amber), 0 0 0 1px #000, 0 2px 3px rgba(0,0,0,.6); }
  .bhead { display:flex; align-items:baseline; gap:5px; color:#d8d4c8; }
  .freq { font-size:17px; letter-spacing:1px; }
  .box.playing .freq { color:var(--amber); text-shadow:0 0 6px rgba(255,162,58,.55); }
  .unit { font-size:9px; letter-spacing:1px; opacity:.7; }
  .led { flex:0 0 auto; align-self:center; width:7px; height:7px; border-radius:50%; background:#33302c; box-shadow:inset 0 1px 1px rgba(0,0,0,.7); }
  .led.green { background:#42ff78; box-shadow:0 0 6px #42ff78; }
  .led.amber { background:var(--amber); box-shadow:0 0 6px var(--amber); }
  .led.red { background:var(--red); box-shadow:0 0 6px var(--red); }
  .box select { width:100%; margin-top:5px; padding-left:6px; border-radius:2px; background-color:#060c0b;
    box-shadow:inset 0 1px 4px #000; font-size:12px; }
  .btitle { margin-top:4px; font-family:'Courier New', ui-monospace, monospace; font-size:9.5px; letter-spacing:.5px;
    color:var(--vfd); opacity:.75; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; min-height:12px; }
  .box.dead .btitle { color:var(--red); opacity:1; }

  @media (max-width: 480px) {
    .chassis { padding:13px 12px 16px; }
    .brand { font-size:19px; }
    .badges span:last-child { display:none; }
    .grid { gap:2px 10px; }
    .slot { height:36px; }
    select { font-size:12px; height:34px; }
    .boxes { gap:6px; }
    .box { padding:7px 6px 6px; }
    .freq { font-size:16px; }
    .box select { height:36px; font-size:11px; }
  }
`;

if (!customElements.get('radiostream-preset-card')) {
  customElements.define('radiostream-preset-card', RadiostreamPresetCard);
  window.customCards = window.customCards || [];
  window.customCards.push({ type: 'radiostream-preset-card', name: 'Radiostream Preset Memory', description: 'Presets und Senderwahl der drei Radiostream-Boxen im Stil des RS-970-Receivers' });
}
