import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os

# ====== CONFIG ======
wp_paths = [
    "/wp-login.php",
    "/wp/wp-login.php",
    "/blog/wp-login.php",
    "/cms/wp-login.php",
    "/admin/wp-login.php",
    "/wordpress/wp-login.php"
]

batch_size = 10000      # jumlah URL per batch
max_threads = 1000       # sesuaikan, 200 contoh yang lebih aman daripada 1000
timeout_sec = 5         # timeout per request
found_file = "found_wp.txt"   # file hasil
checkpoint_file = "checkpoint.txt"  # menyimpan indeks baris terakhir yang diproses

# ====== FUNSI CEK ======
def check_wp(session, url):
    """Cek semua kemungkinan path WordPress login, return path pertama ditemukan"""
    for path in wp_paths:
        target = url.rstrip("/") + path
        try:
            # gunakan session untuk koneksi yang lebih efisien
            response = session.get(target, timeout=timeout_sec)
            if response.status_code == 200:
                return target
        except requests.RequestException:
            continue
    return None

def process_batch(batch, batch_number):
    found_urls = []
    total = len(batch)
    start_time = time.time()

    # buat session sekali per batch
    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {executor.submit(check_wp, session, url): (i, url) for i, url in enumerate(batch)}
            completed = 0
            for future in as_completed(futures):
                idx, url = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    # jangan biarkan satu error mematikan seluruh batch
                    print(f"\n[ERROR] saat cek {url}: {e}")
                    result = None

                completed += 1
                if result:
                    found_urls.append(result)
                    print(f"[FOUND] {result}")

                # Progress & estimasi waktu (tampilkan setiap 100 atau akhir batch)
                if completed % 100 == 0 or completed == total:
                    elapsed = time.time() - start_time
                    percent = completed / total * 100
                    # amankan div by zero (completed won't be zero here)
                    est_total = elapsed / (completed / total)
                    est_remaining = est_total - elapsed
                    print(f"Batch {batch_number} Progress: {completed}/{total} ({percent:.2f}%), "
                          f"Elapsed: {int(elapsed)}s, Est Remaining: {int(est_remaining)}s", end='\r')

    # Simpan hasil batch
    if found_urls:
        with open(found_file, "a", encoding="utf-8") as f:
            for url in found_urls:
                f.write(url + "\n")
    print()  # newline setelah batch selesai

# ====== HELPER CHECKPOINT ======
def save_checkpoint(line_index):
    with open(checkpoint_file, "w", encoding="utf-8") as f:
        f.write(str(line_index))

def load_checkpoint():
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                return int(f.read().strip() or 0)
        except Exception:
            return 0
    return 0

# ====== MAIN ======
if __name__ == "__main__":
    list_file = input("Masukkan nama file list (misal: list.txt): ").strip()

    if not os.path.exists(list_file):
        print(f"❌ File '{list_file}' tidak ditemukan.")
        exit(1)

    # load checkpoint: indeks baris yang sudah selesai (0-based)
    start_idx = load_checkpoint()
    if start_idx > 0:
        print(f"Resuming dari baris ke-{start_idx + 1} (checkpoint).")

    batch = []
    count = 0
    current_line_idx = 0  # indeks baris file (0-based)

    with open(list_file, "r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f):
            current_line_idx = idx
            if idx < start_idx:
                continue  # skip yang sudah diproses menurut checkpoint
            url = line.strip()
            if url:
                batch.append(url)

            if len(batch) >= batch_size:
                count += 1
                print(f"\nProcessing batch #{count}, {len(batch)} URLs (file line {idx + 1})")
                process_batch(batch, count)
                batch = []
                # simpan checkpoint: baris terakhir yang sudah dilewati
                save_checkpoint(idx + 1)

    # Sisa batch terakhir
    if batch:
        count += 1
        print(f"\nProcessing batch #{count}, {len(batch)} URLs (file line {current_line_idx + 1})")
        process_batch(batch, count)
        save_checkpoint(current_line_idx + 1)

    # jika ingin menghapus checkpoint setelah sukses:
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    print("\n✅ Semua batch selesai.")
