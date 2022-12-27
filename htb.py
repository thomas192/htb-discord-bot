import time
import requests
import os
from dotenv import load_dotenv
from utils import load_from_json, write_to_json

BASE_URL = "https://www.hackthebox.eu/api/v4"
USER_AGENT = "curl/7.68.0"

load_dotenv()


def get_login_token() -> str:
    url = f"{BASE_URL}/login"
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json;charset=utf-8"}
    data = {
        "email": os.getenv("EMAIL"),
        "password": os.getenv("PASSWORD"),
        "remember": True
    }

    r = requests.post(url, headers=headers, json=data)
    data = r.json()
    token = data["message"]["access_token"]

    return token


TOKEN = os.getenv("HTB_TOKEN")


def dump_htb_endpoint(token: str, endpoint: str, out_file_name: str):
    print(f"[*] dump_htb_endpoint({endpoint})")
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json", "Authorization": f"Bearer {token}"}
    url = f"https://www.hackthebox.eu/api/v4/{endpoint}"
    r = requests.get(url, headers=headers)
    data = r.json()
    if endpoint == "machine/list":
        data = data["info"]
    elif endpoint == "challenge/list":
        data = data["challenges"]
    write_to_json(f"{out_file_name}.json", data)


def update_active(machines=True, challenges=True):
    print(f"update_active()")
    if machines:
        dump_htb_endpoint(TOKEN, "machine/list", out_file_name="machine/active")
    if challenges:
        dump_htb_endpoint(TOKEN, "challenge/list", out_file_name="challenge/active")


# Return info about active machine and/or challenge
# Format: [{id, type, name, difficulty}, {...}]
def get_active(machines=True, challenges=True):
    print(f"get_active()")
    actives = []
    if machines:
        m_list = load_from_json("machine/active.json")
        for m in m_list:
            actives.append({"id": str(m["id"]), "type": "machine", "name": m["name"], "difficulty": m["difficultyText"]})
    if challenges:
        c_list = load_from_json("challenge/active.json")
        for c in c_list:
            actives.append({"id": str(c["id"]), "type": "challenge", "name": c["name"], "difficulty": c["difficulty"]})

    return actives


def update_activity(machines=True, challenges=True):
    print("update_activity()")
    actives = get_active(machines=machines, challenges=challenges)
    for e in actives:
        print(f"[*] updating {e['type']} activity {e['id']}")
        endpoint = f"{e['type']}/activity/{e['id']}"
        out_file_name = f"{e['type']}/{e['id']}"
        dump_htb_endpoint(TOKEN, endpoint, out_file_name)
        time.sleep(3)
