"""
即梦AI (Jimeng AI) API Helper — uses volcengine SDK for proper V4 signing.

Two auth methods:
  1. Environment variables: VOLC_ACCESSKEY, VOLC_SECRETKEY (+ optional VOLC_SESSION_TOKEN)
  2. Direct: pass ak, sk to JimengAI(ak, sk)

Usage:
    from src.api_helper import JimengAI
    ai = JimengAI()  # reads env vars
    task_id = ai.submit_text_to_image("a cute cat")
    result = ai.wait_for_result(task_id, "jimeng_t2i_v31")
    print(result.get("image_urls"))
"""
import json
import os
import time
from urllib.parse import urlencode

import requests

# Use the SDK's proven signer
from volcenginesdkcore.signv4 import SignerV4


class JimengAI:
    """Jimeng AI API client with Volcengine V4 Signature."""

    ENDPOINT = "https://visual.volcengineapi.com"
    REGION = "cn-north-1"
    SERVICE = "cv"

    def __init__(self, access_key: str = None, secret_key: str = None, session_token: str = None):
        self.access_key = access_key or os.environ.get("VOLC_ACCESSKEY", "")
        self.secret_key = secret_key or os.environ.get("VOLC_SECRETKEY", "")
        self.session_token = session_token or os.environ.get("VOLC_SESSION_TOKEN", "")

        if not self.access_key or not self.secret_key:
            raise ValueError(
                "Credentials required. Set VOLC_ACCESSKEY and VOLC_SECRETKEY "
                "environment variables, or pass ak/sk to JimengAI()."
            )

    def _request(self, action: str, body: dict) -> dict:
        qs = {"Action": action, "Version": "2022-08-31"}
        url = f"{self.ENDPOINT}?{urlencode(qs)}"

        payload = json.dumps(body, ensure_ascii=False)
        headers = {"Content-Type": "application/json", "Host": "visual.volcengineapi.com"}

        SignerV4.sign(
            "/", "POST", headers, payload, {},
            qs, self.access_key, self.secret_key,
            self.REGION, self.SERVICE, self.session_token or None,
        )

        resp = requests.post(url, headers=headers, data=payload, timeout=120)
        return resp.json()

    # ── Public API ──────────────────────────────────────────

    def submit_text_to_image(self, prompt: str, width: int = 1328,
                             height: int = 1328, seed: int = -1,
                             use_pre_llm: bool = True) -> str:
        body = {
            "req_key": "jimeng_t2i_v31",
            "prompt": prompt,
            "seed": seed,
            "width": width,
            "height": height,
            "use_pre_llm": use_pre_llm,
        }
        result = self._request("CVSync2AsyncSubmitTask", body)
        code = result.get("code")
        if code != 10000:
            raise RuntimeError(f"T2I submit failed: code={code}, msg={result.get('message')}, "
                               f"detail={result.get('ResponseMetadata',{}).get('Error',{})}")
        return result["data"]["task_id"]

    def submit_video_first_last(self, first_image_url: str, last_image_url: str,
                                prompt: str, seed: int = -1, seconds: int = 5) -> str:
        frames = 121 if seconds == 5 else 241
        body = {
            "req_key": "jimeng_i2v_first_tail_v30_1080",
            "image_urls": [first_image_url, last_image_url],
            "prompt": prompt,
            "seed": seed,
            "frames": frames,
        }
        result = self._request("CVSync2AsyncSubmitTask", body)
        code = result.get("code")
        if code != 10000:
            raise RuntimeError(f"Video submit failed: code={code}, msg={result.get('message')}")
        return result["data"]["task_id"]

    def get_result(self, task_id: str, req_key: str, return_url: bool = True) -> dict:
        body = {"req_key": req_key, "task_id": task_id}
        if return_url and req_key == "jimeng_t2i_v31":
            body["req_json"] = json.dumps({"return_url": True}, ensure_ascii=False)
        result = self._request("CVSync2AsyncGetResult", body)
        code = result.get("code")
        if code != 10000:
            return {"status": "error", "message": result.get("message")}
        return result["data"]

    def wait_for_result(self, task_id: str, req_key: str,
                        poll_interval: int = 5, max_wait: int = 300) -> dict:
        start = time.time()
        while time.time() - start < max_wait:
            data = self.get_result(task_id, req_key)
            status = data.get("status", "unknown")
            if status == "done":
                return data
            if status in ("not_found", "expired"):
                return {"status": status, "message": f"Task {status}"}
            time.sleep(poll_interval)
        return {"status": "timeout", "message": f"Exceeded max wait {max_wait}s"}
