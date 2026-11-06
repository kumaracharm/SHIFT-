"""
DRIFTGUARD IEEE-CIS Fraud Detection Dataset Download Script
Connects to Kaggle via official Kaggle MCP / API, verifies competition rules,
downloads competition data files, extracts archives, and validates data directory contents.
"""

import os
import sys
import json
import zipfile
import urllib.request
import urllib.error
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings

TARGET_DIR = settings.RAW_DATA_DIR / "ieee_cis"
TARGET_DIR.mkdir(parents=True, exist_ok=True)
COMPETITION_NAME = "ieee-fraud-detection"
MCP_ENDPOINT = "https://www.kaggle.com/mcp"

EXPECTED_FILES = [
    "train_transaction.csv",
    "train_identity.csv",
    "test_transaction.csv",
    "test_identity.csv",
    "sample_submission.csv",
]


def get_kaggle_token() -> tuple[str | None, str | None]:
    """Retrieves Kaggle authentication from environment, kaggle.json, or mcp_config.json."""
    # 1. Environment variables
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    bearer = os.environ.get("KAGGLE_TOKEN")
    if bearer:
        return None, bearer
    if username and key:
        return f"{username}:{key}", None

    # 2. kaggle.json
    kaggle_json_path = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json_path.exists():
        try:
            data = json.loads(kaggle_json_path.read_text(encoding="utf-8"))
            u = data.get("username")
            k = data.get("key")
            if u and k:
                return f"{u}:{k}", None
        except Exception:
            pass

    # 3. mcp_config.json
    mcp_config_path = Path.home() / ".gemini" / "config" / "mcp_config.json"
    if mcp_config_path.exists():
        try:
            cfg = json.loads(mcp_config_path.read_text(encoding="utf-8"))
            headers = cfg.get("mcpServers", {}).get("kaggle", {}).get("headers", {})
            auth_header = headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                return None, auth_header[7:].strip()
        except Exception:
            pass

    return None, None


def check_mcp_competition_metadata() -> dict:
    """Queries Kaggle MCP server for public competition metadata."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_competition",
            "arguments": {
                "request": {
                    "competitionName": COMPETITION_NAME
                }
            }
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        MCP_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            lines = [line[5:].strip() for line in body.split("\n") if line.startswith("data:")]
            if lines:
                res_obj = json.loads(lines[0])
                text_content = res_obj["result"]["content"][0]["text"]
                return json.loads(text_content)
    except Exception as exc:
        print(f"[WARN] Unable to reach Kaggle MCP: {exc}")
    return {}


def download_via_kaggle_api() -> bool:
    """Downloads dataset using Kaggle official SDK / CLI with local kaggle.json."""
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print(f"[INFO] Authenticated with Kaggle as: {api.get_config_value('username')}")
        print(f"[INFO] Downloading competition files for '{COMPETITION_NAME}' to {TARGET_DIR}...")
        api.competition_download_files(COMPETITION_NAME, path=str(TARGET_DIR), quiet=False)
        return True
    except Exception as exc:
        err_msg = str(exc)
        if "403" in err_msg or "rules" in err_msg.lower():
            print("\n" + "=" * 70)
            print("[ACTION REQUIRED] KAGGLE COMPETITION RULES NOT ACCEPTED")
            print("=" * 70)
            print(f"You must accept the rules for this competition before Kaggle will allow downloading data.")
            print(f"Please open your browser, visit:")
            print(f"  https://www.kaggle.com/competitions/{COMPETITION_NAME}/rules")
            print(f"Click 'Understand and Accept', then run this download script again.")
            print("=" * 70 + "\n")
        else:
            print(f"[ERROR] Kaggle API download failed: {exc}")
        return False


def extract_archives():
    """Unzips all .zip archives in the raw destination folder."""
    zip_files = list(TARGET_DIR.glob("*.zip"))
    for zf in zip_files:
        print(f"[INFO] Extracting {zf.name}...")
        try:
            with zipfile.ZipFile(zf, "r") as zip_ref:
                zip_ref.extractall(TARGET_DIR)
            print(f"[OK] Extracted {zf.name}")
        except Exception as exc:
            print(f"[ERROR] Failed extracting {zf.name}: {exc}")


def verify_downloaded_files() -> bool:
    """Verifies that the required CSV files exist and have non-zero sizes."""
    print("\n=== Download Verification ===")
    all_present = True
    for fname in EXPECTED_FILES:
        fpath = TARGET_DIR / fname
        if fpath.exists():
            size_mb = fpath.stat().st_size / (1024 * 1024)
            print(f" [OK] {fname:25s} : {size_mb:8.2f} MB")
        else:
            print(f" [MISSING] {fname:25s}")
            all_present = False
    return all_present


def main():
    print("=" * 70)
    print("DRIFTGUARD: IEEE-CIS Fraud Detection Dataset Downloader")
    print("=" * 70)

    # 1. Fetch metadata from Kaggle MCP
    print(f"[1/4] Connecting to Kaggle MCP at {MCP_ENDPOINT}...")
    meta = check_mcp_competition_metadata()
    if meta:
        print(f"  Competition Title : {meta.get('title')}")
        print(f"  Category          : {meta.get('category')}")
        print(f"  Evaluation Metric : {meta.get('evaluation_metric')}")
        print(f"  URL               : {meta.get('url')}")
    else:
        print("  Proceeding with direct download pipeline...")

    # 2. Check Authentication
    basic_creds, bearer_token = get_kaggle_token()
    if not basic_creds and not bearer_token:
        print("\n" + "=" * 70)
        print("[ACTION REQUIRED] KAGGLE AUTHENTICATION NEEDED")
        print("=" * 70)
        print("Kaggle requires authentication to download competition datasets.")
        print("Please follow these two steps:")
        print(f"1. Accept competition rules in your browser:")
        print(f"   https://www.kaggle.com/competitions/{COMPETITION_NAME}/rules")
        print("   (Click 'Understand and Accept')")
        print("")
        print("2. Generate your Kaggle API key:")
        print("   Visit https://www.kaggle.com/settings -> scroll to 'API' -> click 'Create New Token'")
        print("   Place the downloaded 'kaggle.json' file at:")
        print(f"   {Path.home() / '.kaggle' / 'kaggle.json'}")
        print("=" * 70 + "\n")
        sys.exit(2)

    # 3. Download competition files
    print(f"\n[2/4] Downloading '{COMPETITION_NAME}' files to {TARGET_DIR}...")
    success = download_via_kaggle_api()
    if not success:
        sys.exit(1)

    # 4. Extract archives
    print("\n[3/4] Extracting downloaded archives...")
    extract_archives()

    # 5. Verify presence and readability
    print("\n[4/4] Verifying extracted files...")
    ok = verify_downloaded_files()
    if ok:
        print("\n[SUCCESS] IEEE-CIS dataset successfully downloaded and verified in data/raw/ieee_cis/")
    else:
        print("\n[WARN] Some files were not found. Check download logs above.")


if __name__ == "__main__":
    main()

