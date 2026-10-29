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
      navStills: '画面截图', stillsLabel: '画面定格', stillsTitle: '作品截图',
      stillsIntro: '过往创作留下的画面，\n记录不同阶段的光线与情绪。',
      galleryView: '画廊', listView: '目录', previewNote: '静音片段预览', pausePreview: '暂停预览', resumePreview: '继续预览',
      toolsLabel: '创作之外，也造工具', toolsTitle: '让想法，顺手发生', toolsIntro: '从 AI 画布到日常计算，把自己的需要做成可以使用的应用。', toolsExplore: '查看项目与应用', toolFeatured: 'AI 无限画布',
      viewImage: '查看大图', zoomImage: '放大查看', fitImage: '适应画面', previousImage: '上一张', nextImage: '下一张', closeImage: '关闭图片浏览',
      imageLoading: '正在加载图片…', imageError: '图片暂时无法加载，请切换其他图片后重试。', copyEmail: '复制邮箱', emailCopied: '邮箱已复制', emailCopyFailed: '请手动复制：highstrith@gmail.com',
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
      navStills: 'Stills', stillsLabel: 'Frozen frames', stillsTitle: 'Stills',
      stillsIntro: 'Frames left behind by past works,\ncapturing light and mood at different stages.',
      galleryView: 'Gallery', listView: 'Directory', previewNote: 'Silent film excerpts', pausePreview: 'Pause preview', resumePreview: 'Resume preview',
      toolsLabel: 'Making tools, too', toolsTitle: 'Room for your ideas', toolsIntro: 'From an AI canvas to everyday calculations, small apps built around real needs.', toolsExplore: 'Explore projects & apps', toolFeatured: 'AI infinite canvas',
      viewImage: 'View full image', zoomImage: 'Zoom in', fitImage: 'Fit to screen', previousImage: 'Previous', nextImage: 'Next', closeImage: 'Close image viewer',
      imageLoading: 'Loading image…', imageError: 'This image could not be loaded. Switch to another image and try again.', copyEmail: 'Copy email', emailCopied: 'Email copied', emailCopyFailed: 'Copy this address: highstrith@gmail.com',
    },
  };

  // 画面定格（作品截图）数据。替换图片时，把 image 换成新文件路径即可；
  // 如需增减条目，直接在此数组增删对象，页面会自动重排。
  const stillFrames = [
    { image: 'assets/stills/nezha-boy.jpg', thumbnail: 'assets/stills/nezha-boy-preview.webp', cnTitle: '月下少年', enTitle: 'Boy Under the Moon', cnDesc: '国风角色三维渲染：月夜水面，少年执枪而立。', enDesc: 'A stylized 3D character render: a boy with his spear on the water under the moon.' },
    { image: 'assets/stills/jade-blades.jpg', thumbnail: 'assets/stills/jade-blades-preview.webp', cnTitle: '翡翠之刃', enTitle: 'Jade Blades', cnDesc: '玉石质感与玫瑰金相结合的奇幻武器设计。', enDesc: 'Fantasy weapon design pairing jade-like blades with rose-gold fittings.' },
    { image: 'assets/stills/frost-rune-sword.jpg', thumbnail: 'assets/stills/frost-rune-sword-preview.webp', cnTitle: '寒渊符文剑', enTitle: 'Frost Rune Sword', cnDesc: '冰晶符文巨剑的三视图渲染展示。', enDesc: 'A rune-etched greatsword presented in a three-view render.' },
    { image: 'assets/stills/wasteland-dagger.jpg', thumbnail: 'assets/stills/wasteland-dagger-preview.webp', cnTitle: '废土之刃', enTitle: 'Wasteland Dagger', cnDesc: '扳手改造匕首的写实 PBR 材质练习。', enDesc: 'A realistic PBR study of a wrench-repurposed dagger.' },
    { image: 'assets/uploads/posters/reset-day-20261007-16x9.png', cnTitle: '重置日 · 归零之后', enTitle: 'Reset Day · After the reset', cnDesc: '画面里的一束光，落在重新开始的那一刻。', enDesc: 'A beam of light landing on the moment everything starts over.' },
    { image: 'assets/uploads/posters/lying-down-20261001-16x9.png', cnTitle: '趴着办公早该知道 · 床式工位', enTitle: 'Should Have Worked Lying Down · Bed desk', cnDesc: '一本正经的喜剧，藏在最日常的构图里。', enDesc: 'A straight-faced comedy hidden in an everyday composition.' },
    { image: 'assets/posters/creative-3.jpg', cnTitle: '动作预演 · 一个转身', enTitle: 'Action Study · A turn', cnDesc: '角色动作与镜头节奏的一次练习。', enDesc: 'A study of character movement and camera rhythm.' },
    { image: 'assets/posters/render-test.jpg', cnTitle: '能量实验 · 火焰材质', enTitle: 'Energy Study · Flame material', cnDesc: '火焰与能量材质的动态渲染实验。', enDesc: 'A motion render study of flame and energy materials.' },
  ];

  function renderStills() {
    if (!stillsGrid) return;
    stillsGrid.replaceChildren(...stillFrames.map((frame, index) => {
      const title = language === 'cn' ? frame.cnTitle : frame.enTitle;
      const desc = language === 'cn' ? frame.cnDesc : frame.enDesc;
      const figure = create('figure', 'still-card');
      figure.setAttribute('data-reveal', '');
      const button = create('button', 'still-media');
      button.type = 'button';
      button.dataset.still = String(index);
      button.setAttribute('aria-label', `${t('viewImage')}: ${title}`);
      button.setAttribute('aria-haspopup', 'dialog');
      const image = create('img');
      image.loading = 'lazy';
      image.decoding = 'async';
      setPosterImage(image, frame.thumbnail || frame.image, 'card');
      image.alt = title;
      image.width = index === 0 ? 270 : 480;
      image.height = index === 0 ? 480 : 300;
      button.append(image, create('span', 'still-open-hint', t('viewImage')));
      button.addEventListener('click', () => openStill(index, button));
      const caption = create('figcaption');
      caption.append(create('h3', '', title), create('p', '', desc));
      figure.append(button, caption);
      return figure;
    }));
    window.StudioReveal?.refresh(stillsGrid);
  }
  const grid = $('#worksGrid');
  const stillsGrid = $('#stillsGrid');
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
  const stillViewer = $('#stillViewer');
  const stillImage = $('#stillViewerImage');
  const stillStage = $('#stillViewerStage');

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
  let featurePaused = false;
  let selectedStill = 0;
  let stillReturnFocus = null;
  let noticeTimer = 0;

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
    cardRecords = works.map((work, index) => {
      const item = create('div', 'work-item');
      item.setAttribute('data-reveal', '');
      item.style.setProperty('--i', String(index % 2));
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
    updateActiveNavigation();
    updateCardText();
    const total = $('.filter-total');
    if (total) total.textContent = String(works.length);
    window.StudioReveal?.refresh(grid);
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
      if (visible) record.item.dataset.gallerySlot = String(count % 4);
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
      const details = create('span', 'pick-copy');
      details.append(create('span', 'pick-title', workTitle(work)), create('span', 'pick-category', workText(work, 'Sub')));
      button.append(image, create('span', 'pick-number', String(index + 1).padStart(2, '0')), details);
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
    if ($('#featureDescription')) $('#featureDescription').textContent = workText(work, 'Desc');
    if ($('#featurePosition')) $('#featurePosition').textContent = `${String(featuredWorks.indexOf(work) + 1).padStart(2, '0')} / ${String(featuredWorks.length).padStart(2, '0')}`;
    document.querySelectorAll('[data-hero-play]').forEach((button) => button.setAttribute('aria-label', `${t('watch')}: ${name}`));
    heroControls?.querySelectorAll('[data-feature]').forEach((button) => {
      const active = button.dataset.feature === selectedFeatureId;
      button.setAttribute('aria-pressed', String(active));
      button.classList.toggle('is-active', active);
      if (!active) button.style.setProperty('--preview-progress', '0');
    });
    syncPreview();
  }

  function previewAllowed() {
    return !reducedMotion.matches && !document.hidden && !player?.open && !qrDialog?.open && !stillViewer?.open;
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
        const progress = Math.max(0, Math.min(1, (video.currentTime - segmentStart) / Math.min(featurePreviewSeconds, video.duration - segmentStart || featurePreviewSeconds)));
        heroControls?.querySelector('[aria-pressed="true"]')?.style.setProperty('--preview-progress', String(progress));
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
    if (work && !featurePaused && heroNearViewport && nearViewport(heroVideo)) startPreview(work, heroVideo, hero);
    else stopPreview();
  }

  function updateScrollLock() {
    document.body.classList.toggle('modal-open', Boolean(player?.open || qrDialog?.open || stillViewer?.open));
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
    if (!musicWanted || document.hidden || player?.open || qrDialog?.open || stillViewer?.open) {
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
    document.querySelectorAll('[data-projects-link]').forEach(link => link.setAttribute('href', language === 'en' ? 'projects.html?lang=en' : 'projects.html'));
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
    renderStills();
    updateCardText();
    renderHeroControls();
    updateHero();
    applyFilters();
    updatePlayerText();
    updateQrDialog();
    if (hoveredQrButton) showQrPreview(hoveredQrButton);
    updateMusicUI();
    updateExhibitionText();
    window.StudioReveal?.relang(document);
  }

  function updateExhibitionText() {
    $('#viewSwitch')?.setAttribute('aria-label', language === 'cn' ? '作品视图' : 'Work views');
    document.querySelector('[data-view="gallery"]')?.setAttribute('aria-label', language === 'cn' ? '画廊视图' : 'Gallery view');
    document.querySelector('[data-view="list"]')?.setAttribute('aria-label', language === 'cn' ? '目录视图' : 'Directory view');
    $('#featurePreviewLabel').textContent = t(featurePaused ? 'resumePreview' : 'pausePreview');
    $('#featurePreviewToggle').setAttribute('aria-label', t(featurePaused ? 'resumePreview' : 'pausePreview'));
    $('#stillViewerClose').setAttribute('aria-label', t('closeImage'));
    $('[data-tool-image]')?.setAttribute('alt', language === 'cn' ? 'AI 无限画布界面' : 'AI infinite canvas interface');
    if (stillViewer?.open) updateStillText();
  }

  function updateStillText() {
    const frame = stillFrames[selectedStill];
    const title = language === 'cn' ? frame.cnTitle : frame.enTitle;
    $('#stillViewerTitle').textContent = title;
    $('#stillViewerDescription').textContent = language === 'cn' ? frame.cnDesc : frame.enDesc;
    $('#stillViewerPosition').textContent = `${String(selectedStill + 1).padStart(2, '0')} / ${String(stillFrames.length).padStart(2, '0')}`;
    stillImage.alt = title;
    const zoomed = stillStage.classList.contains('is-zoomed');
    $('#stillZoom').setAttribute('aria-label', t(zoomed ? 'fitImage' : 'zoomImage'));
    $('#stillZoom span').textContent = t(zoomed ? 'fitImage' : 'zoomImage');
  }

  function resetStillZoom() {
    stillStage.classList.remove('is-zoomed');
    stillStage.scrollTop = stillStage.scrollLeft = 0;
    $('#stillZoom').setAttribute('aria-pressed', 'false');
  }

  function showStill(index) {
    selectedStill = (index + stillFrames.length) % stillFrames.length;
    resetStillZoom();
    updateStillText();
    const status = $('#stillViewerStatus');
    status.hidden = false;
    status.textContent = t('imageLoading');
    stillImage.hidden = true;
    // Disabling the focused zoom button would drop focus outside this dialog
    // while the next image loads, losing subsequent arrow-key navigation.
    if (document.activeElement === $('#stillZoom')) $('#stillViewerClose').focus({ preventScroll: true });
    $('#stillZoom').disabled = true;
    stillImage.onload = () => {
      status.hidden = true;
      stillImage.hidden = false;
      $('#stillZoom').disabled = false;
    };
    stillImage.onerror = () => { status.textContent = t('imageError'); };
    stillImage.src = mediaURL(stillFrames[selectedStill].image);
  }

  function openStill(index, trigger) {
    stillReturnFocus = trigger;
    stopPreview();
    hideQrPreview();
    showStill(index);
    stillViewer.showModal();
    updateScrollLock();
    syncMusic();
    $('#stillViewerClose').focus({ preventScroll: true });
  }

  function toggleStillZoom() {
    if ($('#stillZoom').disabled) return;
    const zoomed = stillStage.classList.toggle('is-zoomed');
    $('#stillZoom').setAttribute('aria-pressed', String(zoomed));
    if (!zoomed) stillStage.scrollTop = stillStage.scrollLeft = 0;
    updateStillText();
  }

  $('#stillZoom')?.addEventListener('click', toggleStillZoom);
  let suppressStillClickUntil = 0;
  stillImage?.addEventListener('click', () => {
    if (performance.now() >= suppressStillClickUntil) toggleStillZoom();
  });
  $('#stillPrevious')?.addEventListener('click', () => showStill(selectedStill - 1));
  $('#stillNext')?.addEventListener('click', () => showStill(selectedStill + 1));
  $('#stillViewerClose')?.addEventListener('click', () => stillViewer.close());
  stillViewer?.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    showStill(selectedStill + (event.key === 'ArrowLeft' ? -1 : 1));
  });
  let stillSwipe = null;
  stillStage?.addEventListener('pointerdown', event => {
    if (event.pointerType !== 'touch' || stillStage.classList.contains('is-zoomed')) return;
    stillSwipe = { x: event.clientX, y: event.clientY, id: event.pointerId };
  });
  stillStage?.addEventListener('pointerup', event => {
    const start = stillSwipe;
    stillSwipe = null;
    if (!start || start.id !== event.pointerId) return;
    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      suppressStillClickUntil = performance.now() + 400;
      showStill(selectedStill + (dx < 0 ? 1 : -1));
    }
  });
  stillStage?.addEventListener('pointercancel', () => { stillSwipe = null; });
  stillViewer?.addEventListener('close', () => {
    if (stillViewer.open) return;
    stillImage.onload = stillImage.onerror = null;
    stillImage.removeAttribute('src');
    resetStillZoom();
    updateScrollLock();
    const target = stillReturnFocus;
    stillReturnFocus = null;
    if (target?.isConnected) target.focus({ preventScroll: true });
    syncPreview();
    syncMusic();
  });
  stillViewer?.addEventListener('click', event => {
    if (event.target !== stillViewer) return;
    const rect = stillViewer.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) stillViewer.close();
  });
  $('#featurePreviewToggle')?.addEventListener('click', () => {
    featurePaused = !featurePaused;
    $('#featurePreviewToggle').setAttribute('aria-pressed', String(featurePaused));
    updateExhibitionText();
    syncPreview();
  });
  $('#viewSwitch')?.addEventListener('click', event => {
    const button = event.target.closest('[data-view]');
    if (!button) return;
    const list = button.dataset.view === 'list';
    grid.classList.toggle('is-list', list);
    document.querySelectorAll('[data-view]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    window.StudioReveal?.refresh(grid);
    syncPreview();
  });
  $('#copyEmail')?.addEventListener('click', async () => {
    let message;
    try {
      await navigator.clipboard.writeText('highstrith@gmail.com');
      message = t('emailCopied');
    } catch { message = t('emailCopyFailed'); }
    const notice = $('#siteNotice');
    notice.textContent = message;
    notice.classList.add('is-visible');
    window.clearTimeout(noticeTimer);
    noticeTimer = window.setTimeout(() => { notice.classList.remove('is-visible'); }, 4500);
  });

  $('#adminEntryLink')?.toggleAttribute('hidden', !isLoopback && !isFile);
  $('#copyrightYear')?.replaceChildren(document.createTextNode(String(new Date().getFullYear())));
  renderStills();
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
      const rect = screen.getBoundingClientRect();
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
      const rect = screen.getBoundingClientRect();
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
      updateActiveNavigation();
    });
  }, { passive: true });
  if (hero && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(([entry]) => {
      heroNearViewport = entry.isIntersecting;
      syncPreview();
    });
    observer.observe(hero);
  }

  // A work catalogue can be much taller than the viewport; an intersection
  // ratio threshold would never activate it. Track section starts instead.
  const navSectionLinks = [...document.querySelectorAll('.main-nav a[href^="#"]')];
  const navSections = navSectionLinks.map(link => ({ link, section: document.getElementById(link.hash.slice(1)) })).filter(item => item.section);
  function updateActiveNavigation() {
    const marker = ($('.site-header')?.getBoundingClientRect().bottom || 0) + window.innerHeight * .2;
    const current = navSections.filter(({ section }) => section.getBoundingClientRect().top <= marker).at(-1)?.link;
    navSectionLinks.forEach(link => {
      if (link === current) link.setAttribute('aria-current', 'true');
      else link.removeAttribute('aria-current');
    });
  }
  window.addEventListener('resize', updateActiveNavigation, { passive: true });

  setLanguage(new URLSearchParams(window.location.search).get('lang') === 'en' ? 'en' : 'cn');
  loadCatalogue();
})();
