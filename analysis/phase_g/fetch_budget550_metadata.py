"""Fetch PUBLIC, unauthenticated OpenRouter model metadata only, never inference.

No bank, source text, responses, credentials or .env is read. GET URLs are a
closed list. No chat/completions, POST, redirects or implicit retries permitted.
The new snapshot is write-once; reruns read it unless a new directory is chosen
in a reviewed code change. This is not part of the inference controller.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

MODELS = ("google/gemini-2.5-flash", "deepseek/deepseek-v4-flash", "openai/gpt-5-mini",
          "qwen/qwen3-30b-a3b-instruct-2507", "openai/gpt-oss-20b", "nvidia/nemotron-3-nano-30b-a3b")
OUT = Path(__file__).resolve().parent / "u_arch_v3_budget550/provider_metadata"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = []
    with httpx.Client(timeout=30, follow_redirects=False, transport=httpx.HTTPTransport(retries=0), trust_env=False) as client:
        for model in MODELS:
            path = OUT / (model.replace("/", "__") + ".json")
            if path.exists():
                snapshot = json.loads(path.read_text(encoding="utf-8"))
            else:
                url = f"https://openrouter.ai/api/v1/models/{model}/endpoints"
                response = client.get(url)
                response.raise_for_status()
                raw = response.content
                body = response.json()
                assert body["data"]["id"] == model
                snapshot = dict(url=url, method="GET", authentication=False, research_data_sent=False,
                                fetched_at_utc=datetime.now(timezone.utc).isoformat(), status=response.status_code,
                                response_sha256=hashlib.sha256(raw).hexdigest(), response_text=response.text)
                with path.open("x", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(snapshot, indent=2, ensure_ascii=False)+"\n")
            data = json.loads(snapshot["response_text"])["data"]
            index.append({"model": model, "context": data.get("context_length"),
                          "endpoints": [{k:e.get(k) for k in ("provider_name", "tag", "pricing", "context_length", "max_completion_tokens", "supported_parameters", "status")}
                                        for e in data["endpoints"]]})
        catalog = OUT / "selected_catalog.json"
        if not catalog.exists():
            url = "https://openrouter.ai/api/v1/models"
            response = client.get(url)
            response.raise_for_status()
            selected = {x["id"]:x for x in response.json()["data"] if x["id"] in MODELS}
            assert set(selected) == set(MODELS)
            snapshot = dict(url=url, method="GET", authentication=False, research_data_sent=False,
                            fetched_at_utc=datetime.now(timezone.utc).isoformat(), status=response.status_code,
                            complete_response_sha256=hashlib.sha256(response.content).hexdigest(),
                            filtered_to_requested_models=True, selected_models=selected)
            with catalog.open("x",encoding="utf-8",newline="\n") as handle:
                handle.write(json.dumps(snapshot,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"model_endpoint_snapshots":len(index),"selected_catalog_saved":True,
                      "inference_calls":0,"research_data_sent":False}))


if __name__ == "__main__":
    main()
