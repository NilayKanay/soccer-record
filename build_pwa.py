# -*- coding: utf-8 -*-
"""soccer_record_app.html (空のアプリ) から PWA一式 (index.html, sw.js, manifest.json, icons) を生成する．
実行: python build_pwa.py   (dev/pwa/ に出力．学校データは入れない)"""
import io, os, re, json, math
from PIL import Image, ImageDraw

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, '..', 'soccer_record_app.html')
html = io.open(src, encoding='utf-8').read()

# 学校データ・大会情報が空であることを確認 (個人情報を公開しない)
for sid in ('schoolDbSeed', 'tournamentInfoSeed'):
    m = re.search(r'<script type="application/json" id="%s">(.*?)</script>' % sid, html, re.S)
    assert m and m.group(1).strip() in ('{}', '[]', ''), '%s is not empty' % sid

APP_VER = re.search(r"APP_BUILD\s*=\s*'([^']+)'", html).group(1)
cache_name = 'soccer-record-' + APP_VER

head_add = '''<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#1b6b3a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="サッカー記録">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" type="image/png" href="icon-192.png">
'''
assert html.count('<meta name="viewport"') == 1
html = re.sub(r'(<meta name="viewport"[^>]*>\n?)', lambda m: m.group(1) + head_add, html, 1)

reg = '''<script>
if ((location.protocol === 'https:' || location.hostname === 'localhost') && 'serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('sw.js').catch(function () {});
  });
}
</script>
'''
i = html.rfind('</body>')
assert i > 0 and html[i:].count('<script') == 0
html = html[:i] + reg + html[i:]
io.open(os.path.join(here, 'index.html'), 'w', encoding='utf-8', newline='').write(html)

sw = '''// オフライン用 Service Worker (自動生成: build_pwa.py)
const CACHE = '%s';
const FILES = ['./', 'index.html', 'manifest.json', 'icon-180.png', 'icon-192.png', 'icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
// キャッシュ優先 + 裏で更新 (ネットが無くても開ける．更新は次回起動で反映)
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(caches.open(CACHE).then(c => c.match(e.request, {ignoreSearch: true}).then(hit => {
    const net = fetch(e.request).then(r => { if (r && r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || net;
  })));
});
''' % cache_name
io.open(os.path.join(here, 'sw.js'), 'w', encoding='utf-8', newline='').write(sw)

manifest = {
    "name": "サッカー公式記録 電子入力", "short_name": "サッカー記録",
    "start_url": "./index.html", "scope": "./", "display": "standalone",
    "orientation": "any", "background_color": "#ffffff", "theme_color": "#1b6b3a",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}
io.open(os.path.join(here, 'manifest.json'), 'w', encoding='utf-8', newline='').write(json.dumps(manifest, ensure_ascii=False, indent=2))

def icon(size):
    S = 4; n = size * S
    im = Image.new('RGB', (n, n), (27, 107, 58))
    d = ImageDraw.Draw(im)
    c = n / 2; r = n * 0.34
    d.ellipse([c - r, c - r, c + r, c + r], fill='white', outline=(20, 20, 20), width=int(n * 0.012))
    def poly(cx, cy, rad, rot=-90):
        return [(cx + rad * math.cos(math.radians(rot + 72 * i)), cy + rad * math.sin(math.radians(rot + 72 * i))) for i in range(5)]
    d.polygon(poly(c, c, r * 0.36), fill=(20, 20, 20))
    for i in range(5):
        a = math.radians(-90 + 72 * i)
        px, py = c + r * 0.72 * math.cos(a), c + r * 0.72 * math.sin(a)
        d.line([(c + r * 0.36 * math.cos(a), c + r * 0.36 * math.sin(a)), (px, py)], fill=(20, 20, 20), width=int(n * 0.012))
        d.polygon(poly(c + r * 1.02 * math.cos(a), c + r * 1.02 * math.sin(a), r * 0.2, rot=-90 + 72 * i + 36 + 90), fill=(20, 20, 20))
    return im.resize((size, size), Image.LANCZOS)
for s in (180, 192, 512):
    icon(s).save(os.path.join(here, 'icon-%d.png' % s))
print('built', cache_name, len(html))
