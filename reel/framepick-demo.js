/* Framepick prototype states: what is real, what is a local demo, what is not built.
 *
 * Everything here is front-end only. The demo purchase never sends a request, never
 * charges anything and never grants a real viewing right; it exists so the state
 * machine can be reviewed before any payment provider is connected. */
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => [...document.querySelectorAll(selector)];

  const store = {
    key: 'framepick:demo:orders:v1',
    read() {
      try {
        const parsed = JSON.parse(localStorage.getItem(this.key) || '[]');
        return Array.isArray(parsed) ? parsed : [];
      } catch { return []; }
    },
    write(orders) {
      try { localStorage.setItem(this.key, JSON.stringify(orders)); } catch { /* demo data is optional */ }
    }
  };

  /* Service states: ready = works on this page, local = works locally / not deployed,
   * missing = not built. Each entry names what a real rollout would need. */
  const SERVICES = [
    { name: '片库发现：搜索、组合筛选、排序、收藏、详情', state: 'ready',
      detail: '本页面的真实功能。作品信息来自片库记录，收藏只保存在此浏览器。',
      need: '无需后端；大规模后改由片库接口提供。' },
    { name: '榜单 · 每日更新', state: 'ready',
      detail: '按本站收录日期排序，数据来自片库本身。', need: '无需后端。' },
    { name: '榜单 · 近 10 天热门', state: 'local',
      detail: '按本站「前往原作」的去重跳转次数排序：北京时间今天及前 9 个自然日，同一访客每部作品每天最多计一次，仅原作入口计入。页面明确标注这是跳转次数，不是播放量。',
      need: '需要部署统计接口与服务端持久化；正式站点未部署时该榜如实留空。' },
    { name: '榜单 · 口碑高分', state: 'local',
      detail: '使用站内访客评分，试行至少 5 人、均分 8 分与样本加权；未达门槛不展示，也不编造分数。',
      need: '需要部署评价服务与评分快照；没有评分时显示空状态，不显示“连续高分”。' },
    { name: '访客评价与评分', state: 'local',
      detail: '本地服务可用，签名 Cookie 识别访客，可在本浏览器更新或撤回；正式站点尚未部署。',
      need: 'HTTPS 同源评价接口、服务端存储、限流与内容审核；跨站 Cookie 与多实例写入需另行设计。' },
    { name: '账号（邮箱＋密码）', state: 'local',
      detail: '本地可用，仅为本原型的演示账号：密码哈希与会话都在本机，不是线上账号服务。访客评价不并入账号，也不能凭昵称认领。',
      need: '部署账号服务、邮箱验证与找回密码邮件、跨设备会话与安全审计。' },
    { name: '单片购票与支付', state: 'missing',
      detail: '未接入。本页只提供演示流程：不收任何费用，不产生真实订单，不声称点击即完成购买。',
      need: '商户号（微信支付／支付宝）、下单与异步回调接口、服务端决定的价格与权益、重复通知幂等、对账与发票。' },
    { name: '我的影院与授权期内反复观看', state: 'missing',
      detail: '未接入。演示权益只保存在此浏览器，不代表可以播放授权正片。',
      need: '媒资加密或签名 URL、授权期校验、播放器、并发与下载限制。' },
    { name: '创作者投稿、审核、授权与收益结算', state: 'missing',
      detail: '未接入。当前只保留流程说明与合作邮箱，分成比例与结算周期未确定，不填写固定承诺。',
      need: '审核后台、权利材料留痕、合同与分成规则、有效订单与退款扣减、结算状态。' },
    { name: '搜片 AI 调度', state: 'missing',
      detail: '未实施。首批来源为小红书、抖音、哔哩哔哩，人工核实后才进入片库。',
      need: '调度任务、平台数据的合规来源、去重与看片评估流程。' }
  ];
  const STATE_LABEL = { ready: '已实现', local: '本地演示 · 正式未部署', missing: '未接入' };

  const DEMO_FILM = '演示影片 · 示例授权正片（非真实作品）';
  const RIGHTS = '购买权益：在该作品授权期内反复观看；不是永久拥有，也不是 48 小时租赁。价格与授权期由服务端决定。';
  const TIMEOUT_MS = 900;

  let orders = store.read();
  let signedIn = false;
  let draft = null;
  let timer = null;

  function pad(n) { return String(n).padStart(2, '0'); }
  function stamp(ms) {
    const date = new Date(ms);
    return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate());
  }

  function persist() { store.write(orders); }

  function openDialog(dialog) {
    if (!dialog || dialog.open) return;
    dialog.showModal();
    document.body.classList.add('has-dialog');
  }
  function closeDialog(dialog) {
    if (!dialog?.open) return;
    dialog.close();
    if (!$('#filmDialog')?.open) document.body.classList.remove('has-dialog');
  }

  /* ---------- prototype strip + service status ---------- */

  function renderServices() {
    const list = $('#statusList');
    if (!list) return;
    list.textContent = '';
    for (const service of SERVICES) {
      const row = document.createElement('article');
      row.className = 'status-row';
      row.dataset.state = service.state;
      const head = document.createElement('h3');
      head.textContent = service.name;
      const chip = document.createElement('span');
      chip.className = 'state-chip';
      chip.dataset.state = service.state;
      chip.textContent = STATE_LABEL[service.state];
      head.after(chip);
      const detail = document.createElement('p');
      detail.className = 'status-detail';
      detail.textContent = service.detail;
      const need = document.createElement('p');
      need.className = 'status-need';
      need.textContent = '正式接入需要：' + service.need;
      row.append(head, chip, detail, need);
      list.append(row);
    }
  }

  function wirePrototypeBar() {
    const bar = $('#prototypeBar');
    if (!bar) return;
    let dismissed = false;
    try { dismissed = sessionStorage.getItem('framepick:demo:bar') === 'off'; } catch { /* private mode */ }
    bar.hidden = dismissed;
    $('#prototypeClose')?.addEventListener('click', () => {
      bar.hidden = true;
      try { sessionStorage.setItem('framepick:demo:bar', 'off'); } catch { /* private mode */ }
    });
    $('#statusOpen')?.addEventListener('click', () => { renderServices(); openDialog($('#statusDialog')); });
    for (const opener of $$('[data-open-status]')) {
      opener.addEventListener('click', (event) => {
        event.preventDefault();
        renderServices();
        openDialog($('#statusDialog'));
      });
    }
    $('#statusClose')?.addEventListener('click', () => closeDialog($('#statusDialog')));
    $('#statusDialog')?.addEventListener('close', () => {
      if (!$('#filmDialog')?.open && !$('#purchaseDialog')?.open) document.body.classList.remove('has-dialog');
    });
  }

  /* ---------- demo purchase: every state a real checkout has to handle ---------- */

  const COPY = {
    login: { chip: '未登录', title: '先登录，再购买（演示）',
      body: '单片观影需要账号来保存订单与观影权益。本原型没有真实账号服务，登录状态只在本地演示；未登录也可以继续免费发现、评价与跳转原作。' },
    unpaid: { chip: '未购买', title: '确认价格与权益（演示）',
      body: RIGHTS },
    paying: { chip: '支付中', title: '正在跳转支付（演示）', body: '演示流程不会调用任何支付渠道，也不会收费。' },
    confirming: { chip: '确认中', title: '服务端正在确认订单（演示）', body: '真实接入时由支付回调与服务端确认；重复通知不会重复发权益或重复计收益。' },
    active: { chip: '已购 · 授权有效', title: '已购（演示）', body: '演示订单已确认，不代表真实付款，也不能播放授权正片。' },
    failed: { chip: '支付失败', title: '支付未完成（演示）', body: '未产生任何费用，可以重试或取消。' },
    canceled: { chip: '已取消', title: '订单已取消（演示）', body: '未产生任何费用，也没有获得观影权益。' },
    refunding: { chip: '退款中', title: '退款处理中（演示）', body: '退款期间权益仍然保留，处理完成后收回。' },
    refunded: { chip: '已退款', title: '已退款（演示）', body: '款项退回，观影权益已收回；真实结算以支付渠道与对账结果为准。' },
    expired: { chip: '授权到期', title: '授权期已结束（演示）', body: '可重新购买以继续观看；到期不等于永久拥有。' },
    unavailable: { chip: '暂时无法播放', title: '影片已下架或暂不可播（演示）', body: '已购订单保留，放映恢复后可继续观看；涉及下架的退款规则另行说明。' }
  };
  const ACTIONS = {
    login: { main: '去登录（演示）', secondary: '取消' },
    unpaid: { main: '演示支付 3 元', secondary: '取消' },
    paying: { main: '支付中…', secondary: '取消' },
    confirming: { main: '确认中…', secondary: '取消' },
    active: { main: '演示：申请退款', secondary: '演示：授权到期' },
    failed: { main: '重试演示支付', secondary: '取消订单' },
    canceled: { main: '重新演示购票', secondary: '关闭' },
    refunding: { main: '退款中…', secondary: '关闭' },
    refunded: { main: '重新演示购票', secondary: '关闭' },
    expired: { main: '重新演示购票', secondary: '关闭' },
    unavailable: { main: '演示：影片下架后恢复', secondary: '关闭' }
  };

  function activeOrder() { return orders.find((order) => order.film === DEMO_FILM) || null; }

  function setState(state, extra = {}) {
    clearTimeout(timer);
    const order = activeOrder() || { id: 'demo-' + Date.now(), film: DEMO_FILM, price: draft?.price || 3, createdAt: Date.now() };
    Object.assign(order, extra, { state });
    if (!orders.includes(order)) orders.unshift(order);
    if (state === 'active' && !order.expiresAt) order.expiresAt = Date.now() + 30 * 24 * 3600 * 1000;
    persist();
    if (draft) draft.state = state;
    renderCinema();
    renderPurchase();
    if (state === 'paying') timer = setTimeout(() => setState('confirming'), TIMEOUT_MS);
    if (state === 'confirming') timer = setTimeout(() => setState('active'), TIMEOUT_MS + 400);
    if (state === 'refunding') timer = setTimeout(() => setState('refunded'), TIMEOUT_MS);
  }

  function renderPurchase() {
    const dialog = $('#purchaseDialog');
    if (!dialog) return;
    const order = activeOrder();
    const state = draft?.state || order?.state || (signedIn ? 'unpaid' : 'login');
    const copy = COPY[state];
    const action = ACTIONS[state];
    $('#purchaseChip').textContent = copy.chip;
    $('#purchaseChip').dataset.state = state;
    $('#purchaseTitle').textContent = copy.title;
    $('#purchaseBody').textContent = copy.body;
    $('#purchaseMeta').textContent = '演示影片：' + DEMO_FILM + ' · 拟定价格 ' + (order?.price || draft?.price || 3) + ' 元（价格由服务端决定）'
      + (order?.expiresAt ? ' · 演示授权至 ' + stamp(order.expiresAt) : '');
    $('#purchaseAction').textContent = action.main;
    $('#purchaseSecondary').textContent = action.secondary;
    const busy = state === 'paying' || state === 'confirming' || state === 'refunding';
    $('#purchaseAction').disabled = busy;
  }

  function openPurchase(price = 3) {
    const order = activeOrder();
    draft = { price: order?.price || price, state: order?.state || (signedIn ? 'unpaid' : 'login') };
    renderPurchase();
    openDialog($('#purchaseDialog'));
  }

  function advance() {
    const state = draft?.state || activeOrder()?.state || 'login';
    switch (state) {
      case 'login':
        openDialog($('#accountDialog'));
        return;
      case 'unpaid':
        setState('paying', { price: draft.price });
        return;
      case 'failed':
        setState('paying');
        return;
      case 'canceled': case 'refunded': case 'expired':
        setState('unpaid');
        return;
      case 'active':
        setState('refunding');
        return;
      case 'active-expire':
        setState('expired');
        return;
      case 'unavailable':
        setState('active');
        return;
      default:
        return;
    }
  }

  function secondaryAction() {
    const state = draft?.state || 'unpaid';
    if (state === 'active') { setState('expired'); return; }
    if (state === 'failed' || state === 'canceled') setState('canceled');
    closeDialog($('#purchaseDialog'));
  }

  function wirePurchase() {
    const dialog = $('#purchaseDialog');
    if (!dialog) return;
    for (const opener of $$('[data-demo-purchase]')) {
      opener.addEventListener('click', (event) => {
        event.preventDefault();
        draft = { price: Number(opener.dataset.demoPrice || 3), state: null };
        const order = activeOrder();
        if (order) draft.state = order.state;
        openPurchase(draft.price);
        if (order) renderPurchase();
      });
    }
    $('#purchaseAction').addEventListener('click', () => { advance(); renderPurchase(); });
    $('#purchaseSecondary').addEventListener('click', secondaryAction);
    $('#purchaseClose')?.addEventListener('click', () => closeDialog(dialog));
    $('#purchaseSimulate')?.addEventListener('click', () => setState('failed'));
    $('#purchaseUnavailable')?.addEventListener('click', () => setState('unavailable'));
    dialog.addEventListener('close', () => {
      draft = null;
      if (!$('#filmDialog')?.open && !$('#statusDialog')?.open) document.body.classList.remove('has-dialog');
    });
  }

  /* ---------- 我的影院 ---------- */

  function renderCinema() {
    const list = $('#cinemaList');
    if (!list) return;
    list.textContent = '';
    const live = orders.filter((order) => ['active', 'refunding', 'unavailable'].includes(order.state));
    $('#cinemaEmpty').hidden = live.length !== 0;
    $('#cinemaEmpty').textContent = orders.length === 0
      ? '还没有演示订单。本页的购票、授权与收益均未接入，「演示购票」只用来查看界面状态。'
      : '当前没有有效的演示权益（已退款或授权到期）。';
    for (const order of orders) {
      const row = document.createElement('article');
      row.className = 'cinema-row';
      const title = document.createElement('h3');
      title.textContent = order.film;
      const chip = document.createElement('span');
      chip.className = 'state-chip';
      chip.dataset.state = order.state;
      chip.textContent = COPY[order.state]?.chip || order.state;
      const meta = document.createElement('p');
      meta.className = 'cinema-meta';
      meta.textContent = '演示订单 · 拟定 ' + order.price + ' 元 · 创建于 ' + stamp(order.createdAt)
        + (order.expiresAt ? ' · 授权至 ' + stamp(order.expiresAt) : '')
        + ' · 不产生真实付款或放映权益';
      const actions = document.createElement('div');
      actions.className = 'cinema-actions';
      const watch = document.createElement('button');
      watch.type = 'button';
      watch.className = 'button secondary demo-button';
      watch.textContent = '演示：尝试播放';
      watch.addEventListener('click', () => {
        $('#cinemaNote').textContent = '授权放映未接入：演示权益不能播放正片。真实接入需要签名地址与授权期校验。';
      });
      const refund = document.createElement('button');
      refund.type = 'button';
      refund.className = 'button secondary demo-button';
      refund.textContent = '演示：申请退款';
      refund.addEventListener('click', () => setState('refunding'));
      const drop = document.createElement('button');
      drop.type = 'button';
      drop.className = 'button secondary demo-button';
      drop.textContent = '演示：影片下架';
      drop.addEventListener('click', () => setState('unavailable'));
      actions.append(watch, refund, drop);
      row.append(title, chip, meta, actions);
      list.append(row);
    }
    $('#cinemaClear')?.toggleAttribute('hidden', orders.length === 0);
  }

  function wireCinema() {
    if (!$('#cinemaList')) return;
    $('#cinemaClear')?.addEventListener('click', () => {
      orders = [];
      persist();
      renderCinema();
      $('#cinemaNote').textContent = '已清除此浏览器中的演示订单。真实订单与收益不会保存在浏览器里。';
    });
    renderCinema();
  }

  /* ---------- degrade gracefully when the creator module is not shipped ---------- */

  function wireCreatorFallback() {
    const entry = $('#creatorEntry');
    const dialog = $('#creatorDialog');
    if (!entry || !dialog || window.framepickCreatorsReady) return;
    entry.addEventListener('click', () => {
      $('#creatorAvailability').textContent = '创作者投稿、审核与收益结算尚未接入：当前为演示原型，只保留流程说明与合作邮箱，不产生真实投稿或收益记录。';
      $('#creatorBody').hidden = true;
      openDialog(dialog);
    });
    for (const closer of $$('#creatorClose, #creatorDialog [data-close-creator]')) {
      closer.addEventListener('click', () => closeDialog(dialog));
    }
  }

  function wireDemoChips() {
    // Every dialog that depends on an unbuilt service carries a visible 演示 marker.
    for (const node of $$('[data-demo-chip]')) {
      node.textContent = node.dataset.demoChip || '演示';
    }
  }

  wirePrototypeBar();
  wirePurchase();
  wireCinema();
  wireCreatorFallback();
  wireDemoChips();
  renderServices();

  window.addEventListener('framepick:account', ({ detail }) => {
    signedIn = Boolean(detail?.signedIn);
    if (signedIn && draft?.state === 'login') {
      draft.state = 'unpaid';
      renderPurchase();
    }
    const entry = $('#accountEntry');
    if (entry) entry.dataset.demoAccount = String(signedIn);
  });

  window.dispatchEvent(new CustomEvent('framepick:demo-ready', { detail: { services: SERVICES.length } }));
})();
