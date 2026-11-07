#!/usr/bin/env python3
import urllib.request, json, time, os, subprocess, shutil

FIREBASE_URL = 'https://huy-truyen-default-rtdb.firebaseio.com'

PLAYLIST_MAP = {
    'manhua_review': {
        'pid': 'PLiRIDCLG9ywgG1ICxbFRo6Jd_oo3_VedK',
        'default_genre': 'Review Tổng Hợp',
        'is_short': False,
        'label': 'Anime Review (anime =))'
    },
    'manhua_short': {
        'pid': 'PLSrwH1M5cNVI',
        'default_genre': 'Shorts / Highlight',
        'is_short': True,
        'label': 'Anime Shorts'
    },
    'ggggg': {
        'pid': 'PLHoJ3mnZpj-M',
        'default_genre': 'GGGGG Series',
        'is_short': False,
        'label': 'GGGGGGGG Series'
    },
    'gggg_short': {
        'pid': 'PLcTLFRFPWUHQ',
        'default_genre': 'GGGG Short',
        'is_short': True,
        'label': '=)) ggggggg Short'
    }
}

def get_yt_dlp_path():
    candidate = os.path.expanduser('~/.local/bin/yt-dlp')
    if os.path.exists(candidate) and os.access(candidate, os.X_OK):
        return candidate
    return shutil.which('yt-dlp')

def format_duration(sec):
    if not sec or sec <= 0:
        return '00:00'
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def fetch_playlist_yt_dlp(playlist_id, is_short=False):
    yt_bin = get_yt_dlp_path()
    if not yt_bin:
        print("⚠️ Không tìm thấy yt-dlp, vui lòng kiểm tra ~/.local/bin/yt-dlp")
        return []

    url = f'https://www.youtube.com/playlist?list={playlist_id}'
    cmd = [
        yt_bin,
        '--flat-playlist',
        '--dump-single-json',
        '--no-warnings',
        '--ignore-errors',
        url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
        data = json.loads(res.stdout)
        raw_entries = data.get('entries', [])
    except Exception as e:
        print(f"❌ Lỗi khi quét playlist {playlist_id} bằng yt-dlp: {e}")
        return []

    items = []
    seen = set()
    for entry in raw_entries:
        if not entry:
            continue
        vid_id = entry.get('id')
        if not vid_id or vid_id in seen:
            continue
        seen.add(vid_id)

        title = entry.get('title') or 'Video YouTube'
        if title in ('[Private video]', '[Deleted video]'):
            continue

        raw_dur = entry.get('duration')
        sec = int(raw_dur) if raw_dur is not None and str(raw_dur).isdigit() else 0
        dur_str = format_duration(sec) if sec > 0 else ('0:30' if is_short else '10:00')

        channel = entry.get('channel') or entry.get('uploader') or 'YouTube Playlist'
        link = f"https://www.youtube.com/shorts/{vid_id}" if is_short else f"https://www.youtube.com/watch?v={vid_id}"

        items.append({
            'vid_id': vid_id,
            'title': title[:180],
            'duration': dur_str,
            'seconds': sec,
            'channel': channel,
            'link': link,
            'thumb': f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg",
            'thumb_high': f"https://img.youtube.com/vi/{vid_id}/hqdefault.jpg"
        })

    return items

def sync_all_playlists():
    print("🚀 Bắt đầu quét chuyên sâu 100% video YouTube qua yt-dlp...")
    total_added_all = 0

    for repo_key, conf in PLAYLIST_MAP.items():
        pid = conf['pid']
        label = conf.get('label', repo_key)
        print(f"\n📂 Đang quét: {label} (Playlist ID: {pid})...")
        crawled = fetch_playlist_yt_dlp(pid, is_short=conf['is_short'])
        print(f" -> Trích xuất thành công: {len(crawled)} video từ YouTube Playlist")

        fb_url = f'{FIREBASE_URL}/repos/{repo_key}.json'
        try:
            req = urllib.request.Request(fb_url)
            cur_data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8')) or []
        except Exception as e:
            print(f" ⚠️ Không lấy được dữ liệu hiện tại từ Firebase: {e}")
            cur_data = []

        existing_map = {}
        for item in cur_data:
            if isinstance(item, dict) and item.get('vid_id'):
                existing_map[item['vid_id']] = item

        added = []
        updated_list = []

        for c_item in crawled:
            vid_id = c_item['vid_id']
            if vid_id in existing_map:
                # Giữ nguyên thông tin đã có, cập nhật nếu thiếu
                old = existing_map[vid_id]
                old['title'] = c_item['title']
                if not old.get('duration') or old.get('duration') == '00:00':
                    old['duration'] = c_item['duration']
                    old['seconds'] = c_item['seconds']
                if not old.get('channel') or old.get('channel') == 'Kênh mới':
                    old['channel'] = c_item['channel']
                updated_list.append(old)
            else:
                c_item['genre'] = conf['default_genre']
                c_item['desc'] = 'Video tự động cập nhật từ YouTube Playlist.'
                added.append(c_item)
                updated_list.append(c_item)

        # Giữ lại các video cũ đã có mà có thể YouTube tạm thời không trả về
        seen_ids = set(c['vid_id'] for c in crawled)
        for old_id, old_item in existing_map.items():
            if old_id not in seen_ids:
                updated_list.append(old_item)

        # Sắp xếp theo thời lượng giảm dần
        updated_list.sort(key=lambda x: x.get('seconds', 0), reverse=True)

        print(f" ✨ Phát hiện: {len(added)} video MỚI! Tổng hiện tại: {len(updated_list)} video")

        # Lưu lên Firebase
        put_req = urllib.request.Request(
            fb_url,
            data=json.dumps(updated_list, ensure_ascii=False).encode('utf-8'),
            method='PUT',
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(put_req, timeout=30)
        print(f" ✅ Đã đồng bộ trọn vẹn 100% ({len(updated_list)} video) lên Firebase Cloud Database!")
        total_added_all += len(added)

    print(f"\n🎉 HOÀN THÀNH XUẤT SẮC! Đã bổ sung tổng cộng {total_added_all} video mới vào Cloud.")
    return total_added_all

if __name__ == '__main__':
    sync_all_playlists()
