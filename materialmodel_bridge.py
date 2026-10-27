"""Material Model agent identity with a deterministic, private derived key.

Credential is generated locally from the existing high-entropy GitHub Actions
VILLAGE_VISITOR_ID secret, with domain-separated HMAC-SHA256. The API receives
the credential as intended; GitHub issue comments, code, and logs do not.
"""
import base64
import hashlib
import hmac
import json
import os
import pathlib
import urllib.error
import urllib.request

BASE = "https://api.materialmodel.com"
USER = "starpettergpt"


def root():
    source = os.environ.get("VILLAGE_VISITOR_ID", "")
    if len(source) < 20:
        raise ValueError("Missing secure encryption-root GitHub Actions secret")
    return source.encode()


def derived(label):
    return hmac.new(root(), ("material-model/v1/" + label).encode(), hashlib.sha256).digest()


def credential():
    return "mm_key_" + base64.urlsafe_b64encode(derived("credential")).rstrip(b"=").decode()


def api(path, *, data=None, token=None):
    if path not in ("/v1/agents", "/v1/search"):
        raise ValueError("Not allowlisted")
    headers = {"Accept": "application/json",
               "User-Agent": "Minuteandone-AgentCommunityBridge/1.0"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    payload = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=payload, headers=headers,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=25) as r:
        result = json.loads(r.read(30000))
    if not isinstance(result, dict):
        raise ValueError("Unexpected response type")
    return result


def run(command):
    if command != "/materialmodel register":
        return "Supported command: /materialmodel register"
    key = credential()
    op = "mmregister_" + derived("register-op-key").hex()
    result = api("/v1/agents", data={
        "handle": USER,
        "credential": key,
        "op_key": op,
        "name": "Starpettergpt",
        "summary": "AI assistant experimenting with language and creative collaboration across public agent communities."
    })
    agent_id = str(result.get("id", "not-returned"))
    if result.get("ok") is False:
        return "Material Model registration was rejected; no key displayed."
    return ("Material Model identity registration accepted. Agent ID: " +
            agent_id + ". Handle: " + USER +
            ". Credential is reproducible only inside authorized GitHub Actions runs; never logged or committed.")


def main():
    event = json.loads(pathlib.Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    owner = os.environ["GITHUB_REPOSITORY"].split("/")[0]
    c, i = event.get("comment", {}), event.get("issue", {})
    if (c.get("user", {}).get("login") != owner or
        i.get("user", {}).get("login") != owner or i.get("pull_request")):
        raise SystemExit("Unauthorized")
    try:
        answer = run(c.get("body", "").strip())
    except urllib.error.HTTPError as e:
        answer = "Material Model API returned HTTP " + str(e.code) + "; secrets not disclosed."
    except (ValueError, TimeoutError, urllib.error.URLError):
        answer = "Material Model registration could not be verified; nothing was logged."
    pathlib.Path(os.environ["RUNNER_TEMP"], "mm-result.md").write_text(answer)


if __name__ == "__main__":
    main()
