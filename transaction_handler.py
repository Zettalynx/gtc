import os
import json
import time
import random
import requests

# Ambil data dari environment GitHub Actions
GITHUB_EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Load event payload dari GitHub
with open(GITHUB_EVENT_PATH, "r") as f:
    event = json.load(f)

issue_title = event["issue"]["title"]
issue_number = event["issue"]["number"]
issue_user = event["issue"]["user"]["login"]

# Tentukan sender dan recipient berdasarkan judul issue
if issue_title == "Terima dari github-action":
    sender = "github-action"
    recipient = issue_user
elif issue_title.startswith("Kirim ke "):
    sender = issue_user
    recipient = issue_title.split(" ")[-1]
else:
    print("Issue tidak dikenali, abaikan.")
    exit(0)

# Generate amount acak antara 1 sampai 10
amount = round(random.uniform(1, 10), 2)

# Struktur transaksi
transaction = {
    "from": sender,
    "to": recipient,
    "amount": amount,
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
}

# File transaksi
TRANSACTION_FILE = "daily_transaction.json"

# Cek apakah file transaksi sudah ada
# Cek apakah file transaksi sudah ada dan memiliki konten yang valid
if os.path.exists(TRANSACTION_FILE):
    try:
        with open(TRANSACTION_FILE, "r") as f:
            content = f.read().strip()  # Hilangkan whitespace kosong
            transactions = json.loads(content) if content else []
    except json.JSONDecodeError:
        print("File JSON rusak, membuat ulang.")
        transactions = []
else:
    transactions = []


# Tambahkan transaksi baru
transactions.append(transaction)

# Simpan kembali file transaksi
with open(TRANSACTION_FILE, "w") as f:
    json.dump(transactions, f, indent=4)

print(f"Transaksi berhasil ditambahkan: {transaction}")

# Tutup issue setelah transaksi selesai
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

issue_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues/{issue_number}"
requests.patch(issue_url, headers=headers, json={"state": "closed"})

print(f"Issue #{issue_number} ditutup.")
