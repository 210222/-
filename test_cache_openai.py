import json, time, urllib.request, os

with open(os.path.expanduser('~/.claude/settings.json')) as f:
    TOKEN = json.load(f)['env']['ANTHROPIC_AUTH_TOKEN']

BASE = "https://api.deepseek.com/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}

SYSTEM = "You are a test assistant. Answer in one sentence."

def call(question, label, use_thinking=False):
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    body = {
        "model": "deepseek-v4-flash",
        "max_tokens": 128,
        "messages": msgs,
    }
    if use_thinking:
        body["thinking"] = {"type": "enabled"}

    req = urllib.request.Request(BASE, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    usage = data.get("usage", {})

    # OpenAI format uses different field names
    # DeepSeek might return prompt_tokens_details for cache info
    details = usage.get("prompt_tokens_details", {})
    cr = details.get("cache_creation_tokens", usage.get("cache_creation_input_tokens", 0))
    rd = details.get("cache_read_tokens", usage.get("cache_read_input_tokens", 0))
    total = usage.get("prompt_tokens", usage.get("input_tokens", 0))

    print(f"[{label}] total={total}  cache_create={cr}  cache_read={rd}  "
          f"full_usage_keys={list(usage.keys())}")
    return usage

print("=" * 60)
print("DeepSeek V4 Flash - OpenAI Endpoint Cache Test")
print("=" * 60)

print("\n--- Round 1: no thinking ---")
r1 = call("What is the capital of France?", "T1-noThink-1st")
time.sleep(2)
r2 = call("What is the capital of France?", "T2-noThink-2nd")

print("\n--- Round 2: with thinking ---")
time.sleep(2)
r3 = call("What is the capital of France?", "T3-thinking-1st", use_thinking=True)
time.sleep(2)
r4 = call("What is the capital of France?", "T4-thinking-2nd", use_thinking=True)

print("\n--- Round 3: different question (prefix test) ---")
time.sleep(2)
r5 = call("What is the capital of Japan?", "T5-noThink-newQ")

print(f"\n>>> OpenAI endpoint full usage sample: {json.dumps(r1, indent=2)}")
