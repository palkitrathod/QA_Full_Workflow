import sys, json, os, requests

def main():
    args = json.load(sys.stdin)
    base_url = args.get('base_url')
    ticket_id = args.get('ticket_id')
    token = args.get('auth_token') or os.getenv('JIRA_TOKEN')
    if not (base_url and ticket_id):
        print(json.dumps({"status": "error", "error": "Missing base_url or ticket_id"}))
        return
    url = f"{base_url}/rest/api/3/issue/{ticket_id}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        print(json.dumps({"status": "success", "data": resp.json()}))
    except Exception as e:
        print(json.dumps({"status": "error", "error": str(e)}))

if __name__ == "__main__":
    main()
