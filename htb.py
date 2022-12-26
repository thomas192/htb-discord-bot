import requests
import os
from dotenv import load_dotenv
from utils import load_from_json, write_to_json

BASE_URL = "https://www.hackthebox.eu/api/v4"
USER_AGENT = "curl/7.68.0"

load_dotenv()


# Login to HTB and return a token string
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


# Dumps data from machines HTB endpoint
def dump_htb_endpoint(token: str, endpoint: str, out_file_name: str):
    print("dump_htb_endpoint()")
    print(f"[*] dumping endpoint: {endpoint}")
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json", "Authorization": f"Bearer {token}"}
    url = f"https://www.hackthebox.eu/api/v4/{endpoint}"

    r = requests.get(url, headers=headers)
    data = r.json()
    data = data["info"]

    write_to_json(f"{out_file_name}.json", data)


# Updates active machines
def update_active_machines():
    print("update_active_machines()")
    dump_htb_endpoint(TOKEN, "machine/list", out_file_name="machines_active")


# Returns a list of ids of active machines
# [[id, name, difficulty], ...]
def get_active_machines():
    print("get_active_machines()")
    active_machines = load_from_json("machines_active.json")
    machine_list = []
    for m in active_machines:
        machine_list.append([str(m["id"]), m["name"], m["difficultyText"]])
    return machine_list


# Updates files that store machines activity
def update_machines_activity():
    print("update_machines_activity()")
    machine_list = get_active_machines()
    # Update activity for each machine
    for m in machine_list:
        print(f"[*] updating machine activity {m}")
        endpoint = "machine/activity/" + m[0]
        out_file_name = "machines_activity_" + m[0]
        dump_htb_endpoint(TOKEN, endpoint, out_file_name)
