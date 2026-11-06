# Kaggle MCP and API Integration Setup Guide

DRIFTGUARD integrates directly with Kaggle via:
1. **Remote MCP Server:** `https://www.kaggle.com/mcp`
2. **Kaggle Official Python API:** `kaggle.api.kaggle_api_extended`

---

## 1. Accept Competition Rules (Mandatory)

Kaggle competitions require accepting terms of use before any data can be downloaded:

1. Open your browser and navigate to:
   [https://www.kaggle.com/competitions/ieee-fraud-detection/rules](https://www.kaggle.com/competitions/ieee-fraud-detection/rules)
2. Log in to your Kaggle account.
3. Review the rules and click **"Understand and Accept"**.

---

## 2. Obtain Kaggle Authentication Token

To protect your privacy and credentials, **never paste your secret token into chat or commit it to Git**.

1. Navigate to your [Kaggle Account Settings](https://www.kaggle.com/settings).
2. Scroll to the **API** section.
3. Click **"Create New Token"**.
4. This downloads a file named `kaggle.json` containing:
   ```json
   {"username": "your_kaggle_username", "key": "your_secret_api_key"}
   ```
5. Place this file in your user directory:
   - **Windows:** `C:\Users\<YourUser>\.kaggle\kaggle.json`
   - (For this workstation: `C:\Users\ldevi\.kaggle\kaggle.json`)

---

## 3. Remote MCP Server Configuration

Antigravity is pre-configured with the remote Kaggle MCP server in:
`~/.gemini/config/mcp_config.json`

```json
{
  "mcpServers": {
    "kaggle": {
      "url": "https://www.kaggle.com/mcp"
    }
  }
}
```

If you prefer to authenticate the MCP HTTP endpoint directly with a personal token:
1. Copy your Kaggle Personal Access Token (starts with `KGAT_` from Account Settings).
2. Add the `headers` field to `mcp_config.json`:
   ```json
   {
     "mcpServers": {
       "kaggle": {
         "url": "https://www.kaggle.com/mcp",
         "headers": {
           "Authorization": "Bearer KGAT_your_token_here"
         }
       }
     }
   }
   ```

---

## 4. Automatic Download Execution

Once `kaggle.json` is in place, execute the automated downloader:

```powershell
python scripts/download_ieee_cis.py
```

This will automatically:
- Query competition metadata from Kaggle MCP.
- Download `ieee-fraud-detection.zip`.
- Extract `train_transaction.csv`, `train_identity.csv`, and test files to `data/raw/ieee_cis/`.
- Validate file sizes and readability.

