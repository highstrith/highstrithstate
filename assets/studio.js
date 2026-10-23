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
      skip: '跳转到作品', navWorks: '作品', navProjects: '项目与应用', navResume: '创作者档案', navAbout: '关于', navContact: '联系', admin: '作品管理',
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
      aboutResume: '创作者档案与简历',
      contactLabel: '从一句「我有个想法」开始', location: '中国 · 南京', contactTitle: '下一个画面，\n一起完成',
      wechatAccount: '微信 Gw1sgdsj_787', elsewhere: '也可以在这里找到我',
      wechat: '微信', douyin: '抖音', red: '小红书', bili: '哔哩哔哩',
      scanShort: '扫码查看', openShort: '打开主页',
      sound: '背景音乐', backTop: '回到顶部', playerHint: 'Esc 关闭', qrHint: '打开对应 App 扫码，和我打个招呼',
      searchPlaceholder: '寻找一部作品', searchLabel: '搜索作品', filterLabel: '作品分类', featureLabel: '选择精选作品',
      closeVideo: '关闭视频', closeQR: '关闭二维码', play: '播放', retry: '重试播放',
      loading: '正在加载作品…', buffering: '正在缓冲…', restricted: '点击播放，开始观看这部作品。',
      error: '暂时无法加载这部作品，请重试。', slow: '加载比平时慢，可以继续等待或重试。',
      musicOn: '开', musicOff: '关', playMusic: '播放背景音乐', pauseMusic: '暂停背景音乐',
      comment: '评论', commentClose: '收起评论', commentCount: '条评论',
      commentFailed: '评论暂时加载不出来，请稍后再试。',
      softwareTools: '熟练使用的软件', madeWith: '制作软件',
    },
    en: {
      skip: 'Skip to works', navWorks: 'Works', navProjects: 'Projects', navResume: 'Resume', navAbout: 'About', navContact: 'Contact', admin: 'Manage works',
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
      aboutResume: 'Profile & Resume',
      contactLabel: 'It starts with “I have an idea”', location: 'Nanjing · China', contactTitle: 'Let’s make\nthe next image',
      wechatAccount: 'WeChat Gw1sgdsj_787', elsewhere: 'Find me elsewhere',
      wechat: 'WeChat', douyin: 'Douyin', red: 'Xiaohongshu', bili: 'Bilibili',
      scanShort: 'Scan the code', openShort: 'Open profile',
      sound: 'Background music', backTop: 'Back to top', playerHint: 'Esc to close', qrHint: 'Scan in the matching app and say hello',
      searchPlaceholder: 'Find a work', searchLabel: 'Search works', filterLabel: 'Filter works', featureLabel: 'Choose a featured work',
      closeVideo: 'Close video', closeQR: 'Close QR code', play: 'Play', retry: 'Try again',
      loading: 'Loading the film…', buffering: 'Buffering…', restricted: 'Press play to watch this film.',
      error: 'This film could not be loaded. Please try again.', slow: 'Loading is taking longer than usual. Keep waiting or try again.',
      musicOn: 'On', musicOff: 'Off', playMusic: 'Play background music', pauseMusic: 'Pause background music',
      comment: 'Comments', commentClose: 'Hide comments', commentCount: 'comments',
      commentFailed: 'Comments could not be loaded right now. Please try again later.',
      softwareTools: 'Tools I work with', madeWith: 'Made with',
    },
  };

  const grid = $('#worksGrid');
  const filters = $('#workFilters');
  const search = $('#workSearch');
  const hero = $('.hero-feature');
  const heroVideo = $('#heroPreview');
  const heroPoster = $('#heroPoster');
  let heroFreeze = null;
  let heroFreezeTimer = 0;
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
  const featurePreviewSeconds = 10;
  const featureVisits = new Map();
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

  // 评论由腾讯云开发上的 Twikoo 提供。envId 留空时整段逻辑不启用，
  // 页面不会多渲染任何节点，也不会向外部请求任何脚本。
  const commentConfig = window.STUDIO_COMMENT_CONFIG || {};
  const commentText = (value) => (typeof value === 'string' ? value.trim() : '');
  const commentEnvId = commentText(commentConfig.envId);
    const commentsEnabled = commentEnvId !== '';
  const commentRegion = commentText(commentConfig.region) || undefined;
  const commentFuncName = commentText(commentConfig.funcName) || undefined;
  const commentVersion = commentText(commentConfig.version) || 'latest';
  const commentSource = `https://cdn.jsdelivr.net/npm/twikoo@${commentVersion}/dist/twikoo.all.min.js`;
  let commentCounts = null;
  let openCommentCard = null;
  let widgetLoading = null;
  let widgetUnreachable = false;

  const t = (key) => copy[language][key] || '';
  const text = (value) => typeof value === 'string' ? value : '';
  const workText = (work, field) => text(work[(language === 'cn' ? 'cn' : 'en') + field]) || text(work['cn' + field]) || text(work['en' + field]);
  const workTitle = (work) => workText(work, 'Title');
  const softwareNames = new Map([...document.querySelectorAll('.footer-software [data-software]')]
    .map(element => [element.dataset.software, { cn: element.dataset.cn, en: element.dataset.en }]));
  const workSoftware = (work) => [...new Set(Array.isArray(work?.software) ? work.software.filter(id => softwareNames.has(id)) : [])];
  const create = (tag, className, content) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (content !== undefined) element.textContent = content;
    return element;
  };

  // Catalogue text is never interpreted as markup; public media stays inside assets/.
  function renderSoftware(work, element) {
    if (!element) return;
    const ids = workSoftware(work);
    element.hidden = !ids.length;
    const tags = create('span', 'software-tags');
    tags.append(...ids.map(id => create('span', 'software-tag', softwareNames.get(id)[language])));
    element.replaceChildren(create('span', 'work-software-label', t('madeWith')), tags);
  }

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

  function imageVariants(source) {
    const key = text(source).trim().replace(/^\.\//, '');
    const variants = typeof posterImageData !== 'undefined' ? posterImageData[key] : null;
    return Array.isArray(variants) ? variants.filter((variant) =>
      mediaURL(variant.src) && Number.isInteger(variant.width) && variant.width > 0 &&
      Number.isInteger(variant.height) && variant.height > 0
    ) : [];
  }

  function posterSource(source, thumbnail = false) {
    const variants = imageVariants(source);
    const variant = thumbnail ? variants[0] : variants.find((item) => item.width >= 960) || variants.at(-1);
    return mediaURL(variant?.src || source);
  }

  function setPosterImage(image, source, role) {
    const variants = imageVariants(source);
    if (variants.length && role !== 'thumbnail') {
      image.sizes = role === 'hero'
        ? '(max-width: 600px) calc(100vw - 40px), (max-width: 1100px) calc(100vw - 64px), (max-width: 1696px) calc(100vw - 96px), 1600px'
        : '(max-width: 600px) calc(100vw - 40px), (max-width: 1100px) calc((100vw - 96px) / 2), (max-width: 1696px) calc((100vw - 128px) / 2), 784px';
      image.srcset = variants.map((item) => `${mediaURL(item.src)} ${item.width}w`).join(', ');
    } else {
      image.removeAttribute('srcset');
      image.removeAttribute('sizes');
    }
    const variant = variants.at(-1);
    if (variant) {
      image.width = variant.width;
      image.height = variant.height;
    } else {
      image.removeAttribute('width');
      image.removeAttribute('height');
    }
    const poster = posterSource(source, role === 'thumbnail');
    if (poster) image.src = poster;
    else image.removeAttribute('src');
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
      'added-title-render': 'featured-timeline-1',
    };
    const candidates = works.map((work) => works.find((item) => item.id === featureReplacements[work.id]) || work);
    featuredWorks = [...new Map(candidates.map((work) => [work.id, work])).values()].slice(0, 5);
    if (!featuredWorks.some((work) => work.id === selectedFeatureId)) selectedFeatureId = featuredWorks[0]?.id || '';
    renderCards();
    renderHeroControls();
    updateHero();
    applyFilters();
    if (commentsEnabled) prefetchCommentCounts();
  }

  function renderCards() {
    stopPreview();
    closeComments();
    hoveredCard = null;
    focusedCard = null;
    cardRecords = works.map((work) => {
      const item = create('div', 'work-item');
      const card = create('button', 'work-card');
      card.type = 'button';
      card.dataset.workId = work.id;
      const media = create('span', 'work-media');
      const image = create('img');
      image.loading = 'lazy';
      image.decoding = 'async';
      setPosterImage(image, work.poster, 'card');
      const video = create('video');
      video.muted = true;
      video.defaultMuted = true;
      video.loop = true;
      video.playsInline = true;
      video.preload = 'none';
      video.setAttribute('muted', '');
      video.setAttribute('playsinline', '');
      video.setAttribute('aria-hidden', 'true');
      media.append(image, video);
      const caption = create('span', 'work-caption');
      const category = create('span', 'work-category');
      const title = create('span', 'work-title');
      const description = create('span', 'work-description');
      caption.append(category, title, description);
      const software = workSoftware(work).length ? create('span', 'work-software') : null;
      if (software) caption.append(software);
      card.append(media, caption);
      const record = { work, item, card, media, image, video, category, title, description, software, categories: categories(work) };
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
      item.append(card);
      if (commentsEnabled) attachCommentEntry(record);
      return record;
    });
    grid?.replaceChildren(...cardRecords.map(({ item }) => item));
    updateCardText();
    const total = $('.filter-total');
    if (total) total.textContent = String(works.length);
  }

  function updateCardText() {
    cardRecords.forEach(({ work, card, image, category, title, description, software }) => {
      const name = workTitle(work);
      title.textContent = name;
      category.textContent = workText(work, 'Sub');
      description.textContent = workText(work, 'Desc');
      renderSoftware(work, software);
      image.alt = language === 'cn' ? `${name}作品画面` : `Still from ${name}`;
      card.setAttribute('aria-label', `${t('watch')}: ${name}`);
    });
    if (commentsEnabled) cardRecords.forEach(updateCommentEntry);
  }

  function applyFilters() {
    const query = (search?.value || '').trim().normalize('NFKC').toLocaleLowerCase();
    let count = 0;
    cardRecords.forEach((record) => {
      const visible = (currentFilter === 'all' || record.categories.has(currentFilter)) && (!query || record.query.includes(query));
      record.item.hidden = !visible;
      if (!visible && openCommentCard === record) closeComments();
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

  // 每部作品只保留一个评论线程。Twikoo 会把内容挂到 id 为 twikoo 的容器上，
  // 因此展开哪一部就把这个 id 交给哪一部，收起时归还，避免出现多个活动线程。
  const commentThread = (work) => `/works/${encodeURIComponent(text(work.id))}`;

  function commentRequest(urls) {
    return {
      envId: commentEnvId,
      urls,
      ...(commentRegion ? { region: commentRegion } : {}),
      ...(commentFuncName ? { funcName: commentFuncName } : {}),
    };
  }

  function attachCommentEntry(record) {
    const toggle = create('button', 'comment-toggle');
    toggle.type = 'button';
    toggle.setAttribute('aria-expanded', 'false');
    const label = create('span', 'comment-toggle-label');
    const count = create('span', 'comment-toggle-count');
    count.hidden = true;
    const panel = create('div', 'comment-panel work-comments');
    panel.hidden = true;
    toggle.append(label, count);
    toggle.addEventListener('click', () => {
      if (openCommentCard === record) closeComments();
      else openComments(record);
    });
    record.item.append(toggle, panel);
    Object.assign(record, { toggle, toggleLabel: label, toggleCount: count, panel });
  }

  function updateCommentEntry(record) {
    const { toggle, toggleLabel, toggleCount, panel, work } = record;
    if (!toggle) return;
    const open = openCommentCard === record;
    const label = open ? t('commentClose') : t('comment');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', `${label} — ${workTitle(work)}`);
    toggleLabel.textContent = label;
    const total = commentCounts?.get(commentThread(work)) ?? null;
    toggleCount.textContent = typeof total === 'number' && total > 0 ? String(total) : '';
    toggleCount.hidden = toggleCount.textContent === '';
    toggleCount.title = typeof total === 'number' && total > 0 ? `${total} ${t('commentCount')}` : '';
    panel?.classList.toggle('is-open', open);
  }

  function openComments(record) {
    if (widgetUnreachable) return;
    closeComments();
    openCommentCard = record;
    record.panel.hidden = false;
    record.panel.id = 'twikoo';
    updateCommentEntry(record);
    loadCommentWidget()
      .then((widget) => widget.init({ ...commentRequest([commentThread(record.work)]), el: '#twikoo' }))
      .catch(() => showCommentError(record));
  }

  function closeComments() {
    const record = openCommentCard;
    if (!record) return;
    openCommentCard = null;
    record.panel.hidden = true;
    record.panel.removeAttribute('id');
    record.panel.replaceChildren();
    updateCommentEntry(record);
  }

  function showCommentError(record) {
    record.panel.replaceChildren(create('p', 'comment-error', t('commentFailed')));
  }

  function loadCommentWidget() {
    if (typeof window.twikoo?.init === 'function') return Promise.resolve(window.twikoo);
    if (widgetLoading) return widgetLoading;
    widgetLoading = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = commentSource;
      script.async = true;
      script.addEventListener('load', () => {
        if (typeof window.twikoo?.init === 'function') resolve(window.twikoo);
        else reject(new Error('comment widget unavailable'));
      });
      script.addEventListener('error', () => reject(new Error('comment widget unreachable')));
      document.head.append(script);
    }).catch((error) => {
      widgetLoading = null;
      throw error;
    });
    return widgetLoading;
  }

  // 计数在浏览器空闲时一次性取回全部作品，避免首屏多发请求；
  // 服务不可达时静默收起入口，作品目录与播放保持可用。
  function prefetchCommentCounts() {
    const urls = works.map(commentThread);
    if (!urls.length) return;
    const request = () => loadCommentWidget()
      .then((widget) => widget.getCommentsCount(commentRequest(urls)))
      .then((rows) => {
        if (!Array.isArray(rows)) throw new Error('unexpected comment count payload');
        commentCounts = new Map(rows.map((row) => [row.url, Number(row.count) || 0]));
        cardRecords.forEach(updateCommentEntry);
      })
      .catch(() => {
        widgetUnreachable = true;
        closeComments();
        cardRecords.forEach((record) => {
          record.toggle?.remove();
          if (record.panel) record.panel.hidden = true;
        });
      });
    if (typeof window.requestIdleCallback === 'function') window.requestIdleCallback(request, { timeout: 4000 });
    else window.setTimeout(request, 1200);
  }

  function renderHeroControls() {
    const controls = featuredWorks.map((work, index) => {
      const button = create('button', 'hero-pick');
      button.type = 'button';
      button.dataset.feature = work.id;
      button.setAttribute('aria-label', `${String(index + 1).padStart(2, '0')}: ${workTitle(work)}`);
      button.setAttribute('aria-pressed', String(work.id === selectedFeatureId));
      const image = create('img');
      image.alt = '';
      image.loading = 'lazy';
      image.decoding = 'async';
      setPosterImage(image, work.poster, 'thumbnail');
      button.append(image, create('span', '', String(index + 1).padStart(2, '0')));
      button.addEventListener('click', () => selectFeature(work.id));
      button.addEventListener('pointerenter', (event) => {
        if (event.pointerType === 'mouse') selectFeature(work.id);
      });
      button.addEventListener('focus', () => selectFeature(work.id));
      return button;
    });
    heroControls?.replaceChildren(...controls);
  }

  function selectFeature(id) {
    if (id === selectedFeatureId || !featuredWorks.some(work => work.id === id)) return;
    featureVisits.set(selectedFeatureId, (featureVisits.get(selectedFeatureId) || 0) + 1);
    selectedFeatureId = id;
    updateHero();
  }

  function nextFeature() {
    const index = featuredWorks.findIndex(work => work.id === selectedFeatureId);
    selectFeature(featuredWorks[(index + 1) % featuredWorks.length]?.id);
  }

  function updateHero() {
    const work = featuredWorks.find((item) => item.id === selectedFeatureId);
    if (!work) {
      stopPreview();
      return;
    }
    const name = workTitle(work);
    if (heroPoster) {
      setPosterImage(heroPoster, work.poster, 'hero');
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
    return !reducedMotion.matches && !document.hidden && !player?.open && !qrDialog?.open;
  }

  function nearViewport(element) {
    if (!element || element.hidden) return false;
    const rect = element.getBoundingClientRect();
    return rect.bottom > 0 && rect.top < window.innerHeight && rect.width > 0;
  }

  // A single <video> cannot hold the outgoing frame while the next clip loads, so
  // snapshot the current frame into a canvas and dissolve from it. Without this the
  // element goes blank the moment the source changes and the cut reads as a jump.
  function captureHeroFrame() {
    if (!heroVideo || reducedMotion.matches) return null;
    if (heroVideo.readyState < 2 || !heroVideo.videoWidth || !heroVideo.videoHeight) return null;
    const box = heroVideo.getBoundingClientRect();
    if (!box.width || !box.height) return null;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const canvas = document.createElement('canvas');
    canvas.className = 'hero-freeze';
    canvas.setAttribute('aria-hidden', 'true');
    canvas.width = Math.max(1, Math.round(box.width * ratio));
    canvas.height = Math.max(1, Math.round(box.height * ratio));
    const context = canvas.getContext('2d');
    if (!context) return null;
    // Keep the film's own aspect ratio so the frozen frame lines up with the live one.
    const scale = Math.min(canvas.width / heroVideo.videoWidth, canvas.height / heroVideo.videoHeight);
    const width = heroVideo.videoWidth * scale;
    const height = heroVideo.videoHeight * scale;
    try {
      context.drawImage(heroVideo, (canvas.width - width) / 2, (canvas.height - height) / 2, width, height);
    } catch (error) {
      return null; // Cross-origin media taints the canvas; fall back to an instant swap.
    }
    return canvas;
  }

  function attachHeroFreeze(canvas) {
    if (!canvas || !heroVideo?.isConnected) return;
    clearHeroFreeze();
    heroFreeze = canvas;
    heroVideo.after(canvas);
    // Dissolve straight away: the new still is already behind the canvas, so the
    // outgoing frame gives the swap something to fade from instead of a hard cut.
    window.requestAnimationFrame(() => {
      if (heroFreeze !== canvas) return;
      canvas.classList.add('is-leaving');
      heroFreezeTimer = window.setTimeout(() => {
        heroFreeze = null;
        canvas.remove();
      }, 520);
    });
  }

  function clearHeroFreeze() {
    const canvas = heroFreeze;
    heroFreeze = null;
    window.clearTimeout(heroFreezeTimer);
    heroFreezeTimer = 0;
    if (canvas) canvas.remove();
  }

  function stopPreview() {
    clearHeroFreeze();
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
    const frozenFrame = video === heroVideo ? captureHeroFrame() : null;
    stopPreview();
    if (frozenFrame) attachHeroFreeze(frozenFrame);
    const controller = new AbortController();
    const session = { video, container, source, controller };
    activePreview = session;
    if (video === heroVideo) {
      let segmentStart = 0;
      video.loop = false;
      video.addEventListener('loadedmetadata', () => {
        if (activePreview !== session) return;
        const segments = Math.max(1, Math.floor((video.duration + .05) / featurePreviewSeconds));
        segmentStart = ((featureVisits.get(work.id) || 0) % segments) * featurePreviewSeconds;
        if (segmentStart) video.currentTime = segmentStart;
      }, { signal: controller.signal });
      const advance = () => {
        if (activePreview === session && previewAllowed() && heroNearViewport && nearViewport(video)) nextFeature();
      };
      // Media time stops during buffering, backgrounding and pauses. A wall
      // clock interval would skip films before visitors actually see them.
      video.addEventListener('timeupdate', () => {
        if (activePreview === session && video.currentTime > 0 && !container.classList.contains('is-previewing')) {
          container.classList.add('is-previewing');
        }
        if (!video.paused && !video.seeking && video.currentTime >= segmentStart + featurePreviewSeconds) advance();
      }, { signal: controller.signal });
      video.addEventListener('ended', advance, { signal: controller.signal });
    }
    video.addEventListener('playing', () => {
      if (activePreview !== session) return;
      container.classList.add('is-previewing');
    }, { signal: controller.signal });
    video.addEventListener('error', () => {
      if (activePreview === session) stopPreview();
    }, { signal: controller.signal });
    video.muted = true;
    video.defaultMuted = true;
    video.playsInline = true;
    video.setAttribute('muted', '');
    video.setAttribute('playsinline', '');
    video.src = source;
    video.load();
    const playAttempt = video.play();
    if (playAttempt && typeof playAttempt.catch === 'function') {
      playAttempt.catch(() => {
        if (activePreview !== session) return;
        container.classList.remove('is-previewing');
        if (video === heroVideo) clearHeroFreeze();

        // Autoplay recovery on user interaction if restricted by browser policy
        const resumeOnGesture = () => {
          if (activePreview === session && video.paused) {
            video.play()?.then(() => {
              container.classList.add('is-previewing');
            }).catch(() => {});
          }
        };
        ['pointerdown', 'touchstart', 'scroll', 'keydown'].forEach((evt) => {
          window.addEventListener(evt, resumeOnGesture, { once: true, passive: true });
        });
      });
    }
  }

  function syncPreview() {
    if (!previewAllowed()) { stopPreview(); return; }
    const card = !narrowScreen.matches && finePointer.matches
      ? [hoveredCard, focusedCard].find((record) => record && nearViewport(record.card))
      : null;
    if (card) { startPreview(card.work, card.video, card.card); return; }
    const work = featuredWorks.find((item) => item.id === selectedFeatureId);
    if (work && heroNearViewport && nearViewport(hero)) startPreview(work, heroVideo, hero);
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
    listen('error', () => {
      const fallback = mediaURL(playerWork?.mobileVideo || playerWork?.video);
      if (playerWork && playerSource !== fallback && fallback) {
        playerSource = fallback;
        playerVideo.src = playerSource;
        playerVideo.load();
        attemptPlayerPlay(controller);
        return;
      }
      clearPlayerTimer();
      showPlayerState('error');
    });
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
    renderSoftware(playerWork, $('#playerSoftware'));
    showPlayerState(playerState);
  }

  function openPlayer(work, trigger) {
    if (!player || !playerVideo) return;
    playerWork = work;
    playerReturnFocus = trigger || document.activeElement;
    const mobile = narrowScreen.matches || coarsePointer.matches;
    playerSource = mediaURL(mobile ? (work.mobileVideo || work.video) : (work.webVideo || work.video));
    const poster = posterSource(work.poster);
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
    document.querySelector('[data-projects-link]')?.setAttribute('href', language === 'en' ? 'projects.html?lang=en' : 'projects.html');
    document.querySelectorAll('[data-resume-link]').forEach(el => {
      el.setAttribute('href', language === 'en' ? 'resume.html?lang=en' : 'resume.html');
    });
    document.querySelectorAll('.footer-software [data-software]').forEach(element => {
      element.textContent = softwareNames.get(element.dataset.software)[language];
    });
    document.documentElement.lang = language === 'cn' ? 'zh-CN' : 'en';
    document.querySelectorAll('[data-i18n]').forEach((element) => {
      const key = element.dataset.i18n;
      if (Object.prototype.hasOwnProperty.call(copy[language], key)) setLines(element, t(key));
    });
    const languageButton = $('#langSwitch');
    if (languageButton) {
      languageButton.textContent = language === 'cn' ? 'EN' : '中文';
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

  // The play badge trails the pointer so it never covers the corner of the frame a
  // visitor is looking at, then eases back to the middle once the pointer leaves.
  (function trackHeroPlay() {
    const screen = hero?.querySelector('.feature-screen');
    const badge = hero?.querySelector('[data-hero-play]');
    if (!screen || !badge) return;
    const follow = { x: 0, y: 0, toX: 0, toY: 0, halfW: 0, halfH: 0, frame: 0, active: false };

    function place() {
      badge.style.left = '0px';
      badge.style.top = '0px';
      badge.style.transform = `translate3d(${follow.x - follow.halfW}px, ${follow.y - follow.halfH}px, 0)`;
    }

    function park() {
      hero.classList.remove('is-play-follow');
      badge.style.left = '';
      badge.style.top = '';
      badge.style.transform = '';
    }

    function step() {
      follow.frame = 0;
      const dx = follow.toX - follow.x;
      const dy = follow.toY - follow.y;
      if (Math.abs(dx) < .4 && Math.abs(dy) < .4) {
        follow.x = follow.toX;
        follow.y = follow.toY;
        if (follow.active) place();
        else park();
        return;
      }
      follow.x += dx * .22;
      follow.y += dy * .22;
      place();
      follow.frame = window.requestAnimationFrame(step);
    }

    function aim(x, y) {
      follow.toX = x;
      follow.toY = y;
      if (!follow.frame) follow.frame = window.requestAnimationFrame(step);
    }

    function measure() {
      follow.halfW = badge.offsetWidth / 2;
      follow.halfH = badge.offsetHeight / 2;
    }

    screen.addEventListener('pointermove', (event) => {
      if (event.pointerType !== 'mouse' || reducedMotion.matches) return;
      const rect = hero.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      measure();
      if (!follow.active) {
        // Start from wherever the badge sits so following never jumps.
        const box = badge.getBoundingClientRect();
        follow.x = box.left - rect.left + box.width / 2;
        follow.y = box.top - rect.top + box.height / 2;
        follow.active = true;
        hero.classList.add('is-play-follow');
      }
      const pad = 12;
      aim(
        Math.min(Math.max(event.clientX - rect.left, follow.halfW + pad), rect.width - follow.halfW - pad),
        Math.min(Math.max(event.clientY - rect.top, follow.halfH + pad), rect.height - follow.halfH - pad),
      );
    });

    screen.addEventListener('pointerleave', () => {
      if (!follow.active) return;
      const rect = hero.getBoundingClientRect();
      follow.active = false;
      measure();
      aim(rect.width / 2, rect.height * .45);
    });

    window.addEventListener('resize', () => {
      if (!follow.active) {
        window.cancelAnimationFrame(follow.frame);
        follow.frame = 0;
        park();
      }
    }, { passive: true });
  })();
  $('#workPlayerClose')?.addEventListener('click', closePlayer);
  player?.addEventListener('cancel', (event) => { event.preventDefault(); closePlayer(); });
  player?.addEventListener('close', finishPlayer);
  let playerHudTimer = null;
  function showPlayerHud(icon, text) {
    if (!player) return;
    let hud = $('#playerHud');
    if (!hud) {
      hud = create('div', 'player-hud', '');
      hud.id = 'playerHud';
      player.querySelector('.player-screen')?.appendChild(hud);
    }
    if (!hud) return;
    hud.innerHTML = `<span class="hud-icon">${icon}</span>${text ? `<span class="hud-text">${text}</span>` : ''}`;
    hud.classList.remove('show');
    void hud.offsetWidth;
    hud.classList.add('show');
    clearTimeout(playerHudTimer);
    playerHudTimer = setTimeout(() => {
      hud.classList.remove('show');
    }, 650);
  }

  player?.addEventListener('keydown', (event) => {
    if (event.target && (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA')) return;
    if (event.code === 'Space') {
      event.preventDefault();
      if (!playerVideo) return;
      if (playerVideo.paused) {
        playerVideo.play()?.catch(() => {});
        showPlayerHud('▶', language === 'en' ? 'Play' : '播放');
      } else {
        playerVideo.pause();
        showPlayerHud('❚❚', language === 'en' ? 'Pause' : '暂停');
      }
    } else if (event.code === 'ArrowLeft') {
      event.preventDefault();
      if (playerVideo && Number.isFinite(playerVideo.currentTime)) {
        playerVideo.currentTime = Math.max(0, playerVideo.currentTime - 5);
        showPlayerHud('⏪', '-5s');
      }
    } else if (event.code === 'ArrowRight') {
      event.preventDefault();
      if (playerVideo && Number.isFinite(playerVideo.currentTime)) {
        const duration = Number.isFinite(playerVideo.duration) ? playerVideo.duration : Infinity;
        playerVideo.currentTime = Math.min(duration, playerVideo.currentTime + 5);
        showPlayerHud('⏩', '+5s');
      }
    } else if (event.code === 'KeyM') {
      if (playerVideo) {
        playerVideo.muted = !playerVideo.muted;
        showPlayerHud(playerVideo.muted ? '🔇' : '🔊', playerVideo.muted ? (language === 'en' ? 'Mute' : '静音') : (language === 'en' ? 'Sound' : '原声'));
      }
    } else if (event.code === 'KeyF') {
      if (document.fullscreenElement) {
        document.exitFullscreen?.().catch(() => {});
        showPlayerHud('⛶', language === 'en' ? 'Exit Fullscreen' : '退出全屏');
      } else {
        (playerVideo?.requestFullscreen || playerVideo?.webkitRequestFullscreen)?.call(playerVideo)?.catch(() => {});
        showPlayerHud('⛶', language === 'en' ? 'Fullscreen' : '全屏');
      }
    }
  });
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
    });
    observer.observe(hero);
  }

  // ScrollSpy for main-nav sections (#works, #about, #contact)
  const navSectionLinks = [...document.querySelectorAll('.main-nav a[href^="#"]')];
  if (navSectionLinks.length > 0 && typeof IntersectionObserver === 'function') {
    const sectionObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          navSectionLinks.forEach(link => {
            const isMatch = link.getAttribute('href') === `#${id}`;
            if (isMatch) link.setAttribute('aria-current', 'true');
            else link.removeAttribute('aria-current');
          });
        }
      });
    }, { rootMargin: '-20% 0px -60% 0px', threshold: 0.05 });

    navSectionLinks.forEach(link => {
      const section = document.querySelector(link.getAttribute('href'));
      if (section) sectionObserver.observe(section);
    });
  }

  setLanguage(new URLSearchParams(window.location.search).get('lang') === 'en' ? 'en' : 'cn');
  loadCatalogue();
})();
