(() => {
  'use strict';

  // Works Catalog
  const worksCatalog = {
    'work-ai-patient': {
      id: 'work-ai-patient',
      title: 'AI患者',
      titleEn: 'AI Patient',
      category: 'story',
      categoryName: '科幻 / 叙事短片',
      categoryNameEn: 'Sci-Fi / Narrative Film',
      videoUrl: 'assets/uploads/work-1783863596658-desktop.mp4',
      poster: 'assets/optimized-images/6690d6626117558e-a0066563-480w.webp',
      description: '探讨人与 AI 深度捆绑下的个体异化与自主性重构。独立主导全流程编剧、生图、生视频、三维景深修正、剪辑与达芬奇电影级调色。',
      descriptionEn: 'An exploration of identity alienation and autonomy under deep human-AI synergy. Independently created end-to-end: screenwriting, AI visual generation, 3D depth fix, editing, and DaVinci color grading.'
    },
    'work-reset-day-20261007': {
      id: 'work-reset-day-20261007',
      title: '重置日',
      titleEn: 'Reset Day',
      category: 'story',
      categoryName: '剧情 / AI 短片',
      categoryNameEn: 'Drama / AI Short Film',
      videoUrl: 'assets/optimized/work-reset-day-20261007/1d7ccf6864c1657f-web.mp4',
      poster: 'assets/optimized-images/9f50ee24bfd4004e-a0066563-480w.webp',
      description: 'AI 镜头与三维运镜结合的剧情实验短片，探索多镜头间主体光影与面部的一致性控制。',
      descriptionEn: 'Narrative short combining AI generation and 3D camera staging, focusing on visual consistency across scenes.'
    },
    'work-lying-down-20261001': {
      id: 'work-lying-down-20261001',
      title: '趴着办公早该知道',
      titleEn: 'Office Humor',
      category: 'story',
      categoryName: 'AI 动画 / 喜剧短片',
      categoryNameEn: 'AI Animation / Comedy',
      videoUrl: 'assets/optimized/work-lying-down-20261001/4e6663b8d35374e3-web.mp4',
      poster: 'assets/optimized-images/03ccc84131cda5d1-a0066563-480w.webp',
      description: '趣味职场日常脑洞，结合角色动态模拟与夸张视觉节奏表达。',
      descriptionEn: 'Humorous workplace short combining dynamic character motion and expressive pacing.'
    },
    'added-creative-3': {
      id: 'added-creative-3',
      title: '动作预演',
      titleEn: 'Motion Previs',
      category: 'motion',
      categoryName: '角色 / 动画预演',
      categoryNameEn: 'Character / Animation Previs',
      videoUrl: 'assets/optimized/added-creative-3/defe29806e1f9157-web.mp4',
      poster: 'assets/optimized-images/222086fa98b92ab3-a0066563-480w.webp',
      description: '使用 Cascadeur 动力学与 Blender 辅助角色肢体动画预演，为 AI 视频生成提供严谨的物理骨骼与运镜约束。',
      descriptionEn: 'Character motion previs using Cascadeur physics and Blender, providing physical camera constraints for AI video generation.'
    },
    'visual-study': {
      id: 'visual-study',
      title: '产品视觉实验',
      titleEn: 'Product Visual Study',
      category: 'motion',
      categoryName: '产品 / 三维渲染',
      categoryNameEn: 'Product / 3D Render',
      videoUrl: 'assets/works/visual-study.mp4',
      poster: 'assets/optimized-images/e97c6ff097d826f1-a0066563-480w.webp',
      description: '商业产品三维布光与动态特写渲染，突出材质物理精度与光影质感。',
      descriptionEn: 'Commercial 3D lighting and product render study, emphasizing materials precision and lighting textures.'
    },
    'title-render': {
      id: 'title-render',
      title: '特运尖兵片头',
      titleEn: 'Title Motion Render',
      category: 'motion',
      categoryName: '片头 / 三维视觉',
      categoryNameEn: 'Title / 3D Motion',
      videoUrl: 'assets/works/title-render.mp4',
      poster: 'assets/optimized-images/601cff6a9961ed78-a0066563-480w.webp',
      description: '高张力科幻重金属片头动态包装与光影渲染。',
      descriptionEn: 'High-energy sci-fi metallic title package and lighting motion design.'
    },
    'added-v30001-0180': {
      id: 'added-v30001-0180',
      title: '街巷角色动画',
      titleEn: 'Street Character Animation',
      category: 'motion',
      categoryName: '角色 / 虚幻场景',
      categoryNameEn: 'Character / UE Scene',
      videoUrl: 'assets/optimized/added-v30001-0180/8a46db64910c1909-web.mp4',
      poster: 'assets/optimized-images/193ddb83066f2889-a0066563-480w.webp',
      description: '虚幻引擎 5 场景搭建与三维角色穿梭运镜实验。',
      descriptionEn: 'UE5 urban environment layout and dynamic 3D camera staging.'
    },
    'added-render-test': {
      id: 'added-render-test',
      title: '能量实验',
      titleEn: 'Energy FX Render',
      category: 'motion',
      categoryName: '特效 / 动力学渲染',
      categoryNameEn: 'FX / Dynamics Render',
      videoUrl: 'assets/optimized/added-render-test/691a1bf6da2dbbec-web.mp4',
      poster: 'assets/optimized-images/5da0a011cbca2914-a0066563-480w.webp',
      description: 'Blender 粒子系统与动力学模拟，结合发光材质与后期合成。',
      descriptionEn: 'Blender particle dynamics simulation with emissive materials and compositing.'
    },
    'added-completed-film': {
      id: 'added-completed-film',
      title: '花与兔子',
      titleEn: 'Flower & Rabbit',
      category: 'story',
      categoryName: '短片 / 概念动画',
      categoryNameEn: 'Short Film / Concept Animation',
      videoUrl: 'assets/optimized/added-completed-film/bb09a3da3e160a0d-web.mp4',
      poster: 'assets/optimized-images/6d2f85fc57c178c2-a0066563-480w.webp',
      description: '细腻情感短篇，童话与未来视觉风格结合的艺术实验。',
      descriptionEn: 'Poetic short film exploring fairy-tale aesthetic in futuristic CG rendering.'
    },
    'work-street-ball': {
      id: 'work-street-ball',
      title: '街头篮球',
      titleEn: 'Streetball Energy',
      category: 'edit',
      categoryName: '运动 / 节奏快剪',
      categoryNameEn: 'Sports / Fast Edit',
      videoUrl: 'assets/uploads/desktop/work-1783436201027-desktop.mp4',
      poster: 'assets/optimized-images/8d357111b84eb7ad-a0066563-480w.webp',
      description: '高密度音乐卡点与动作剪辑，展现强烈的视听冲击力与节奏感。',
      descriptionEn: 'High-energy beat-matching and motion cutting delivering intense audio-visual rhythm.'
    },
    'featured-prove-it': {
      id: 'featured-prove-it',
      title: 'Prove It',
      titleEn: 'Prove It Commercial',
      category: 'edit',
      categoryName: '商业广告 / 剪辑包装',
      categoryNameEn: 'Commercial / Edit & Motion',
      videoUrl: 'assets/optimized/featured-prove-it/1476460cc117075e-web.mp4',
      poster: 'assets/optimized-images/99c48a03afa54602-a0066563-480w.webp',
      description: '品牌宣传广告商业剪辑与视觉包装，突出调色与节奏转化。',
      descriptionEn: 'Commercial brand editing and motion package with filmic grading.'
    },
    'featured-approach': {
      id: 'featured-approach',
      title: '搭讪',
      titleEn: 'The Approach',
      category: 'story',
      categoryName: '叙事 / 镜头剪辑',
      categoryNameEn: 'Narrative / Cinematic Edit',
      videoUrl: 'assets/optimized/featured-approach/ebd7e20914383cac-web.mp4',
      poster: 'assets/optimized-images/275d0ff36d09dc0c-a0066563-480w.webp',
      description: '电影感镜头剪辑，人物眼神交流与呼吸感微节奏把控。',
      descriptionEn: 'Cinematic storytelling edit emphasizing glances, micro-rhythm, and character dynamics.'
    },
    'featured-exported-film': {
      id: 'featured-exported-film',
      title: 'Two Seconds',
      titleEn: 'Two Seconds',
      category: 'edit',
      categoryName: '剪辑 / 达芬奇调色',
      categoryNameEn: 'Edit / Color Grading',
      videoUrl: 'assets/optimized/featured-exported-film/33eef9ca7328cfea-web.mp4',
      poster: 'assets/optimized-images/1fd3f7c48e33ddaa-a0066563-480w.webp',
      description: '达芬奇 ACES 色彩科学工作流调色与精剪范例。',
      descriptionEn: 'DaVinci Resolve ACES color-managed pipeline and precision editing showcase.'
    },
    'timeline-vertical': {
      id: 'timeline-vertical',
      title: 'AI 之后',
      titleEn: 'After AI',
      category: 'edit',
      categoryName: '竖版 / 信息流剪辑',
      categoryNameEn: 'Vertical / Feed Edit',
      videoUrl: 'assets/works/timeline-vertical.mp4',
      poster: 'assets/optimized-images/ddfc97d74e1f0d46-a0066563-320w.webp',
      description: '新媒体前 3 秒强抓眼球节奏实验与动态视觉合成。',
      descriptionEn: 'First 3-second hook experiment designed for mobile feed retention.'
    }
  };

  // State
  let currentLang = new URLSearchParams(window.location.search).get('lang') === 'en' ? 'en' : 'cn';
  let currentView = window.location.hash === '#cinema' ? 'cinema' : 'resume';
  let currentCategory = 'all';
  let lastResumeScroll = 0;

  // DOM Elements
  const resumeView = document.querySelector('#view-resume');
  const cinemaView = document.querySelector('#view-cinema');
  const segmentResume = document.querySelector('[data-switch-view="resume"]');
  const segmentCinema = document.querySelector('[data-switch-view="cinema"]');
  const langSwitchBtn = document.querySelector('#langSwitch');
  const toast = document.querySelector('#toast');
  const qrDialog = document.querySelector('#qrDialog');
  const qrDialogClose = document.querySelector('#qrDialogClose');
  const qrDialogImg = document.querySelector('#qrDialogImg');
  const qrDialogTitle = document.querySelector('#qrDialogTitle');
  const qrDialogDesc = document.querySelector('#qrDialogDesc');
  const resumePlayer = document.querySelector('#resumePlayer');
  const resumePlayerVideo = document.querySelector('#resumePlayerVideo');
  const resumePlayerClose = document.querySelector('#resumePlayerClose');
  const playerTitle = document.querySelector('#playerTitle');
  const playerCategory = document.querySelector('#playerCategory');
  const playerDesc = document.querySelector('#playerDesc');
  const cinemaGrid = document.querySelector('#cinemaGrid');
  const filterBtns = document.querySelectorAll('[data-filter]');
  const searchInput = document.querySelector('#workSearchInput');
  const printBtn = document.querySelector('#printBtn');

  // View Switching
  function switchView(viewName, workIdToPlay) {
    if (viewName === 'cinema') {
      if (currentView === 'resume') {
        lastResumeScroll = window.scrollY;
      }
      currentView = 'cinema';
      resumeView.setAttribute('hidden', '');
      cinemaView.removeAttribute('hidden');
      if (segmentResume) segmentResume.setAttribute('aria-selected', 'false');
      if (segmentCinema) segmentCinema.setAttribute('aria-selected', 'true');
      try {
        history.replaceState(null, '', '#cinema' + (currentLang === 'en' ? '?lang=en' : ''));
      } catch {}
      window.scrollTo({ top: 0, behavior: 'smooth' });

      if (workIdToPlay) {
        openPlayer(workIdToPlay);
      }
    } else {
      currentView = 'resume';
      cinemaView.setAttribute('hidden', '');
      resumeView.removeAttribute('hidden');
      if (segmentResume) segmentResume.setAttribute('aria-selected', 'true');
      if (segmentCinema) segmentCinema.setAttribute('aria-selected', 'false');
      try {
        history.replaceState(null, '', '#resume' + (currentLang === 'en' ? '?lang=en' : ''));
      } catch {}
      if (lastResumeScroll > 0) {
        window.scrollTo({ top: lastResumeScroll, behavior: 'smooth' });
      }
    }
  }

  // Player Control
  function openPlayer(workId) {
    const work = worksCatalog[workId];
    if (!work) return;

    playerTitle.textContent = currentLang === 'en' ? work.titleEn : work.title;
    playerCategory.textContent = currentLang === 'en' ? work.categoryNameEn : work.categoryName;
    playerDesc.textContent = currentLang === 'en' ? work.descriptionEn : work.description;
    
    resumePlayerVideo.src = work.videoUrl;
    resumePlayerVideo.poster = work.poster;
    if (typeof resumePlayer.showModal === 'function') {
      resumePlayer.showModal();
    } else {
      resumePlayer.setAttribute('open', '');
    }
    resumePlayerVideo.play().catch(() => {});
  }

  function closePlayer() {
    resumePlayerVideo.pause();
    resumePlayerVideo.removeAttribute('src');
    resumePlayerVideo.load();
    if (typeof resumePlayer.close === 'function') {
      resumePlayer.close();
    } else {
      resumePlayer.removeAttribute('open');
    }
  }

  if (resumePlayerClose) {
    resumePlayerClose.addEventListener('click', closePlayer);
  }
  if (resumePlayer) {
    resumePlayer.addEventListener('cancel', (e) => {
      e.preventDefault();
      closePlayer();
    });
  }

  // Render Cinema Works
  function renderCinemaWorks() {
    if (!cinemaGrid) return;
    const query = (searchInput ? searchInput.value.trim().toLowerCase() : '');
    
    const worksList = Object.values(worksCatalog).filter(w => {
      const matchCat = currentCategory === 'all' || w.category === currentCategory;
      const matchQuery = !query || 
        w.title.toLowerCase().includes(query) || 
        w.titleEn.toLowerCase().includes(query) || 
        w.description.toLowerCase().includes(query);
      return matchCat && matchQuery;
    });

    cinemaGrid.innerHTML = '';
    worksList.forEach(work => {
      const card = document.createElement('article');
      card.className = 'cinema-work-card';
      const title = currentLang === 'en' ? work.titleEn : work.title;
      const cat = currentLang === 'en' ? work.categoryNameEn : work.categoryName;
      const desc = currentLang === 'en' ? work.descriptionEn : work.description;
      const playText = currentLang === 'en' ? 'Play Film' : '播放完整作品';

      card.innerHTML = `
        <div class="work-card-thumb" data-play="${work.id}" role="button" tabindex="0" aria-label="${title} · ${playText}">
          <img src="${work.poster}" alt="${title}" loading="lazy">
          <div class="work-play-overlay">
            <div class="play-circle">
              <svg viewBox="0 0 24 24"><path d="m9 5 11 7-11 7z"/></svg>
            </div>
          </div>
        </div>
        <div class="work-card-info">
          <p class="work-card-meta">${cat}</p>
          <h3 class="work-card-title">${title}</h3>
          <p class="work-card-desc">${desc}</p>
          <div class="work-card-actions">
            <button type="button" class="action-btn action-btn-primary" data-play="${work.id}">
              <svg viewBox="0 0 24 24"><path d="m9 5 11 7-11 7z"/></svg>
              <span>${playText}</span>
            </button>
            <span class="work-card-badge">${work.category === 'story' ? 'AI短片' : (work.category === 'motion' ? '3D三维' : '后期剪辑')}</span>
          </div>
        </div>
      `;
      cinemaGrid.appendChild(card);
    });

    // Attach click handlers
    cinemaGrid.querySelectorAll('[data-play]').forEach(btn => {
      btn.addEventListener('click', () => {
        openPlayer(btn.getAttribute('data-play'));
      });
    });
  }

  // Toast Functionality
  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => {
      toast.classList.remove('show');
    }, 2400);
  }

  // Language Toggle
  function setLanguage(lang) {
    currentLang = lang;
    document.documentElement.lang = currentLang === 'en' ? 'en' : 'zh-CN';
    document.title = currentLang === 'en' 
      ? 'Junjie Lin (Highstrith) · Interactive Resume & Works' 
      : '林俊杰 · 个人简历与作品展厅 — Highstrith';

    document.querySelectorAll('[data-cn][data-en]').forEach(el => {
      el.textContent = el.dataset[currentLang];
    });
    document.querySelectorAll('[data-cn-label][data-en-label]').forEach(el => {
      el.setAttribute(el.tagName === 'IMG' ? 'alt' : 'aria-label', el.dataset[`${currentLang}Label`]);
    });

    if (langSwitchBtn) {
      langSwitchBtn.textContent = currentLang === 'en' ? '中文' : 'EN';
    }

    renderCinemaWorks();
  }

  // Event Listeners
  if (segmentResume) {
    segmentResume.addEventListener('click', () => switchView('resume'));
  }
  if (segmentCinema) {
    segmentCinema.addEventListener('click', () => switchView('cinema'));
  }
  document.querySelectorAll('[data-switch-view="resume"]').forEach(btn => {
    btn.addEventListener('click', () => switchView('resume'));
  });
  document.querySelectorAll('[data-switch-view="cinema"]').forEach(btn => {
    btn.addEventListener('click', () => switchView('cinema'));
  });

  // Spotlight direct play
  document.querySelectorAll('[data-play-work]').forEach(btn => {
    btn.addEventListener('click', () => {
      const workId = btn.getAttribute('data-play-work');
      switchView('cinema', workId);
    });
  });

  // QR Code Popups
  document.querySelectorAll('[data-open-qr]').forEach(btn => {
    btn.addEventListener('click', () => {
      const qrType = btn.getAttribute('data-open-qr');
      if (qrType === 'wechat') {
        qrDialogImg.src = 'assets/social/wechat-qr.png';
        qrDialogTitle.textContent = currentLang === 'en' ? 'WeChat Contact' : '微信扫码联系';
        qrDialogDesc.textContent = currentLang === 'en' ? 'ID: Gw1sgdsj_787' : '微信号：Gw1sgdsj_787（点击即可复制）';
      } else {
        qrDialogImg.src = 'assets/site-qr.svg';
        qrDialogTitle.textContent = currentLang === 'en' ? 'Scan to View Works' : '手机扫码浏览作品集';
        qrDialogDesc.textContent = 'highstrith.github.io/highstrithstate';
      }
      if (typeof qrDialog.showModal === 'function') {
        qrDialog.showModal();
      } else {
        qrDialog.setAttribute('open', '');
      }
    });
  });

  if (qrDialogClose) {
    qrDialogClose.addEventListener('click', () => {
      if (typeof qrDialog.close === 'function') {
        qrDialog.close();
      } else {
        qrDialog.removeAttribute('open');
      }
    });
  }

  // Copy to clipboard
  document.querySelectorAll('[data-copy]').forEach(btn => {
    btn.addEventListener('click', () => {
      const textToCopy = btn.getAttribute('data-copy');
      navigator.clipboard.writeText(textToCopy).then(() => {
        showToast(currentLang === 'en' ? `Copied: ${textToCopy}` : `已复制：${textToCopy}`);
      }).catch(() => {
        showToast(`微信号：${textToCopy}`);
      });
    });
  });

  // Print buttons
  document.querySelectorAll('#printBtn, #printBtn2').forEach(btn => {
    btn.addEventListener('click', () => {
      if (currentView !== 'resume') {
        switchView('resume');
      }
      setTimeout(() => {
        window.print();
      }, 150);
    });
  });

  // Category filters
  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.setAttribute('aria-pressed', 'false'));
      btn.setAttribute('aria-pressed', 'true');
      currentCategory = btn.getAttribute('data-filter');
      renderCinemaWorks();
    });
  });

  if (searchInput) {
    searchInput.addEventListener('input', renderCinemaWorks);
  }

  if (langSwitchBtn) {
    langSwitchBtn.addEventListener('click', () => {
      setLanguage(currentLang === 'cn' ? 'en' : 'cn');
    });
  }

  // Initialize
  setLanguage(currentLang);
  switchView(currentView);
  renderCinemaWorks();
})();
