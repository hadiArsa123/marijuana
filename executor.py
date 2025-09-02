import subprocess
from datetime import datetime, timedelta

# Range tanggal (mundur dari 2025-06-30 ke 2025-06-01)
start_date = datetime(2025, 6, 30)
end_date = datetime(2025, 6, 1)

threads = 1200
result_file = "44.txt"

current_date = start_date

while current_date >= end_date:
    tanggal_str = current_date.strftime("%Y/%m/%d")
    print(f"Menjalankan grabber.py untuk tanggal {tanggal_str} -> {result_file}")

    # Jalankan grabber.py dengan input otomatis
    process = subprocess.Popen(
        ["python", "grabber.py"],  # Windows pakai "python", bukan "python3"
        stdin=subprocess.PIPE,
        text=True
    )

    # Kirim input ke grabber.py
    process.communicate(f"{tanggal_str}\n{threads}\n{result_file}\n")

    # Mundur 1 hari
    current_date -= timedelta(days=1)