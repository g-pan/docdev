from pathlib import Path

import requests

SOURCE_URL = "http://172.190.97.122/OBT/summary.html"
OUTPUT_PATH = Path(__file__).resolve().parent / "summary.html"


def main() -> None:
    try:
        response = requests.get(SOURCE_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise SystemExit(f"Failed to download summary from {SOURCE_URL}: {exc}") from exc

    OUTPUT_PATH.write_text(response.text, encoding="utf-8", newline="\n")
    print(f"Summary downloaded successfully to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()