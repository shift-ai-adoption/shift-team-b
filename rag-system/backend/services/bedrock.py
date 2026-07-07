"""AWS Bedrock clients: Titan embedding + Claude LLM."""
import json
import os

import boto3

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
EMBED_MODEL_ID = os.environ.get("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
LLM_MODEL_ID = os.environ.get(
    "LLM_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")

EMBED_DIM = 1024

_client = boto3.client("bedrock-runtime", region_name=REGION)


def embed_text(text: str) -> list[float]:
    """Return a 1024-dim embedding for the given text."""
    body = json.dumps({"inputText": text[:8000], "dimensions": EMBED_DIM})
    resp = _client.invoke_model(modelId=EMBED_MODEL_ID, body=body)
    return json.loads(resp["body"].read())["embedding"]


def embed_texts(texts: list[str]) -> list[list[float]]:
    return [embed_text(t) for t in texts]


def generate_answer(query: str, contexts: list[dict],
                    template_structure: str | None = None) -> tuple[str, str]:
    """Ask Claude to answer using retrieved contexts.

    Returns (answer, full_prompt) so the prompt can be stored in history.
    """
    ctx_lines = []
    for i, c in enumerate(contexts, 1):
        ctx_lines.append(
            f"[文書{i}] ファイル名: {c.get('filename')} (v{c.get('version')})\n"
            f"{c.get('content')}")
    ctx_block = "\n\n".join(ctx_lines) if ctx_lines else "(該当文書なし)"

    structure = template_structure or "簡潔で正確な日本語で回答する。"
    prompt = (
        "あなたは社内文書検索アシスタントです。以下の参照文書のみに基づいて"
        "ユーザの質問に日本語で回答してください。参照文書に情報がない場合は"
        "「参照文書に該当する情報がありません」と答えてください。\n\n"
        f"## 出力形式の指示\n{structure}\n\n"
        f"## 参照文書\n{ctx_block}\n\n"
        f"## 質問\n{query}"
    )
    resp = _client.converse(
        modelId=LLM_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 2000, "temperature": 0.2},
    )
    answer = resp["output"]["message"]["content"][0]["text"]
    return answer, prompt
