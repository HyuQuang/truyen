#!/usr/bin/env python3
import urllib.request, re, json, time, os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
}

FIREBASE_URL = 'https://huy-truyen-default-rtdb.firebaseio.com'

PLAYLIST_MAP = {
    'manhua_review': {
        'pid': 'PLiRIDCLG9ywgG1ICxbFRo6Jd_oo3_VedK',
        'default_genre': 'Review Tổng Hợp',
        'is_short': False
    },
    'manhua_short': {
        'pid': 'PLSrwH1M5cNVI',
        'default_genre': 'Shorts / Highlight',
        'is_short': True
    },
    'ggggg': {
        'pid': 'PLHoJ3mnZpj-M',
        'default_genre': 'GGGGG Series',
        'is_short': False
    },
    'gggg_short': {
        'pid': 'PLcTLFRFPWUHQ',
        'default_genre': 'GGGG Short',
        'is_short': True
    }
}

def extract_all_video_items(obj):
    items = []
    if isinstance(obj, dict):
        if 'lockupViewModel' in obj:
            lk = obj['lockupViewModel']
            vid_id = lk.get('contentId')
            title = lk.get('rendererContext', {}).get('accessibilityContext', {}).get('label', '')
            dur = ''
            overlays = lk.get('contentImage', {}).get('thumbnailViewModel', {}).get('overlays', [])
            for ov in overlays:
                for b in ov.get('thumbnailBottomOverlayViewModel', {}).get('badges', []):
                    t = b.get('thumbnailBadgeViewModel', {}).get('text')
                    if t: dur = t
            if vid_id:
                title = re.sub(r'\s*\d+\s*(?:giờ|phút|giây|tiếng).*$', '', title).strip() or title
                items.append({'id': vid_id, 'title': title or 'Video YouTube', 'duration': dur or '10:00'})
        elif 'shortsLockupViewModel' in obj:
            slk = obj['shortsLockupViewModel']
            vid_id = slk.get('onTap', {}).get('innertubeCommand', {}).get('reelWatchEndpoint', {}).get('videoId')
            title = slk.get('overlayMetadata', {}).get('primaryText', {}).get('content', '')
            if vid_id:
                items.append({'id': vid_id, 'title': title or 'YouTube Short', 'duration': '0:30'})
        else:
            for v in obj.values():
                items.extend(extract_all_video_items(v))
    elif isinstance(obj, list):
        for it in obj:
            items.extend(extract_all_video_items(it))
    return items

def find_continuation_token(obj):
    if isinstance(obj, dict):
        if 'continuationCommand' in obj and 'token' in obj['continuationCommand']:
            return obj['continuationCommand']['token']
        for v in obj.values():
            tok = find_continuation_token(v)
            if tok: return tok
    elif isinstance(obj, list):
        for it in obj:
            tok = find_continuation_token(it)
            if tok: return tok
    return None

def fetch_playlist_all(playlist_id, is_short=False):
    url = f'https://www.youtube.com/playlist?list={playlist_id}'
    req = urllib.request.Request(url, headers={'User-Agent': HEADERS['User-Agent'], 'Accept-Language': HEADERS['Accept-Language']})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f'Error loading {playlist_id}: {e}')
        return []

    m = re.search(r'var ytInitialData\s*=\s*(\{.*?\});</script>', html) or re.search(r'ytInitialData\s*=\s*(\{.*?\});', html)
    if not m:
        return []

    data = json.loads(m.group(1))
    items = extract_all_video_items(data)
    token = find_continuation_token(data)

    page = 1
    while token and page < 30:
        page += 1
        payload = {
            'context': {'client': {'clientName': 'WEB', 'clientVersion': '2.20240101.00.00', 'hl': 'vi', 'gl': 'VN'}},
            'continuation': token
        }
        api_req = urllib.request.Request('https://www.youtube.com/youtubei/v1/browse', data=json.dumps(payload).encode('utf-8'), headers=HEADERS)
        try:
            resp = json.loads(urllib.request.urlopen(api_req).read().decode('utf-8'))
            cont_items = extract_all_video_items(resp)
            items.extend(cont_items)
            token = find_continuation_token(resp)
        except Exception as e:
            print(f'Continuation page {page} error: {e}')
            break

    seen = set()
    unique_items = []
    for it in items:
        if it['id'] not in seen:
            seen.add(it['id'])
            unique_items.append(it)
    return unique_items

def main():
    print("🚀 Bắt đầu quét tự động các danh sách phát YouTube...")
    total_added_all = 0

    for repo_key, conf in PLAYLIST_MAP.items():
        pid = conf['pid']
        print(f"\n📂 Đang quét kho: {repo_key} (Playlist: {pid})...")
        crawled = fetch_playlist_all(pid, is_short=conf['is_short'])
        print(f" -> Tìm thấy {len(crawled)} video trên YouTube")

        fb_url = f'{FIREBASE_URL}/repos/{repo_key}.json'
        fb_req = urllib.request.Request(fb_url)
        try:
            cur_data = json.loads(urllib.request.urlopen(fb_req).read().decode('utf-8')) or []
        except:
            cur_data = []

        existing_ids = set(v.get('vid_id') for v in cur_data if v.get('vid_id'))
        added = []

        for it in crawled:
            if it['id'] not in existing_ids:
                sec = 0
                dur_parts = it['duration'].split(':')
                for part in dur_parts:
                    sec = (60 * sec) + (int(part) if part.isdigit() else 0)
                added.append({
                    'title': it['title'][:160],
                    'duration': it['duration'],
                    'seconds': sec,
                    'vid_id': it['id'],
                    'channel': 'YouTube Playlist',
                    'link': f'https://www.youtube.com/shorts/{it["id"]}' if conf['is_short'] else f'https://www.youtube.com/watch?v={it["id"]}',
                    'thumb': f'https://img.youtube.com/vi/{it["id"]}/mqdefault.jpg',
                    'thumb_high': f'https://img.youtube.com/vi/{it["id"]}/hqdefault.jpg',
                    'genre': conf['default_genre'],
                    'desc': 'Video tự động cập nhật từ YouTube Playlist.'
                })

        if added:
            total_added_all += len(added)
            merged = added + cur_data
            merged.sort(key=lambda x: x.get('seconds', 0), reverse=True)
            print(f" ✨ Phát hiện {len(added)} video MỚI! Tổng hiện tại: {len(merged)}")
            
            put_req = urllib.request.Request(
                fb_url,
                data=json.dumps(merged, ensure_ascii=False).encode('utf-8'),
                method='PUT',
                headers={'Content-Type': 'application/json'}
            )
            urllib.request.urlopen(put_req)
            print(f" ✅ Đã lưu thẳng lên Firebase Cloud Database!")
        else:
            print(f" ℹ️ Không có video mới (Kho đã có đủ {len(cur_data)} video).")

    print(f"\n🎉 HOÀN THÀNH TOÀN BỘ! Đã bổ sung tổng cộng {total_added_all} video mới vào Cloud.")

if __name__ == '__main__':
    main()
