#!/usr/bin/env python3
"""
Hume AI Speech Prosody Dataset Downloader
Extracts metadata (X, Y, Color, emotion scores) + downloads audio files
Data embedded directly in the page source as escaped JSON
"""

import re
import json
import csv
import os
import sys
import time
import random
import subprocess
import requests

PAGE_URL = "https://www.hume.ai/explore/speech-prosody-model"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(OUT_DIR, "audio")
CSV_PATH = os.path.join(OUT_DIR, "labels.csv")
METADATA_PATH = os.path.join(OUT_DIR, "metadata.json")
TRACKING_PATH = os.path.join(OUT_DIR, "download_progress.csv")

MIN_FREE_GB = 5

def check_free_space():
    st = os.statvfs(OUT_DIR)
    free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
    return free_gb

def fetch_page():
    print("Fetching page source...")
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    r = requests.get(PAGE_URL, headers=headers, timeout=30)
    r.raise_for_status()
    return r.text

def extract_data(html):
    print("Extracting embedded dataset...")
    # The data is embedded as escaped JSON: \"data\":[{\"File\":...}]
    # Find the start of the data array
    marker = '\\"data\\":[{'
    idx = html.find(marker)
    if idx == -1:
        raise ValueError("Could not find data array in page source")

    # We need to find the matching closing bracket
    # Start after "data":
    start = idx + len('\\"data\\":')

    # Extract a large chunk and unescape it
    # The data ends before the next top-level key or closing brace
    # Strategy: grab everything from start, unescape, then parse
    chunk = html[start:start + 5_000_000]  # 5MB should be enough

    # Unescape the JSON (it's escaped with backslashes)
    chunk = chunk.replace('\\"', '"').replace('\\\\', '\\')

    # Now parse the array
    # Find where the array ends
    depth = 0
    end = 0
    in_string = False
    escape_next = False
    for i, ch in enumerate(chunk):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\':
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if end == 0:
        raise ValueError("Could not find end of data array")

    arr_str = chunk[:end]
    print(f"Extracted {end} chars of JSON array, parsing...")
    data = json.loads(arr_str)
    print(f"Found {len(data)} entries")
    return data

def load_tracking():
    done = set()
    if os.path.exists(TRACKING_PATH):
        with open(TRACKING_PATH) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['status'] == 'ok':
                    done.add(row['url'])
    return done

def append_tracking(url, filename, status):
    exists = os.path.exists(TRACKING_PATH)
    with open(TRACKING_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['url', 'filename', 'status'])
        if not exists:
            writer.writeheader()
        writer.writerow({'url': url, 'filename': filename, 'status': status})

def download_audio(url, dest_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Referer": PAGE_URL,
    }
    part_path = dest_path + ".part"
    try:
        r = requests.get(url, headers=headers, timeout=30, stream=True)
        r.raise_for_status()
        with open(part_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        os.rename(part_path, dest_path)
        return True
    except Exception as e:
        if os.path.exists(part_path):
            os.remove(part_path)
        print(f"  ERROR: {e}")
        return False

def save_metadata(data):
    with open(METADATA_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved metadata to {METADATA_PATH}")

def save_csv(data):
    # Collect all emotion columns
    all_keys = set()
    for entry in data:
        all_keys.update(entry.keys())

    # Fixed columns first, then emotion columns sorted
    fixed = ['File', 'filename', 'X', 'Y', 'Color']
    emotion_cols = sorted(all_keys - set(fixed))
    fieldnames = fixed + emotion_cols

    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for entry in data:
            row = {k: entry.get(k, '') for k in fieldnames}
            # Add local filename
            url = entry.get('File', '')
            fname = os.path.basename(url)
            row['filename'] = fname
            writer.writerow(row)
    print(f"Saved labels CSV to {CSV_PATH}")

def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)

    html = fetch_page()
    data = extract_data(html)

    # Save metadata + CSV immediately
    save_metadata(data)
    save_csv(data)

    # Load tracking
    done = load_tracking()
    print(f"\nAlready downloaded: {len(done)}")
    print(f"Total entries: {len(data)}")

    todo = [e for e in data if e.get('File') not in done]
    print(f"To download: {len(todo)}\n")

    success = 0
    errors = 0

    for i, entry in enumerate(todo):
        url = entry.get('File', '')
        if not url:
            continue

        fname = os.path.basename(url)
        dest = os.path.join(AUDIO_DIR, fname)

        # Skip if already exists on disk
        if os.path.exists(dest):
            append_tracking(url, fname, 'ok')
            done.add(url)
            continue

        # Disk space check
        free = check_free_space()
        if free < MIN_FREE_GB:
            print(f"LOW DISK SPACE: {free:.1f}GB free. Stopping.")
            sys.exit(1)

        print(f"[{i+1}/{len(todo)}] {fname} ... ", end='', flush=True)
        ok = download_audio(url, dest)

        if ok:
            append_tracking(url, fname, 'ok')
            success += 1
            print("ok")
        else:
            append_tracking(url, fname, 'error')
            errors += 1

        time.sleep(random.uniform(0.1, 0.3))

    print(f"\nDone. Success: {success}, Errors: {errors}")
    print(f"Audio: {AUDIO_DIR}")
    print(f"Labels: {CSV_PATH}")
    print(f"Metadata: {METADATA_PATH}")

if __name__ == '__main__':
    main()
