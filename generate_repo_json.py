#!/usr/bin/env python3
from pathlib import Path
import json, os, hashlib

owner = os.getenv("GITHUB_REPOSITORY", "sheep0614-Lin/Sheep-manga")
fingerprint = os.getenv("SIGNING_KEY_FINGERPRINT", "REPLACE_WITH_SHA256_FINGERPRINT").lower().replace(":", "")

repo = {
    "index_v2": f"https://raw.githubusercontent.com/{owner}/main/repo/index.pb",
    "meta": {
        "name": "Sheep Manga",
        "website": f"https://github.com/{owner}",
        "signingKeyFingerprint": fingerprint
    }
}
Path("repo").mkdir(exist_ok=True)
Path("repo/repo.json").write_text(json.dumps(repo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(repo, ensure_ascii=False, indent=2))
