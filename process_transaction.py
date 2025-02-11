import hashlib
import os
import json
import requests
import re
import random
from datetime import datetime

GITHUB_REPO = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

MEMPOOL_FILE = "mempool.json"
BALANCES_FILE = "balances.json"

# Fungsi memuat saldo pengguna
def load_balances():
    if os.path.exists(BALANCES_FILE):
        with open(BALANCES_FILE, "r") as f:
            return json.load(f)
    return {"github-action": {"balance": 50, "last_transaction": None}}

# Fungsi menyimpan saldo pengguna
def save_balances(balances):
    with open(BALANCES_FILE, "w") as f:
        json.dump(balances, f, indent=4)

# Fungsi memuat transaksi dari mempool
def load_mempool():
    if os.path.exists(MEMPOOL_FILE):
        with open(MEMPOOL_FILE, "r") as f:
            return json.load(f)
    return []

# Fungsi menyimpan transaksi ke mempool
def save_mempool(mempool):
    with open(MEMPOOL_FILE, "w") as f:
        json.dump(mempool, f, indent=4)

# Fungsi membuat txid
def generate_txid(sender, recipient, amount, timestamp):
    return hashlib.sha256(f"{sender}{recipient}{amount}{timestamp}".encode()).hexdigest()

# Fungsi menambahkan transaksi
def add_transaction(sender, recipient, amount):
    balances = load_balances()
    if sender == recipient or sender not in balances or balances[sender]["balance"] < amount:
        return None
    timestamp = datetime.utcnow().isoformat()
    balances[sender]["balance"] -= amount
    balances[sender]["last_transaction"] = timestamp
    if recipient not in balances:
        balances[recipient] = {"balance": 0, "last_transaction": None}
    balances[recipient]["balance"] += amount
    balances[recipient]["last_transaction"] = timestamp
    txid = generate_txid(sender, recipient, amount, timestamp)
    mempool = load_mempool()
    mempool.append({"from": sender, "to": recipient, "amount": amount, "timestamp": timestamp, "txid": txid})
    save_mempool(mempool)
    save_balances(balances)
    return txid

# Fungsi membaca issue dari GitHub
def process_issue():
    issues_url = f"https://api.github.com/repos/{GITHUB_REPO}/issues?state=open"
    response = requests.get(issues_url, headers=HEADERS)
    issues = response.json()
    
    for issue in issues:
        title = issue["title"]
        issue_number = issue["number"]
        username = issue["user"]["login"]
        
        if title.startswith("Terima dari github-action"):
            balances = load_balances()
            max_amount = balances["github-action"]["balance"] / 3
            random_amount = round(random.uniform(0.001, max_amount), 6)
            txid = add_transaction("github-action", username, random_amount)
        elif match := re.match(r"Kirim ([\d\.]+) ke ([\w-]+)", title):
            amount, recipient = float(match.group(1)), match.group(2)
            txid = add_transaction(username, recipient, amount)
        else:
            continue
        
        comment_body = f"✅ Transaksi berhasil! TXID: {txid}" if txid else "❌ Transaksi gagal!"
        requests.post(f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}/comments", json={"body": comment_body}, headers=HEADERS)
        requests.patch(f"https://api.github.com/repos/{GITHUB_REPO}/issues/{issue_number}", json={"state": "closed"}, headers=HEADERS)

if __name__ == "__main__":
    process_issue()
