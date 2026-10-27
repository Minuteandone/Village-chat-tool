"""One-account Agentboard bridge with encrypted-at-rest credential storage.

Only owner-created GitHub issue comments trigger commands.
The GitHub Actions secret VILLAGE_VISITOR_ID is used as a high-entropy
encryption root, never printed or included in outgoing HTTP requests.
No token is written into the repository, issue replies, or logs.
"""
import base64
import hashlib
import hmac
import json
import os
import pathlib
import re
import secrets
import urllib.error
import urllib.request

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

ROOT = pathlib.Path("workspace/.agent-credentials")
VAULT = ROOT / "agentboard.v1.json"
BASE = "https://www.agentboard.ai"
AGENT_NAME = "Starpettergpt"
UA = "Minuteandone-AgentboardBridge/1.0"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Redirects are not permitted for credentialed requests")


OPENER = urllib.request.build_opener(NoRedirect())


def safe(s):
    return re.sub(r"@(?![\\u200b\\u200c\\u200d])", "@\\u200b", str(s))


def encryption_root():
    root = os.environ.get("VILLAGE_VISITOR_ID", "")
    if len(root) < 20:
        raise ValueError("Missing high-entropy VILLAGE_VISITOR_ID GitHub Actions secret")
    return root.encode("utf-8")


def derive_key(salt):
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt,
                info=b"Minuteandone-agentboard-credential-v1").derive(encryption_root())


def encrypt(value):
    salt, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    data = json.dumps(value, separators=(",", ":")).encode()
    ciphertext = AESGCM(derive_key(salt)).encrypt(nonce, data, b"agentboard.v1")
    b64 = lambda b: base64.b64encode(b).decode("ascii")
    return {"version": 1, "salt": b64(salt),
            "nonce": b64(nonce), "ciphertext": b64(ciphertext)}


def decrypt(box):
    if box.get("version") != 1:
        raise ValueError("Unknown vault version")
    b64 = base64.b64decode
    salt, nonce, ciphertext = (b64(box[k]) for k in ("salt", "nonce", "ciphertext"))
    return json.loads(AESGCM(derive_key(salt)).decrypt(
        nonce, ciphertext, b"agentboard.v1"))


def saved_identity():
    if not VAULT.exists():
        raise ValueError("No local agent credential. Register first.")
    item = decrypt(json.loads(VAULT.read_text()))
    key = item.get("credential", "")
    if not isinstance(key, str) or not key.startswith("agb_"):
        raise ValueError("Invalid saved credential")
    return item


def persist_identity(value):
    ROOT.mkdir(parents=True, exist_ok=True)
    payload = encrypt(value)
    test = decrypt(payload)
    if test != value:
        raise ValueError("Credential encryption verification failed")
    temp = VAULT.with_suffix(".tmp")
    temp.write_text(json.dumps(payload) + "\\n")
    os.replace(temp, VAULT)


def api(path, *, payload=None, token=None, idem=None):
    allowed_paths = (
        path in ("/api/agents/register", "/api/me")
        or re.fullmatch(r"/api/boards/(general|introductions)/threads", path)
        or re.fullmatch(r"/api/threads/[a-zA-Z0-9_-]{1,100}/replies", path)
    )
    if not allowed_paths:
        raise ValueError("Endpoint not allowlisted")
    headers = {"Accept": "application/json", "User-Agent": UA}
    if token:
        headers["Authorization"] = "Bearer " + token
    if idem:
        headers["Idempotency-Key"] = idem
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload, ensure_ascii=False).encode()
    request = urllib.request.Request(
        BASE + path, data=body, headers=headers,
        method="POST" if body is not None else "GET")
    with OPENER.open(request, timeout=25) as response:
        result = json.loads(response.read(80_000).decode())
    if not isinstance(result, dict):
        raise ValueError("Unexpected API response")
    return result


def handle(command, comment_id):
    if command == "/agentboard register":
        if VAULT.exists():
            identity = saved_identity()
            return ("Already registered, credential safely encrypted. "
                    "Handle: " + str(identity.get("handle", "unknown")))
        root = encryption_root()
        idem = "agentboard-one-" + hmac.new(
            root, b"starpettergpt-2026-registration", hashlib.sha256
        ).hexdigest()[:32]
        response = api("/api/agents/register", payload={
            "name": AGENT_NAME,
            "description": "GPT-based participant in public AI-agent forums; explores language, creativity and collaborative thought experiments."
        }, idem=idem)
        credential = response.get("credential")
        agent = response.get("agent") or {}
        if not isinstance(credential, str) or not credential.startswith("agb_"):
            raise ValueError("Registration response did not contain expected credential")
        handle = str(agent.get("handle", ""))
        persist_identity({"credential": credential, "handle": handle,
                          "profile_url": str(agent.get("url", ""))})
        return ("Agentboard registration succeeded. Encrypted credential saved to "
                "workspace/.agent-credentials/agentboard.v1.json. "
                "Handle: " + handle + ". Profile: " + str(agent.get("url", "")))
    if command == "/agentboard status":
        item = saved_identity()
        result = api("/api/me", token=item["credential"])
        agent = result.get("agent") or result.get("profile") or {}
        return ("Agentboard credential verified. Handle: " +
                str(agent.get("handle", item.get("handle", "unknown"))) +
                ". Raw credential remains hidden.")
    if command.startswith("/agentboard post\\n"):
        parts = command.split("\\n", 2)
        if len(parts) != 3:
            raise ValueError("Post requires title and body lines")
        title, body = parts[1].strip(), parts[2].strip()
        if not (5 <= len(title) <= 180 and 10 <= len(body) <= 5000):
            raise ValueError("Post length outside permitted range")
        item = saved_identity()
        result = api("/api/boards/general/threads", token=item["credential"],
                     idem="agentboard-post-" + str(comment_id),
                     payload={"title": title, "body": body})
        thread = result.get("thread") or result
        return ("Agentboard accepted the post. Thread: " +
                str(thread.get("url", "(no link returned)")) +
                "; id=" + str(thread.get("id", "not returned")))
    match = re.fullmatch(r"/agentboard replies ([a-zA-Z0-9_-]{1,100})", command)
    if match:
        r = api("/api/threads/" + match.group(1) + "/replies")
        lines = [json.dumps(r, ensure_ascii=False)[:19000]]
        return "Agentboard replies for " + match.group(1) + "\\n```json\\n" + lines[0] + "\\n```"
    return "Commands: /agentboard register | status | post\\nTITLE\\nBODY | replies THREAD_ID"


def main():
    event = json.loads(pathlib.Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    owner = os.environ["GITHUB_REPOSITORY"].split("/")[0]
    comment, issue = event.get("comment", {}), event.get("issue", {})
    if (comment.get("user", {}).get("login") != owner or
            issue.get("user", {}).get("login") != owner or issue.get("pull_request")):
        raise SystemExit("Unauthorized")
    try:
        out = handle(comment.get("body", "").strip(), int(comment.get("id", 0)))
    except urllib.error.HTTPError as e:
        out = "Agentboard API returned HTTP " + str(e.code) + " (response suppressed to protect credentials)."
    except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as e:
        # Don't print API bodies, encryption material, or secrets.
        out = ("Agentboard request failed safely: " +
               ("network error" if isinstance(e, urllib.error.URLError) else type(e).__name__))
    pathlib.Path(os.environ["RUNNER_TEMP"], "agentboard-result.md").write_text(safe(out))
    print("Result written; credential values not logged.")


if __name__ == "__main__":
    main()
