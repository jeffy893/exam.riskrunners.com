"""
bedrock_client.py — thin wrapper around Amazon Bedrock (Anthropic Claude) for
authoring exam-realistic actuarial problems.

CREDENTIALS: this module uses the standard AWS credential chain (environment
variables, ~/.aws/credentials, ~/.aws/config, SSO, instance role, etc.). It
NEVER reads or stores secrets in the repo. Configuration is read from a local
`.env` file (git-ignored) or the process environment. See `.env.example` for the
list of variables and defaults.

If Bedrock is unavailable (no credentials, no model access, network error,
boto3 not installed), callers should fall back to the deterministic template
generator in content_fm.py / content_p.py.
"""

import json
import os
import sys

# --------------------------------------------------------------------------
# Minimal .env loader (no external dependency). Loads KEY=VALUE lines from a
# local .env at the repo root, without overriding already-set env vars.
# --------------------------------------------------------------------------
def load_dotenv():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    path = os.path.join(root, ".env")
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


load_dotenv()

# Defaults chosen to match the account tested against; override via .env.
DEFAULT_REGION = os.environ.get("AWS_REGION") or os.environ.get(
    "AWS_DEFAULT_REGION", "us-west-2")
DEFAULT_MODEL = os.environ.get(
    "BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")


class BedrockUnavailable(Exception):
    """Raised when Bedrock cannot be used; callers fall back to templates."""


class BedrockClient:
    def __init__(self, region=None, model_id=None):
        self.region = region or DEFAULT_REGION
        self.model_id = model_id or DEFAULT_MODEL
        try:
            import boto3  # imported lazily so templates work without boto3
        except ImportError as e:
            raise BedrockUnavailable("boto3 is not installed") from e
        try:
            self._client = boto3.client("bedrock-runtime", region_name=self.region)
        except Exception as e:  # pragma: no cover - config errors
            raise BedrockUnavailable(f"could not create Bedrock client: {e}") from e

    def complete_json(self, system_prompt, user_prompt, max_tokens=4000,
                      temperature=0.8):
        """Invoke the model and return parsed JSON from its reply.

        Raises BedrockUnavailable on transport/permission errors so callers can
        fall back. Raises ValueError if the reply is not parseable JSON.
        """
        try:
            resp = self._client.converse(
                modelId=self.model_id,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                },
            )
        except Exception as e:
            raise BedrockUnavailable(f"Bedrock invocation failed: {e}") from e

        text = resp["output"]["message"]["content"][0]["text"]
        return _extract_json(text)

    def ping(self):
        """Cheap connectivity/permission check. Returns True or raises."""
        try:
            self._client.converse(
                modelId=self.model_id,
                messages=[{"role": "user", "content": [{"text": "Reply: OK"}]}],
                inferenceConfig={"maxTokens": 5, "temperature": 0},
            )
            return True
        except Exception as e:
            raise BedrockUnavailable(f"ping failed: {e}") from e


def _extract_json(text):
    """Pull a JSON object/array out of a model reply, tolerating code fences."""
    t = text.strip()
    if t.startswith("```"):
        # strip ```json ... ``` fences
        t = t.split("```", 2)
        t = t[1] if len(t) > 1 else text
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    t = t.strip().strip("`").strip()
    # find the outermost JSON bracketed region
    start = min([i for i in (t.find("{"), t.find("[")) if i != -1] or [-1])
    if start == -1:
        raise ValueError("no JSON found in model reply")
    # try to load progressively from the first bracket
    for end in range(len(t), start, -1):
        chunk = t[start:end]
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            continue
    raise ValueError("could not parse JSON from model reply")
