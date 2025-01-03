import os
import tkinter as tk
from tkinter import messagebox
import asyncio
import aiohttp
import logging
import subprocess
import sys

# Gerekli kütüphaneleri yükleyen fonksiyon
def install_requirements():
    try:
        with open('requirements.txt', 'r') as file:
            packages = file.readlines()
            for package in packages:
                package_name = package.strip()
                if package_name != "tkinter":  # tkinter'ı yüklememek için kontrol
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                    print(f"Installed {package_name}")
    except Exception as e:
        print(f"Error installing packages: {e}")


# Kütüphane kontrolü ve yükleme
install_requirements()

VANITY_LIST = []
DELAY = 0.1
claimed = False

# Log dosyasını logs klasörüne yazma
log_folder = 'logs'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

log_file = os.path.join(log_folder, 'shunko_snipe_log.txt')

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

async def notify(url, json):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=json) as response:
            if response.status == 200:
                print("[+] Webhook notification sent successfully.")
            else:
                print(f"[-] Failed to send webhook notification. Status: {response.status}")

async def claim(url, json, headers):
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, json=json, headers=headers) as response:
            return response.status

async def fetch_vanity(vanity, x, TOKEN, WEBHOOK_URL, SERVER_ID):
    if not vanity:
        return
    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": TOKEN}
        async with session.get(f"https://canary.discord.com/api/v10/invites/{vanity}", headers=headers) as response:
            status = response.status
            if status == 404:
                json = {"code": vanity}
                idk2 = await claim(
                    f"https://canary.discord.com/api/v10/guilds/{SERVER_ID}/vanity-url",
                    json, headers
                )
                if idk2 in (200, 201, 204):
                    print(f"[+] Vanity URL claimed: {vanity}")
                    await notify(WEBHOOK_URL, {"content": f"Vanity URL claimed: {vanity}"})
                else:
                    print(f"[-] Failed to claim vanity: {vanity}")
                    await notify(WEBHOOK_URL, {"content": f"Failed to claim vanity: {vanity} | status: {idk2}"})
            elif status == 200:
                print(f"[+] Attempt: {x} | Vanity: {vanity}")
            elif status == 429:
                print("[-] Rate limit problem, retrying after some delay")
                await notify(WEBHOOK_URL, {"content": f"Rate limit error for vanity: {vanity}, retrying..."})
                raise SystemExit(1)
            else:
                print(f"[-] Unexpected error occurred with status: {status}")
                await notify(WEBHOOK_URL, {"content": f"Unexpected error occurred with status: {status} for vanity: {vanity}"})
                raise SystemExit(1)
    await asyncio.sleep(DELAY)

async def thread_executor(vanity, x, TOKEN, WEBHOOK_URL, SERVER_ID):
    try:
        await fetch_vanity(vanity, x, TOKEN, WEBHOOK_URL, SERVER_ID)
    except Exception as error:
        logging.error(f"Error in thread {x} for vanity {vanity}: {error}")
        print(f"Error in thread {x} for vanity {vanity}: {error}")
        await asyncio.sleep(1)
        await thread_executor(vanity, x, TOKEN, WEBHOOK_URL, SERVER_ID)

async def main(TOKEN, WEBHOOK_URL, SERVER_ID):
    print("Clearing console and preparing...")
    print("Logging into the Discord account...")
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": TOKEN}
            async with session.get("https://canary.discord.com/api/v9/users/@me", headers=headers) as response:
                if response.status in (200, 201, 204):
                    user = await response.json()
                    id = user["id"]
                    username = user["username"]
                    print(f"Successfully logged in as {username} | {id}")
                    logging.info(f"Logged in successfully as {username} | {id}")
                    await notify(WEBHOOK_URL, {"content": f"Shunko Sniper has started successfully. Logged in as {username}."})
                elif response.status == 429:
                    logging.error("Rate limit error occurred while logging in")
                    raise SystemExit(1)
                else:
                    logging.error("Bad Auth: Invalid Token or Authorization")
                    print("Bad Auth")
                    raise SystemExit(1)

        for x in range(100000000):
            for i in range(len(VANITY_LIST)):
                if claimed:
                    logging.info("Claim process completed")
                    raise SystemExit(1)
                await asyncio.sleep(DELAY)
                await thread_executor(VANITY_LIST[i], x, TOKEN, WEBHOOK_URL, SERVER_ID)

    except Exception as error:
        logging.error(f"Error in main execution: {error}")
        print("An error occurred:", error)
        await notify(WEBHOOK_URL, {"content": f"An error occurred in main execution: {error}"})

root = tk.Tk()
root.title("Shunko Sniper")

root.config(bg="#FFFFFF")
root.geometry("600x600")
root.resizable(False, False)

title_label = tk.Label(root, text="Shunko Sniper", font=("Helvetica", 22, "bold"), fg="#000000", bg="#FFFFFF")
title_label.pack(pady=20)

token_label = tk.Label(root, text="Token", font=("Helvetica", 12), fg="#000000", bg="#FFFFFF")
token_label.pack(pady=5)
token_entry = tk.Entry(root, width=50, font=("Helvetica", 12), bg="#FFFFFF", fg="#000000", bd=2, relief="solid")
token_entry.pack(pady=10)

webhook_label = tk.Label(root, text="Webhook URL", font=("Helvetica", 12), fg="#000000", bg="#FFFFFF")
webhook_label.pack(pady=5)
webhook_entry = tk.Entry(root, width=50, font=("Helvetica", 12), bg="#FFFFFF", fg="#000000", bd=2, relief="solid")
webhook_entry.pack(pady=10)

server_id_label = tk.Label(root, text="Server ID", font=("Helvetica", 12), fg="#000000", bg="#FFFFFF")
server_id_label.pack(pady=5)
server_id_entry = tk.Entry(root, width=50, font=("Helvetica", 12), bg="#FFFFFF", fg="#000000", bd=2, relief="solid")
server_id_entry.pack(pady=10)

vanity_list_label = tk.Label(root, text="Vanity List (comma separated)", font=("Helvetica", 12), fg="#000000", bg="#FFFFFF")
vanity_list_label.pack(pady=5)
vanity_list_entry = tk.Entry(root, width=50, font=("Helvetica", 12), bg="#FFFFFF", fg="#000000", bd=2, relief="solid")
vanity_list_entry.pack(pady=10)

delay_label = tk.Label(root, text="Delay (seconds)", font=("Helvetica", 12), fg="#000000", bg="#FFFFFF")
delay_label.pack(pady=5)

delay_slider = tk.Scale(root, from_=0.1, to_=10, orient="horizontal", resolution=0.1, sliderlength=30, length=400, bg="#FFFFFF", fg="#000000", troughcolor="#1ABC9C")
delay_slider.set(0.1)
delay_slider.pack(pady=20)

def start_sniping():
    global VANITY_LIST, DELAY, claimed, SERVER_ID, WEBHOOK_URL

    token = token_entry.get()
    webhook_url = webhook_entry.get()
    server_id = server_id_entry.get()

    VANITY_LIST = vanity_list_entry.get().split(",")
    DELAY = delay_slider.get()

    if not token or not webhook_url or not server_id or not VANITY_LIST:
        messagebox.showerror("Error", "All fields must be filled!")
        logging.error("User attempted to start without filling all fields.")
        return

    SERVER_ID = server_id
    WEBHOOK_URL = webhook_url

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(token, webhook_url, server_id))

start_button = tk.Button(root, text="Start Sniping", font=("Helvetica", 16), bg="#000000", fg="#FFFFFF", relief="flat", command=start_sniping, height=2, width=20)
start_button.pack(pady=20)

root.mainloop()
