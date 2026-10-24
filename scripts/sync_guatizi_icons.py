#!/usr/bin/env python3
"""Download airport logo images listed on guatizi.com into icons/guatizi/."""
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

BASE = "https://guatizi.com/"
OUT = Path("icons/guatizi")
OUT.mkdir(parents=True, exist_ok=True)
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://guatizi.com/",
})

def get_soup(url):
    r = session.get(url, timeout=25)
    if r.status_code == 403:
        raise RuntimeError(
            f"网站拒绝 GitHub Actions 服务器访问（HTTP 403）：{url}。"
            "这不是仓库权限错误；请勿反复重跑。可尝试从允许访问的网络获取图片，"
            "或使用网站/图片权利人提供的公开下载地址。"
        )
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def clean_name(s):
    s = re.sub(r"[\\/:*?\"<>|]", "_", s).strip(" .-_")
    s = re.sub(r"\s+", "-", s)
    return (s[:70] or "airport")

def image_url(img):
    for attr in ("data-src", "data-lazy-src", "src", "data-original"):
        val = img.get(attr)
        if val and not val.startswith("data:"):
            return urljoin(BASE, val)
    srcset = img.get("srcset")
    if srcset:
        return urljoin(BASE, srcset.split(",")[0].strip().split()[0])
    return None

def main():
    home = get_soup(BASE)
    seen = {}
    for a in home.select('a[href*="/sites/"]'):
        href = urljoin(BASE, a.get("href", ""))
        if not re.search(r"/sites/[^/]+\.html", urlparse(href).path):
            continue
        name = a.get_text(" ", strip=True)
        if not name:
            name = a.get("title", "").strip()
        if not name:
            continue
        # Prefer a logo image attached to the listing card.
        container = a
        for _ in range(3):
            if container.parent:
                container = container.parent
            imgs = container.find_all("img")
            candidates = [image_url(i) for i in imgs]
            candidates = [u for u in candidates if u]
            if candidates:
                seen.setdefault(href, (name, candidates[0]))
                break
        seen.setdefault(href, (name, None))

    manifest = []
    for idx, (page, (name, img_url)) in enumerate(seen.items(), 1):
        try:
            if not img_url:
                soup = get_soup(page)
                # Use images explicitly labelled with the airport name; avoid price-chart screenshots.
                candidates = []
                for img in soup.find_all("img"):
                    alt = (img.get("alt") or img.get("title") or "").strip()
                    src = image_url(img)
                    if src and alt and (name.split()[0] in alt or alt in name or name in alt):
                        candidates.append(src)
                if candidates:
                    img_url = candidates[0]
            if not img_url:
                manifest.append({"name": name, "page": page, "status": "no_logo_found"})
                continue
            resp = session.get(img_url, timeout=25)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").lower()
            ext = Path(urlparse(img_url).path).suffix.lower()
            if ext not in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"):
                ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
                       "image/gif": ".gif", "image/svg+xml": ".svg"}.get(content_type.split(";")[0], ".img")
            if not content_type.startswith("image/") and ext == ".img":
                manifest.append({"name": name, "page": page, "image": img_url, "status": "not_an_image"})
                continue
            filename = f"{idx:04d}-{clean_name(name)}{ext}"
            path = OUT / filename
            path.write_bytes(resp.content)
            manifest.append({"name": name, "page": page, "source_image": img_url,
                             "file": str(path), "bytes": len(resp.content), "status": "downloaded"})
            print(f"[OK] {name} -> {path}")
        except Exception as exc:
            manifest.append({"name": name, "page": page, "status": "error", "error": str(exc)})
            print(f"[WARN] {name}: {exc}")
        time.sleep(0.15)

    (OUT / "manifest.json").write_text(json.dumps({
        "source": BASE, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_listed": len(manifest),
        "downloaded": sum(x["status"] == "downloaded" for x in manifest),
        "items": manifest
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Finished: {sum(x['status'] == 'downloaded' for x in manifest)} downloaded / {len(manifest)} listed")

if __name__ == "__main__":
    main()
