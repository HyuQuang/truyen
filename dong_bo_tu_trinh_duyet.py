#!/usr/bin/env python3
import ctypes, struct, json, os, glob, subprocess

print("⏳ Đang quét dữ liệu mới từ trình duyệt Chrome...")

lib = ctypes.CDLL('libsnappy.so')
lib.snappy_uncompress.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
lib.snappy_uncompress.restype = ctypes.c_int
lib.snappy_uncompressed_length.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
lib.snappy_uncompressed_length.restype = ctypes.c_int

def decompress(compressed_bytes):
    uncompressed_len = ctypes.c_size_t()
    res = lib.snappy_uncompressed_length(compressed_bytes, len(compressed_bytes), ctypes.byref(uncompressed_len))
    if res != 0 or uncompressed_len.value > 25000000:
        return None
    out_buf = ctypes.create_string_buffer(uncompressed_len.value)
    res = lib.snappy_uncompress(compressed_bytes, len(compressed_bytes), out_buf, ctypes.byref(uncompressed_len))
    if res != 0:
        return None
    return out_buf.raw[:uncompressed_len.value]

def read_varint(buf, offset):
    res, shift = 0, 0
    while True:
        b = buf[offset]
        offset += 1
        res |= (b & 0x7f) << shift
        if (b & 0x80) == 0: break
        shift += 7
    return res, offset

def parse_block(buf):
    num_restarts = struct.unpack('<I', buf[-4:])[0]
    restarts_pos = len(buf) - 4 - 4 * num_restarts
    pos, entries, last_key = 0, [], bytearray()
    while pos < restarts_pos:
        shared, pos = read_varint(buf, pos)
        non_shared, pos = read_varint(buf, pos)
        val_len, pos = read_varint(buf, pos)
        key = last_key[:shared] + buf[pos : pos + non_shared]
        pos += non_shared
        val = buf[pos : pos + val_len]
        pos += val_len
        last_key = key
        entries.append((bytes(key), bytes(val)))
    return entries

# Find leveldb files
ldb_files = glob.glob(os.path.expanduser('~/.config/google-chrome/Default/Local Storage/leveldb/*.ldb'))
extracted = {}

for ldb_path in ldb_files:
    try:
        with open(ldb_path, 'rb') as f:
            data = f.read()
        if len(data) < 48: continue
        if data[-8:] != bytes.fromhex('57fb808b247547db'): continue
        
        meta_off, p = read_varint(data, len(data) - 48)
        meta_sz, p = read_varint(data, p)
        idx_off, p = read_varint(data, p)
        idx_sz, p = read_varint(data, p)
        idx_raw = data[idx_off : idx_off + idx_sz]
        idx_block = decompress(idx_raw) if data[idx_off + idx_sz] == 1 else idx_raw
        if not idx_block: continue

        for max_key, handle in parse_block(idx_block):
            b_off, p = read_varint(handle, 0)
            b_sz, p = read_varint(handle, p)
            b_raw = data[b_off : b_off + b_sz]
            b_type = data[b_off + b_sz]
            b_data = decompress(b_raw) if b_type == 1 else b_raw
            if b_data:
                for k, v in parse_block(b_data):
                    if b'hyu_repo_' in k:
                        user_key = k[:-8].decode('latin1', errors='ignore').split('\x01')[-1]
                        val_text = v[1:].decode('utf-16le', errors='ignore')
                        try:
                            obj = json.loads(val_text)
                            extracted[user_key] = obj
                        except:
                            pass
    except Exception as e:
        pass

html_path = os.path.expanduser('~/Desktop/website_truyen/index.html')
if not os.path.exists(html_path):
    print("❌ Không tìm thấy file index.html tại Desktop/website_truyen!")
    exit(1)

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

import re
keys = ['manhua_review', 'manhua_short', 'ggggg', 'gggg_short', 'truyen_tranh']
updated_count = 0

for k in keys:
    repo_key = 'hyu_repo_' + k
    if repo_key in extracted:
        new_items = extracted[repo_key]
        print(f"📦 Tìm thấy kho {k}: {len(new_items)} mục từ trình duyệt")
        updated_count += len(new_items)

print(f"✨ Tổng cộng đã nạp: {updated_count} mục.")
