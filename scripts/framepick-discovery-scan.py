#!/usr/bin/env python3
"""Bilibili discovery scanner for Framepick (local helper, no login).

Two steps, both in one file:

  python3 scripts/framepick-discovery-scan.py scan   --out /tmp/found.json [--limit 20]
  python3 scripts/framepick-discovery-scan.py enrich --file /tmp/found.json

`scan`  : opens the public Bilibili search page per keyword (newest first) and
          collects video cards. No login, no captcha bypass, no API signing.
`enrich` : opens each video page to confirm title/author and to look for an
          explicit AI-production statement in the description. Without that
          statement the item stays unproven and the CLI will reject it.

Output is the input format of scripts/framepick-discovery-cli.mjs.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'docs' / 'framepick-discovery-20261103' / 'sources.json'
DURATION = re.compile(r'(?:(\d+):)?(\d{1,3}):(\d{2})')
# Word-boundary matching: a bare "ai" substring also hits said/wait/email, which
# would make every page look like an AI production.
AI_PATTERNS = [
    re.compile(r'\bai\b'), re.compile(r'aigc'), re.compile(r'人工智能'), re.compile(r'ai\s*(生成|制作|短片|电影|动画|短剧|视频|绘)'),
    re.compile(r'midjourney'), re.compile(r'\bsora\b'), re.compile(r'可灵'), re.compile(r'runway'),
    re.compile(r'即梦'), re.compile(r'stable\s*diffusion'), re.compile(r'comfy\s*ui'), re.compile(r'\bveo\b'),
    re.compile(r'seedance'), re.compile(r'kling'), re.compile(r'\bhailuo\b'), re.compile(r'海螺ai'),
]
AI_LABELS = ['AI', 'AIGC', '人工智能', 'AI生成/AI制作', 'Midjourney', 'Sora', '可灵', 'Runway', '即梦', 'Stable Diffusion', 'ComfyUI', 'Veo', 'Seedance', 'Kling', 'Hailuo', '海螺AI']
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'

CARD_JS = """
() => Array.from(document.querySelectorAll('a[href*="/video/BV"]')).map((a) => {
  const card = a.closest('.bili-video-card') || a.closest('li') || a.parentElement;
  const raw = (card && card.innerText ? card.innerText : '');
  const text = raw.replace(/\\s*\\n\\s*/g, ' | ');
  const parts = text.split('|').map((s) => s.trim()).filter(Boolean);
  const titleNode = a.querySelector('.bili-video-card__info--tit, h3, [title]');
  const title = ((titleNode && (titleNode.getAttribute('title') || titleNode.textContent)) || a.getAttribute('title') || '').trim();
  const at = Math.max(parts.findIndex((p) => p === title), parts.findIndex((p) => title && p.includes(title.slice(0, 6))));
  return {
    url: a.href.split('?')[0].replace(/\\/+$/, ''),
    title: title,
    author: at >= 0 ? (parts[at + 1] || '') : '',
    text: text.slice(0, 400),
    duration: (parts.find((p) => /^(?:\\d+:)?\\d{1,3}:\\d{2}$/.test(p)) || ''),
    plays: (parts.find((p) => /^[\\d.]+万?$/.test(p)) || ''),
    date: (raw.match(/(\\d{4}-\\d{2}-\\d{2}|\\d{1,2}-\\d{1,2}|\\d+\\s*(?:分钟|小时|天)前)/) || ['', ''])[1],
  };
}).filter((item) => item.url && item.title && item.duration)
"""


def launch(playwright):
    try:
        return playwright.chromium.launch(channel='chrome', headless=True)
    except Exception:
        return playwright.chromium.launch(headless=True)


def scan(queries, limit, out):
    from playwright.sync_api import sync_playwright
    items = {}
    with sync_playwright() as p:
        browser = launch(p)
        context = browser.new_context(user_agent=UA, locale='zh-CN', viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        for query in queries:
            url = f'https://search.bilibili.com/all?keyword={query}&order=pubdate'
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=45000)
                page.wait_for_timeout(3500)
                for card in page.evaluate(CARD_JS):
                    if not card['author']:
                        continue
                    bv = card['url'].rsplit('/', 1)[-1]
                    if bv and bv not in items:
                        items[bv] = card
                    if len(items) >= limit * len(queries):
                        break
            except Exception as error:  # network hiccups must not kill the run
                print(f'  ! 关键词「{query}」抓取失败：{error}', file=sys.stderr)
            time.sleep(1.5)
        browser.close()
    candidates = []
    for bv, card in items.items():
        if not card['duration']:
            continue
        candidates.append({
            'title': card['title'][:80],
            'author': card['author'][:80] or '（未取到 UP 主）',
            'source': 'bilibili',
            'url': card['url'],
            'runtime': card['duration'],
            'publishedAt': card['date'],
            'popularity': {'metric': '播放', 'value': card['plays']} if card['plays'] else None,
            'note': f'搜索命中：{card["text"][:160]}',
            'aiEvidence': False,
            'aiEvidenceNote': '',
            'evidence': [{'kind': '搜索页快照', 'url': card['url'], 'note': card['text'][:200]}],
        })
    payload = {'runAt': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'), 'runBy': 'ai', 'candidates': candidates}
    Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
    print(f'扫描到 {len(candidates)} 条（已去同 BV、已过滤无时长条目）→ {out}')
    return payload


def enrich(path):
    from playwright.sync_api import sync_playwright
    payload = json.loads(Path(path).read_text(encoding='utf8'))
    with sync_playwright() as p:
        browser = launch(p)
        context = browser.new_context(user_agent=UA, locale='zh-CN', viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        for item in payload['candidates']:
            try:
                page.goto(item['url'], wait_until='domcontentloaded', timeout=45000)
                page.wait_for_timeout(2500)
                data = page.evaluate("""() => ({
                  ogTitle: (document.querySelector('meta[property="og:title"]') || {}).content || '',
                  desc: (document.querySelector('meta[name="description"]') || {}).content || '',
                  text: (document.body ? document.body.innerText : '').slice(0, 3000)
                })""")
            except Exception as error:
                item['note'] = f'{item.get("note", "")} · 打开原页失败：{error}'
                continue
            # Only the video's own title and description count as evidence: the
            # page body also carries recommendations, tags and ads that mention AI.
            haystack = f"{data['ogTitle']} {data['desc']}".lower()
            hit = None
            for index, pattern in enumerate(AI_PATTERNS):
                found = pattern.search(haystack)
                if found:
                    start = max(0, found.start() - 40)
                    hit = (AI_LABELS[index], haystack[start:found.end() + 40].strip())
                    break
            if hit:
                item['aiEvidence'] = True
                item['aiEvidenceNote'] = f'原页出现「{hit[0]}」：{hit[1][:160]}'
            else:
                item['aiEvidence'] = False
                item['aiEvidenceNote'] = '原页未出现 AI／AIGC 等制作属性表述，未认定为 AI 作品'
            item['pageTitle'] = data['ogTitle'].replace('_哔哩哔哩_bilibili', '').strip()
            item['pageDescription'] = data['desc'][:300]
            item['titleMatched'] = item['pageTitle'][:6] in item['title'] or item['title'][:6] in item['pageTitle']
            item['authorMatched'] = bool(item['author']) and item['author'] in data['text']
            time.sleep(1.2)
        browser.close()
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf8')
    proved = sum(1 for item in payload['candidates'] if item.get('aiEvidence'))
    print(f'复核 {len(payload["candidates"])} 条，其中 {proved} 条在原页找到 AI 制作属性表述 → {path}')
    return payload


def main():
    parser = argparse.ArgumentParser(description='Bilibili discovery scanner')
    parser.add_argument('mode', choices=['scan', 'enrich'])
    parser.add_argument('--out', default='/tmp/framepick-found.json')
    parser.add_argument('--file', help='enrich 模式下的候选文件')
    parser.add_argument('--limit', type=int, default=20, help='每个关键词最多保留多少条')
    parser.add_argument('--queries', help='逗号分隔的关键词，默认取 sources.json')
    args = parser.parse_args()

    if args.mode == 'scan':
        queries = args.queries.split(',') if args.queries else json.loads(CONFIG.read_text(encoding='utf8'))['queries']
        scan([q.strip() for q in queries if q.strip()], args.limit, args.out)
    else:
        if not args.file:
            parser.error('enrich 需要 --file')
        enrich(args.file)


if __name__ == '__main__':
    main()
