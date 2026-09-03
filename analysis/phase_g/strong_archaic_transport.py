"""Single-dispatch OpenRouter adapter; offline MockTransport tests only so far.

No environment/credential-file reads, no implicit retries, no executable entry
point. Must be called INSIDE Journal.call after durable reservation. Construction
of this object requires an explicit approval flag and separately verified route.
The shipped execution plan has neither current approval nor verified cost bounds.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_CEILING

import httpx

from analysis.phase_g.strong_archaic_runtime import Stop, MODELS


class SingleDispatchTransport:
    def __init__(self, *, api_key, approved, routes, provider_names=None, client=None):
        if approved is not True or not api_key or not routes or any(not r for r in routes.values()):
            raise Stop("separate paid approval, credentials and verified pinned routes required")
        if not set(routes) <= set(MODELS.values()):
            raise Stop("construction transport cannot enable a target model")
        self.api_key = api_key
        self.routes = routes
        self.provider_names = provider_names or {m: r for m,r in routes.items()}
        if set(self.provider_names) != set(routes) or any(not n for n in self.provider_names.values()):
            raise Stop("pinned provider display names required for every route")
        # HTTPTransport defaults to retries=0. Explicit no redirects, timeout120.
        self.client = client or httpx.Client(transport=httpx.HTTPTransport(retries=0),
                                            timeout=120, follow_redirects=False, trust_env=False)
        self.owns_client = client is None

    def close(self):
        if self.owns_client: self.client.close()

    def __call__(self, job, request):
        model = request["model"]
        route = self.routes.get(model)
        provider = request.get("provider", {})
        if (not route or provider.get("order") != [route] or provider.get("only") != [route] or provider.get("allow_fallbacks") is not False
                or provider.get("require_parameters") is not True or request.get("stream") is not False):
            raise Stop("transport request routing must match verified frozen route")
        # A client job ID header is diagnostic ONLY, not server idempotency.
        reply = self.client.post("https://openrouter.ai/api/v1/chat/completions",
                                 headers={"Authorization": f"Bearer {self.api_key}",
                                          "X-Client-Request-ID": job},
                                 json=request, timeout=120, follow_redirects=False)
        # Never log request headers or request object with embedded authentication.
        result = {"status": "delivery_unknown", "http_status": reply.status_code,
                  "raw_body": reply.text, "model": model,
                  "response_headers": {k: reply.headers[k] for k in ("x-request-id", "date", "retry-after") if k in reply.headers}}
        try:
            raw = reply.json()
        except ValueError:
            return result  # journal saves body and quarantines full reservation
        if not isinstance(raw, dict): return result
        usage = raw.get("usage")
        result.update(request_id=raw.get("id") or reply.headers.get("x-request-id"),
                      provider=raw.get("provider"), model=raw.get("model", model),
                      service_tier=raw.get("service_tier"), usage=usage, content="", finish_reason=None)
        # Even HTTP 4xx/429/5xx are not presumed free. Without explicit cost metadata
        # they remain unresolved until separately reconciled with provider records.
        if isinstance(usage, dict) and usage.get("cost") is not None:
            try:
                amount = Decimal(str(usage["cost"]))
                if amount.is_finite() and amount >= 0:
                    result["billed_nusd"] = int((amount * 1_000_000_000).to_integral_value(rounding=ROUND_CEILING))
            except (ValueError, ArithmeticError):
                pass
        choices = raw.get("choices")
        if 200 <= reply.status_code < 300 and isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict) and isinstance(first.get("message"), dict):
                # Never treat hidden reasoning as the final structured answer.
                content = first["message"].get("content")
                if isinstance(content, str):
                    result.update(status="ok", content=content, finish_reason=first.get("finish_reason"))
        elif raw.get("error"):
            result["status"] = "error"
            result["definitely_unbilled"] = result.get("billed_nusd") == 0
        # Provider mismatch is evidence, not an automatic request to another route.
        if result.get("provider") != self.provider_names[model]:
            result["status"] = "provider_mismatch"
        elif request.get("service_tier") == "flex" and raw.get("service_tier") != "flex":
            # Do not silently keep paying standard rates. The ledger reserves
            # standard rates, saves the billed result, then quarantines for review.
            result["status"] = "service_tier_mismatch"
        return result
