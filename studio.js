(() => {
  'use strict';

  const $ = (selector) => document.querySelector(selector);
  const siteBaseURL = new URL('./', window.location.href);
  const isLoopback = ['localhost', '127.0.0.1', '[::1]', '::1'].includes(window.location.hostname);
  const isFile = window.location.protocol === 'file:';
  const hiddenWorkIds = new Set(['featured-giant-wheel']);
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const narrowScreen = window.matchMedia('(max-width: 700px)');
  const coarsePointer = window.matchMedia('(pointer: coarse)');

  const copy = {
    cn: {
      skip: '跳转到作品', navWorks: '作品', navAbout: '关于', navContact: '联系', admin: '作品管理',
      intro: '独立影像创作者 · 南京', heroTitle: '想象，在此成片',
      heroDesc: '用三维构建世界，用影像讲述故事。\n从一个念头，到让人记住的画面。',
      explore: '探索作品', selected: '精选放映', watch: '观看完整作品',
      discipline: 'AI 影像 / 三维动画 / 动态视觉 / 剪辑', scroll: '向下发现更多',
      portfolio: '每个画面，都有来处', worksTitle: '作品集',
      worksIntro: '一些故事，一些实验。\n在不同的媒介里，寻找自己的表达。',
      all: '全部作品', story: '叙事短片', motion: '三维与动画', edit: '剪辑与视觉',
      empty: '还没有找到这部作品', emptyHint: '试试其他关键词，或查看全部作品。', reset: '查看全部作品',
      aboutLabel: '镜头背后', aboutTitle: '创作的起点，\n是好奇心', portrait: '我的数字人形象',
      aboutLead: '你好，我是橘小桔，也叫 Highstrith。',
      aboutCopy: '我在南京，创作 AI 短片、三维动画和动态影像。从脚本、角色到剪辑与成片，我喜欢把不同的工具放在一起，让脑海里的世界有自己的光线、节奏和情绪。',
      aboutSecond: '这里既有完整的故事，也有尚在探索的视觉实验。比起固定的风格，我更在意每一次创作是否带来新的表达。',
      practiceOne: '故事与影像', practiceTwo: '三维与角色', practiceThree: '剪辑与后期', aboutContact: '聊聊你的想法',
      contactLabel: '从一句「我有个想法」开始', location: '中国 · 南京', contactTitle: '下一个画面，\n一起完成',
      wechatAccount: '微信 Gw1sgdsj_787', elsewhere: '也可以在这里找到我',
      wechat: '微信', douyin: '抖音', red: '小红书', bili: '哔哩哔哩',
      sound: '背景音乐', backTop: '回到顶部 ↑', playerHint: 'Esc 关闭', qrHint: '打开对应 App 扫码，和我打个招呼',
      searchPlaceholder: '寻找一部作品', searchLabel: '搜索作品', filterLabel: '作品分类', featureLabel: '选择精选作品',
      closeVideo: '关闭视频', closeQR: '关闭二维码', play: '播放', retry: '重试播放',
      loading: '正在加载作品…', buffering: '正在缓冲…', restricted: '点击播放，开始观看这部作品。',
      error: '暂时无法加载这部作品，请重试。', slow: '加载比平时慢，可以继续等待或重试。',
      musicOn: '开', musicOff: '关', playMusic: '播放背景音乐', pauseMusic: '暂停背景音乐',
    },
    en: {
      skip: 'Skip to works', navWorks: 'Works', navAbout: 'About', navContact: 'Contact', admin: 'Manage works',
      intro: 'Independent image maker · Nanjing', heroTitle: 'Imagination, in motion',
      heroDesc: 'Building worlds in 3D. Telling stories through film.\nFrom a first thought to an image that stays with you.',
      explore: 'Explore the works', selected: 'Selected screening', watch: 'Watch the full film',
      discipline: 'AI films / 3D animation / Motion design / Editing', scroll: 'Discover more below',
      portfolio: 'Every image starts somewhere', worksTitle: 'The works',
      worksIntro: 'A few stories. A few experiments.\nFinding my own expression across different media.',
      all: 'All works', story: 'Narrative films', motion: '3D & animation', edit: 'Editing & visuals',
      empty: 'No works found', emptyHint: 'Try another keyword, or browse all the works.', reset: 'Show all works',
      aboutLabel: 'Behind the lens', aboutTitle: 'It starts\nwith curiosity', portrait: 'My digital persona',
      aboutLead: 'Hello, I’m 橘小桔, also known as Highstrith.',
      aboutCopy: 'Based in Nanjing, I make AI short films, 3D animation and moving images. From scripts and characters to editing and the finished film, I enjoy bringing different tools together to give imagined worlds their own light, rhythm and emotion.',
      aboutSecond: 'Some of these works tell complete stories; others are visual experiments still being explored. Each project is a chance to find a new way to express an idea.',
      practiceOne: 'Stories & images', practiceTwo: '3D & characters', practiceThree: 'Editing & post', aboutContact: 'Share your idea',
      contactLabel: 'It starts with “I have an idea”', location: 'Nanjing · China', contactTitle: 'Let’s make\nthe next image',
      wechatAccount: 'WeChat Gw1sgdsj_787', elsewhere: 'Find me elsewhere',
      wechat: 'WeChat', douyin: 'Douyin', red: 'Xiaohongshu', bili: 'Bilibili',
      sound: 'Background music', backTop: 'Back to top ↑', playerHint: 'Esc to close', qrHint: 'Scan in the matching app and say hello',
      searchPlaceholder: 'Find a work', searchLabel: 'Search works', filterLabel: 'Filter works', featureLabel: 'Choose a featured work',
      closeVideo: 'Close video', closeQR: 'Close QR code', play: 'Play', retry: 'Try again',
      loading: 'Loading the film…', buffering: 'Buffering…', restricted: 'Press play to watch this film.',
      error: 'This film could not be loaded. Please try again.', slow: 'Loading is taking longer than usual. Keep waiting or try again.',
      musicOn: 'On', musicOff: 'Off', playMusic: 'Play background music', pauseMusic: 'Pause background music',
    },
  };

  const grid = $('#worksGrid');
  const filters = $('#workFilters');
  const search = $('#workSearch');
  const hero = $('.hero-feature');
  const heroVideo = $('#heroPreview');
  const heroPoster = $('#heroPoster');
  const heroControls = $('#featureControls');
  const player = $('#workPlayer');
  const playerVideo = $('#workPlayerVideo');
  const playerStatus = $('#workPlayerStatus');
  const playerMessage = $('#workPlayerMessage');
  const playerAction = $('#workPlayerAction');
  const music = $('#bgMusic');
  const musicButton = $('#musicToggle');
  const qrDialog = $('#social-qr-dialog');
  const qrPreview = $('#social-qr-preview');

  let language = 'cn';
  let works = [];
  let featuredWorks = [];
  let selectedFeatureId = '';
  let currentFilter = 'all';
  let cardRecords = [];
  let hoveredCard = null;
  let focusedCard = null;
  let activePreview = null;
  let heroNearViewport = true;
  let playerWork = null;
  let playerSource = '';
  let playerReturnFocus = null;
  let playerController = null;
  let playerTimer = null;
  let playerState = '';
  let musicWanted = false;
  let musicGeneration = 0;
  let activeQrButton = null;
  let qrReturnFocus = null;
  let hoveredQrButton = null;

  const t = (key) => copy[language][key] || '';
  const text = (value) => typeof value === 'string' ? value : '';
  const workText = (work, field) => text(work[(language === 'cn' ? 'cn' : 'en') + field]) || text(work['cn' + field]) || text(work['en' + field]);
  const workTitle = (work) => workText(work, 'Title');
  const create = (tag, className, content) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = content;
    return element;
  };

  // Catalogue text is never interpreted as markup; public media stays inside assets/.
  function mediaURL(value) {
    const path = text(value).trim().replace(/^\.\//, '');
    if (!path.startsWith('assets/') || path.includes('\\') || /(^|\/)\.\.?(\/|$)/.test(path)) return '';
    try {
      const url = new URL(path, siteBaseURL);
      return url.href.startsWith(new URL('assets/', siteBaseURL).href) ? url.href : '';
    } catch (_) {
      return '';
    }
  }

  function setLines(element, value) {
    if (!element) return;
    const fragment = document.createDocumentFragment();
    value.split('\n').forEach((line, index) => {
      if (index) fragment.append(document.createElement('br'));
      fragment.append(document.createTextNode(line));
    });
    element.replaceChildren(fragment);
  }

  function categories(work) {
    const category = text(work.cnSub);
    const result = new Set();
    if (/短片|叙事|科幻|喜剧/.test(category)) result.add('story');
    if (/三维|动画|角色|片头/.test(category)) result.add('motion');
    if (/剪辑|运动|特效/.test(category) || !result.size) result.add('edit');
    return result;
  }

  function normalizeCatalogue(data) {
    if (!Array.isArray(data)) return null;
    const seen = new Set();
    return data.map((work, index) => ({ work, index }))
      .filter(({ work }) => {
        if (!work || typeof work !== 'object' || !text(work.id) || hiddenWorkIds.has(work.id) || seen.has(work.id)) return false;
        seen.add(work.id);
        return true;
      })
      .sort((a, b) => text(b.work.createdAt).localeCompare(text(a.work.createdAt)) || a.index - b.index)
      .map(({ work }) => work);
  }

  async function fetchCatalogue(url) {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 6000);
    try {
      const response = await fetch(url, { signal: controller.signal, cache: 'no-cache' });
      if (!response.ok) throw new Error('Catalogue unavailable');
      const payload = await response.json();
      const catalogue = normalizeCatalogue(Array.isArray(payload) ? payload : payload?.works);
      if (catalogue === null) throw new Error('Invalid catalogue');
      return catalogue;
    } finally {
      window.clearTimeout(timeout);
    }
  }

  async function loadCatalogue() {
    const snapshot = typeof baseWorkData !== 'undefined' ? baseWorkData : [];
    let catalogue = null;
    if (!isFile) {
      if (isLoopback) {
        try { catalogue = await fetchCatalogue(new URL('/api/works', siteBaseURL)); } catch (_) { /* Static fallback follows. */ }
      }
      if (catalogue === null) {
        try { catalogue = await fetchCatalogue(new URL('data/works.json', siteBaseURL)); } catch (_) { /* The embedded snapshot also works offline. */ }
      }
    }
    works = catalogue === null ? (normalizeCatalogue(snapshot) || []) : catalogue;
    // Preserve the current film selections while newer uploads keep leading the list.
    const featureReplacements = {
      'work-lying-down-20261001': 'featured-prove-it',
      'added-creative-3': 'work-1783863606674-7ta9sp',
      'added-visual-study': 'featured-exported-film',
    };
    const candidates = works.map((work) => works.find((item) => item.id === featureReplacements[work.id]) || work);
    featuredWorks = [...new Map(candidates.map((work) => [work.id, work])).values()].slice(0, 5);
    if (!featuredWorks.some((work) => work.id === selectedFeatureId)) selectedFeatureId = featuredWorks[0]?.id || '';
    renderCards();
    renderHeroControls();
    updateHero();
    applyFilters();
  }

  function renderCards() {
    stopPreview();
    hoveredCard = null;
    focusedCard = null;
    cardRecords = works.map((work, index) => {
      const card = create('button', 'work-card');
      card.type = 'button';
      card.dataset.workId = work.id;
      const media = create('span', 'work-media');
      const image = create('img');
      const poster = mediaURL(work.poster);
      if (poster) image.src = poster;
      image.loading = index < 3 ? 'eager' : 'lazy';
      image.decoding = 'async';
      const video = create('video');
      video.muted = true;
      video.loop = true;
      video.playsInline = true;
      video.preload = 'none';
      video.setAttribute('aria-hidden', 'true');
      const playMark = create('span', 'card-play', '↗');
      playMark.setAttribute('aria-hidden', 'true');
      media.append(image, video, playMark);
      const caption = create('span', 'work-caption');
      const category = create('span', 'work-category');
      const title = create('span', 'work-title');
      const description = create('span', 'work-description');
      caption.append(category, title, description);
      card.append(media, caption);
      const record = { work, card, media, image, video, category, title, description, categories: categories(work) };
      record.query = ['cnTitle', 'enTitle', 'cnSub', 'enSub', 'cnDesc', 'enDesc']
        .map((key) => text(work[key])).join(' ').normalize('NFKC').toLocaleLowerCase();
      card.addEventListener('pointerenter', (event) => {
        if (event.pointerType !== 'mouse') return;
        hoveredCard = record;
        syncPreview();
      });
      card.addEventListener('pointerleave', () => {
        if (hoveredCard === record) hoveredCard = null;
        syncPreview();
      });
      card.addEventListener('focus', () => { focusedCard = record; syncPreview(); });
      card.addEventListener('blur', () => {
        if (focusedCard === record) focusedCard = null;
        syncPreview();
      });
      card.addEventListener('click', () => openPlayer(work, card));
      return record;
    });
    grid?.replaceChildren(...cardRecords.map(({ card }) => card));
    updateCardText();
    const total = $('.filter-total');
    if (total) total.textContent = String(works.length);
  }

  function updateCardText() {
    cardRecords.forEach(({ work, card, image, category, title, description }) => {
      const name = workTitle(work);
      title.textContent = name;
      category.textContent = workText(work, 'Sub');
      description.textContent = workText(work, 'Desc');
      image.alt = language === 'cn' ? `${name}作品画面` : `Still from ${name}`;
      card.setAttribute('aria-label', `${t('watch')}: ${name}`);
    });
  }

  function applyFilters() {
    const query = (search?.value || '').trim().normalize('NFKC').toLocaleLowerCase();
    let count = 0;
    cardRecords.forEach((record) => {
      const visible = (currentFilter === 'all' || record.categories.has(currentFilter)) && (!query || record.query.includes(query));
      record.card.hidden = !visible;
      if (visible) count++;
    });
    filters?.querySelectorAll('[data-filter]').forEach((button) => {
      const active = button.dataset.filter === currentFilter;
      button.setAttribute('aria-pressed', String(active));
      button.classList.toggle('is-active', active);
    });
    if ($('#worksCount')) $('#worksCount').textContent = language === 'cn' ? `${count} 部作品` : `${count} ${count === 1 ? 'work' : 'works'}`;
    if ($('#emptyState')) $('#emptyState').hidden = count !== 0;
    syncPreview();
  }

  function renderHeroControls() {
    const controls = featuredWorks.map((work, index) => {
      const button = create('button', 'hero-pick');
      button.type = 'button';
      button.dataset.feature = work.id;
      button.setAttribute('aria-label', `${String(index + 1).padStart(2, '0')}: ${workTitle(work)}`);
      button.setAttribute('aria-pressed', String(work.id === selectedFeatureId));
      const image = create('img');
      const poster = mediaURL(work.poster);
      if (poster) image.src = poster;
      image.alt = '';
      image.loading = 'lazy';
      button.append(image, create('span', '', String(index + 1).padStart(2, '0')));
      button.addEventListener('click', () => {
        if (selectedFeatureId === work.id) return;
        selectedFeatureId = work.id;
        updateHero();
      });
      return button;
    });
    heroControls?.replaceChildren(...controls);
  }

  function updateHero() {
    const work = featuredWorks.find((item) => item.id === selectedFeatureId);
    if (!work) {
      stopPreview();
      return;
    }
    const name = workTitle(work);
    const poster = mediaURL(work.poster);
    if (heroPoster) {
      if (poster) heroPoster.src = poster;
      else heroPoster.removeAttribute('src');
      heroPoster.alt = language === 'cn' ? `${name}作品画面` : `Still from ${name}`;
    }
    if ($('#featureTitle')) $('#featureTitle').textContent = name;
    if ($('#featureCategory')) $('#featureCategory').textContent = workText(work, 'Sub');
    if ($('#featurePosition')) $('#featurePosition').textContent = `${String(featuredWorks.indexOf(work) + 1).padStart(2, '0')} / ${String(featuredWorks.length).padStart(2, '0')}`;
    document.querySelectorAll('[data-hero-play]').forEach((button) => button.setAttribute('aria-label', `${t('watch')}: ${name}`));
    heroControls?.querySelectorAll('[data-feature]').forEach((button) => {
      const active = button.dataset.feature === selectedFeatureId;
      button.setAttribute('aria-pressed', String(active));
      button.classList.toggle('is-active', active);
    });
    syncPreview();
  }

  function previewAllowed() {
    return !narrowScreen.matches && finePointer.matches && !reducedMotion.matches && !document.hidden && !player?.open && !qrDialog?.open;
  }

  function nearViewport(element) {
    if (!element || element.hidden) return false;
    const rect = element.getBoundingClientRect();
    return rect.bottom > 0 && rect.top < window.innerHeight && rect.width > 0;
  }

  function stopPreview() {
    if (!activePreview) return;
    const { video, container, controller } = activePreview;
    activePreview = null;
    controller.abort();
    video.pause();
    video.removeAttribute('src');
    video.load();
    container.classList.remove('is-previewing');
  }

  function startPreview(work, video, container) {
    const source = mediaURL(work?.previewVideo);
    if (!source || !video || !container) { stopPreview(); return; }
    if (activePreview?.video === video && activePreview.source === source) return;
    stopPreview();
    const controller = new AbortController();
    const session = { video, container, source, controller };
    activePreview = session;
    video.addEventListener('playing', () => {
      if (activePreview === session) container.classList.add('is-previewing');
    }, { signal: controller.signal });
    video.addEventListener('error', () => {
      if (activePreview === session) stopPreview();
    }, { signal: controller.signal });
    video.muted = true;
    video.src = source;
    video.load();
    video.play()?.catch(() => {
      if (activePreview === session) container.classList.remove('is-previewing');
    });
  }

  function syncPreview() {
    if (!previewAllowed()) { stopPreview(); return; }
    const card = [hoveredCard, focusedCard].find((record) => record && nearViewport(record.card));
    if (card) { startPreview(card.work, card.video, card.card); return; }
    const work = featuredWorks.find((item) => item.id === selectedFeatureId);
    if (work && heroNearViewport) startPreview(work, heroVideo, hero);
    else stopPreview();
  }

  function updateScrollLock() {
    document.body.classList.toggle('modal-open', Boolean(player?.open || qrDialog?.open));
  }

  function clearPlayerTimer() {
    window.clearTimeout(playerTimer);
    playerTimer = null;
  }

  function cancelPlayerSession() {
    clearPlayerTimer();
    playerController?.abort();
    playerController = null;
  }

  function showPlayerState(state) {
    playerState = state;
    if (!playerStatus) return;
    playerStatus.hidden = !state;
    playerStatus.dataset.state = state;
    playerMessage.textContent = state ? t(state) : '';
    const action = ['restricted', 'error', 'slow'].includes(state);
    playerAction.hidden = !action;
    playerAction.textContent = state === 'restricted' ? t('play') : t('retry');
  }

  function schedulePlayerWait(controller) {
    clearPlayerTimer();
    if (document.hidden) return;
    playerTimer = window.setTimeout(() => {
      if (playerController === controller && !controller.signal.aborted && player?.open) showPlayerState('slow');
    }, 15000);
  }

  function attemptPlayerPlay(controller) {
    const attempt = playerVideo.play();
    attempt?.catch((error) => {
      if (controller.signal.aborted || playerController !== controller || error.name === 'AbortError') return;
      clearPlayerTimer();
      showPlayerState(playerVideo.error || error.name === 'NotSupportedError' ? 'error' : 'restricted');
    });
  }

  function loadPlayerSource() {
    cancelPlayerSession();
    playerVideo.pause();
    playerVideo.removeAttribute('src');
    playerVideo.load();
    if (!playerSource) { showPlayerState('error'); return; }
    const controller = new AbortController();
    playerController = controller;
    const listen = (event, callback) => playerVideo.addEventListener(event, callback, { signal: controller.signal });
    listen('playing', () => { clearPlayerTimer(); showPlayerState(''); });
    listen('waiting', () => { showPlayerState('buffering'); schedulePlayerWait(controller); });
    listen('stalled', () => { showPlayerState('buffering'); schedulePlayerWait(controller); });
    listen('canplay', () => {
      clearPlayerTimer();
      if (playerVideo.paused && ['loading', 'buffering', 'slow'].includes(playerState)) showPlayerState('restricted');
    });
    listen('pause', () => {
      if (playerVideo.readyState >= 3 && ['loading', 'buffering', 'slow'].includes(playerState)) showPlayerState('restricted');
    });
    listen('error', () => { clearPlayerTimer(); showPlayerState('error'); });
    showPlayerState('loading');
    schedulePlayerWait(controller);
    playerVideo.src = playerSource;
    playerVideo.load();
    attemptPlayerPlay(controller);
  }

  function updatePlayerText() {
    if (!playerWork) return;
    $('#playerTitle').textContent = workTitle(playerWork);
    $('#playerCategory').textContent = workText(playerWork, 'Sub');
    $('#playerDescription').textContent = workText(playerWork, 'Desc');
    showPlayerState(playerState);
  }

  function openPlayer(work, trigger) {
    if (!player || !playerVideo) return;
    playerWork = work;
    playerReturnFocus = trigger || document.activeElement;
    const mobile = narrowScreen.matches || coarsePointer.matches;
    playerSource = mediaURL(mobile ? (work.mobileVideo || work.video) : (work.webVideo || work.video));
    const poster = mediaURL(work.poster);
    if (poster) playerVideo.poster = poster;
    else playerVideo.removeAttribute('poster');
    stopPreview();
    hideQrPreview();
    if (!player.open) player.showModal();
    updateScrollLock();
    syncMusic();
    updatePlayerText();
    loadPlayerSource();
    $('#workPlayerClose')?.focus({ preventScroll: true });
  }

  function finishPlayer() {
    // Native close events are queued; an old close must not tear down a new film.
    if (player?.open || (!playerWork && !playerReturnFocus)) return;
    cancelPlayerSession();
    playerVideo.pause();
    playerVideo.removeAttribute('src');
    playerVideo.removeAttribute('poster');
    playerVideo.load();
    showPlayerState('');
    playerWork = null;
    playerSource = '';
    const target = playerReturnFocus;
    playerReturnFocus = null;
    updateScrollLock();
    if (target?.isConnected) target.focus({ preventScroll: true });
    syncPreview();
    syncMusic();
  }

  function closePlayer() {
    if (!player?.open) return;
    cancelPlayerSession();
    playerVideo.pause();
    playerVideo.removeAttribute('src');
    playerVideo.load();
    player.close();
    finishPlayer();
  }

  function updateMusicUI() {
    if (!musicButton) return;
    musicButton.setAttribute('aria-pressed', String(musicWanted));
    musicButton.setAttribute('aria-label', musicWanted ? t('pauseMusic') : t('playMusic'));
    if ($('#musicState')) $('#musicState').textContent = musicWanted ? t('musicOn') : t('musicOff');
  }

  function syncMusic() {
    if (!music) return;
    const generation = ++musicGeneration;
    updateMusicUI();
    if (!musicWanted || document.hidden || player?.open || qrDialog?.open) {
      music.pause();
      return;
    }
    music.play()?.catch((error) => {
      if (error.name === 'AbortError' || generation !== musicGeneration) return;
      musicWanted = false;
      updateMusicUI();
    });
  }

  function qrTitle(button) {
    return language === 'cn' ? text(button.dataset.qrTitle) : (text(button.dataset.qrEn) || text(button.dataset.qrTitle));
  }

  function updateQrDialog() {
    if (!activeQrButton) return;
    const title = qrTitle(activeQrButton);
    $('#social-qr-title').textContent = title;
    $('#social-qr-account').textContent = text(activeQrButton.dataset.qrAccount);
    const image = $('#social-qr-image');
    const source = mediaURL(activeQrButton.dataset.qrImage);
    if (source) image.src = source;
    image.alt = language === 'cn' ? `${title}二维码` : `${title} QR code`;
  }

  function openQr(button) {
    if (!qrDialog) return;
    activeQrButton = button;
    qrReturnFocus = button;
    updateQrDialog();
    hideQrPreview();
    stopPreview();
    qrDialog.showModal();
    updateScrollLock();
    syncMusic();
    $('#socialQrClose')?.focus({ preventScroll: true });
  }

  function hideQrPreview() {
    if (qrPreview) qrPreview.hidden = true;
    hoveredQrButton = null;
  }

  function showQrPreview(button) {
    if (!qrPreview || !finePointer.matches || narrowScreen.matches || player?.open || qrDialog?.open) return;
    hoveredQrButton = button;
    const source = mediaURL(button.dataset.qrImage);
    if (!source) return;
    qrPreview.querySelector('img').src = source;
    qrPreview.querySelector('p').textContent = `${qrTitle(button)} · ${text(button.dataset.qrAccount)}`;
    qrPreview.hidden = false;
    const anchor = button.getBoundingClientRect();
    const popup = qrPreview.getBoundingClientRect();
    const margin = 16;
    const left = Math.max(margin, Math.min(anchor.left + anchor.width / 2 - popup.width / 2, window.innerWidth - popup.width - margin));
    const preferredTop = anchor.top - popup.height - 14;
    const top = Math.max(margin, Math.min(preferredTop >= margin ? preferredTop : anchor.bottom + 14, window.innerHeight - popup.height - margin));
    qrPreview.style.left = `${left}px`;
    qrPreview.style.top = `${top}px`;
  }

  function setLanguage(nextLanguage) {
    language = nextLanguage;
    document.documentElement.lang = language === 'cn' ? 'zh-CN' : 'en';
    document.querySelectorAll('[data-i18n]').forEach((element) => {
      const key = element.dataset.i18n;
      if (Object.prototype.hasOwnProperty.call(copy[language], key)) setLines(element, t(key));
    });
    const languageButton = $('#langSwitch');
    if (languageButton) {
      languageButton.replaceChildren(document.createTextNode(language === 'cn' ? 'EN ' : '中文 '), create('span', '', '↗'));
      languageButton.lastElementChild.setAttribute('aria-hidden', 'true');
      languageButton.setAttribute('aria-label', language === 'cn' ? 'Switch to English' : '切换到中文');
      languageButton.setAttribute('aria-pressed', String(language === 'en'));
    }
    if (search) { search.placeholder = t('searchPlaceholder'); search.setAttribute('aria-label', t('searchLabel')); }
    filters?.setAttribute('aria-label', t('filterLabel'));
    heroControls?.setAttribute('aria-label', t('featureLabel'));
    $('#workPlayerClose')?.setAttribute('aria-label', t('closeVideo'));
    $('#socialQrClose')?.setAttribute('aria-label', t('closeQR'));
    document.querySelector('.main-nav')?.setAttribute('aria-label', language === 'cn' ? '主导航' : 'Main navigation');
    document.querySelector('.brand')?.setAttribute('aria-label', language === 'cn' ? 'Highstrith 首页' : 'Highstrith home');
    document.querySelector('.hero-foot a')?.setAttribute('aria-label', language === 'cn' ? '向下浏览作品' : 'Browse the works below');
    document.querySelector('.hero-avatar')?.setAttribute('alt', language === 'cn' ? '橘小桔的数字人形象' : 'The digital persona of Highstrith');
    document.title = language === 'cn' ? 'Highstrith · 橘小桔 — 影像与想象' : 'Highstrith · Film & imagination';
    updateCardText();
    renderHeroControls();
    updateHero();
    applyFilters();
    updatePlayerText();
    updateQrDialog();
    if (hoveredQrButton) showQrPreview(hoveredQrButton);
    updateMusicUI();
  }

  $('#adminEntryLink')?.toggleAttribute('hidden', !isLoopback && !isFile);
  $('#copyrightYear')?.replaceChildren(document.createTextNode(String(new Date().getFullYear())));
  filters?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-filter]');
    if (!button || !filters.contains(button)) return;
    currentFilter = button.dataset.filter;
    applyFilters();
  });
  search?.addEventListener('input', applyFilters);
  $('#resetFilters')?.addEventListener('click', () => {
    currentFilter = 'all';
    if (search) search.value = '';
    applyFilters();
    search?.focus({ preventScroll: true });
  });
  $('#langSwitch')?.addEventListener('click', () => setLanguage(language === 'cn' ? 'en' : 'cn'));
  document.querySelectorAll('[data-hero-play]').forEach((button) => button.addEventListener('click', () => {
    const work = featuredWorks.find((item) => item.id === selectedFeatureId);
    if (work) openPlayer(work, button);
  }));
  $('#workPlayerClose')?.addEventListener('click', closePlayer);
  player?.addEventListener('cancel', (event) => { event.preventDefault(); closePlayer(); });
  player?.addEventListener('close', finishPlayer);
  playerAction?.addEventListener('click', () => {
    if (playerState === 'restricted' && playerController) {
      showPlayerState('loading');
      schedulePlayerWait(playerController);
      attemptPlayerPlay(playerController);
    } else loadPlayerSource();
  });
  musicButton?.addEventListener('click', () => { musicWanted = !musicWanted; syncMusic(); });
  if (music) { music.volume = 0.16; music.pause(); }

  document.querySelectorAll('[data-qr-image]').forEach((button) => {
    button.addEventListener('click', () => openQr(button));
    button.addEventListener('pointerenter', (event) => { if (event.pointerType === 'mouse') showQrPreview(button); });
    button.addEventListener('pointerleave', hideQrPreview);
  });
  $('#socialQrClose')?.addEventListener('click', () => qrDialog?.close());
  qrDialog?.addEventListener('close', () => {
    if (qrDialog.open) return;
    const target = qrReturnFocus;
    activeQrButton = null;
    qrReturnFocus = null;
    updateScrollLock();
    if (target?.isConnected) target.focus({ preventScroll: true });
    syncPreview();
    syncMusic();
  });
  [player, qrDialog].forEach((dialog) => dialog?.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom) return;
    if (dialog === player) closePlayer();
    else dialog.close();
  }));

  [reducedMotion, finePointer, narrowScreen].forEach((query) => query.addEventListener('change', () => {
    hideQrPreview();
    syncPreview();
  }));
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      hideQrPreview();
      clearPlayerTimer();
      if (player?.open) playerVideo.pause();
    }
    syncPreview();
    syncMusic();
  });
  window.addEventListener('blur', hideQrPreview);
  window.addEventListener('resize', hideQrPreview, { passive: true });
  let scrollFrame = 0;
  window.addEventListener('scroll', () => {
    if (scrollFrame) return;
    scrollFrame = window.requestAnimationFrame(() => {
      scrollFrame = 0;
      hideQrPreview();
      if (!('IntersectionObserver' in window)) heroNearViewport = nearViewport(hero);
      syncPreview();
    });
  }, { passive: true });
  if (hero && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(([entry]) => {
      heroNearViewport = entry.isIntersecting;
      syncPreview();
    }, { rootMargin: '100px 0px' });
    observer.observe(hero);
  }

  setLanguage('cn');
  loadCatalogue();
})();
