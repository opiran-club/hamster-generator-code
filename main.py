import asyncio
import requests
import uuid
import os
import sys
import time
import random
import json
from colorama import *

init(autoreset=True)

mrh = Fore.LIGHTRED_EX
pth = Fore.LIGHTWHITE_EX
hju = Fore.LIGHTGREEN_EX
kng = Fore.LIGHTYELLOW_EX
bru = Fore.LIGHTBLUE_EX
reset = Style.RESET_ALL
htm = Fore.LIGHTBLACK_EX

EVENTS_DELAY = 20000 / 1000 

def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)

config = load_config()
games = config['games']

def load_proxies():
    proxies = []
    if config.get('use_proxies'):
        try:
            with open('proxies.txt', 'r') as file:
                for line in file:
                    proxies.append(parse_proxy(line.strip()))
        except FileNotFoundError:
            print("proxies.txt not found")
    return proxies

def parse_proxy(proxy_string):
    proxy_parts = proxy_string.split('@')
    auth = proxy_parts[0].split(':')
    host_port = proxy_parts[1].split(':')
    return {
        'http': f"http://{auth[0]}:{auth[1]}@{host_port[0]}:{host_port[1]}",
        'https': f"http://{auth[0]}:{auth[1]}@{host_port[0]}:{host_port[1]}"
    }

def get_proxy(proxies):
    if proxies:
        return random.choice(proxies)
    return None

def _banner():
    banner = r"""
 ██╗████████╗███████╗     ██╗ █████╗ ██╗    ██╗
 ██║╚══██╔══╝██╔════╝     ██║██╔══██╗██║    ██║
 ██║   ██║   ███████╗     ██║███████║██║ █╗ ██║
 ██║   ██║   ╚════██║██   ██║██╔══██║██║███╗██║
 ██║   ██║   ███████║╚█████╔╝██║  ██║╚███╔███╔╝
 ╚═╝   ╚═╝   ╚══════╝ ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝  """ 
    print(Fore.GREEN + Style.BRIGHT + banner + Style.RESET_ALL)
    print(hju + f" Hamster Promo Code Generator")
    print(mrh + f" NOT FOR SALE = Free to use")
    print(mrh + f" before start please '{hju}git pull{mrh}' to update bot\n")

def _clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def log_line():
    print(pth + "~" * 60)

def countdown_timer(seconds):
    while seconds:
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        h = str(h).zfill(2)
        m = str(m).zfill(2)
        s = str(s).zfill(2)
        print(f"{pth}please wait until {h}:{m}:{s} ", flush=True, end="\r")
        seconds -= 1
        time.sleep(1)
    print(f"{pth}please wait until {h}:{m}:{s} ", flush=True, end="\r")

def generate_client_id():
    timestamp = int(time.time() * 1000)
    random_numbers = ''.join([str(random.randint(0, 9)) for _ in range(19)])
    return f"{timestamp}-{random_numbers}"

def generate_uuid():
    return str(uuid.uuid4())

async def login(client_id, app_token, proxies=None):
    response = requests.post('https://api.gamepromo.io/promo/login-client', json={
        'appToken': app_token,
        'clientId': client_id,
        'clientOrigin': 'deviceid'
    }, proxies=proxies)

    if response.status_code != 200:
        raise Exception('Failed to login')

    data = response.json()
    return data['clientToken']

async def emulate_progress(client_token, promo_id, proxies=None):
    response = requests.post('https://api.gamepromo.io/promo/register-event', headers={
        'Authorization': f'Bearer {client_token}',
        'Content-Type': 'application/json'
    }, json={
        'promoId': promo_id,
        'eventId': generate_uuid(),
        'eventOrigin': 'undefined'
    }, proxies=proxies)

    if response.status_code != 200:
        return False

    data = response.json()
    return data['hasCode']

async def generate_key(client_token, promo_id, proxies=None):
    response = requests.post('https://api.gamepromo.io/promo/create-code', headers={
        'Authorization': f'Bearer {client_token}',
        'Content-Type': 'application/json'
    }, json={
        'promoId': promo_id
    }, proxies=proxies)

    if response.status_code != 200:
        raise Exception('Failed to generate key')

    data = response.json()
    return data['promoCode']

def sleep(ms):
    time.sleep(ms / 1000)

def delay_random():
    return random.random() / 3 + 1

def print_progress(iteration, total, prefix='', suffix='', decimals=1, length=35, fill='█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(hju + f'\r{prefix} |{pth}{bar}{hju}| {pth}{percent}{bru}% {hju}{suffix}', end='\r')
    if iteration == total: 
        print()

async def generate_key_process(game, key_count, proxies):
    client_id = generate_client_id()
    client_token = None
    try:
        client_token = await login(client_id, game['appToken'], proxies)
    except Exception as error:
        print(mrh + f"Failed to login: {error}")
        return None

    for i in range(11):
        await asyncio.sleep(EVENTS_DELAY * delay_random())
        has_code = await emulate_progress(client_token, game['promoId'], proxies)
        print_progress(i + 1, 11, prefix='Progress:', suffix='Complete', length=35)
        if has_code:
            break

    try:
        key = await generate_key(client_token, game['promoId'], proxies)
        return key
    except Exception as error:
        print(f"Failed to generate key: {error}")
        return None

async def main():
    _clear()
    _banner()
    log_line()
    proxies = load_proxies()

    while True:
        available_games = list(games.values())
        sample_size = min(10, len(available_games))
        random_games = random.sample(available_games, sample_size)

        for game in random_games:
            print(hju + f"Generating {kng}{game['name']} {hju}promo codes...")
            keys = await asyncio.gather(*[generate_key_process(game, 1, get_proxy(proxies)) for _ in range(10)])
            keys = list(filter(None, keys))

            if keys:
                with open('promo.txt', 'a') as file:
                    for key in keys:
                        file.write(f"{key}\n")

            print(hju + f"Generated {pth}{len(keys)} promo code's for {kng}{game['name']}. {hju}Sleeping...        ")
            countdown_timer(10)

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print(mrh + f"\rSuccessfully logged out of the bot\n")
            sys.exit()
