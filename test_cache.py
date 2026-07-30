import json, time, urllib.request, os

with open(os.path.expanduser('~/.claude/settings.json')) as f:
    TOKEN = json.load(f)['env']['ANTHROPIC_AUTH_TOKEN']

BASE = "https://api.deepseek.com/anthropic/v1/messages"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "anthropic-version": "2023-06-01",
}

SYSTEM = "You are a test assistant. Answer in one sentence."

def call(question, label):
    body = json.dumps({
        "model": "deepseek-v4-flash",
        "max_tokens": 128,
        "system": [{"type": "text", "text": SYSTEM}],
        "messages": [{"role": "user", "content": question}],
    }).encode()
    req = urllib.request.Request(BASE, data=body, headers=HEADERS, method="POST")
    resp = urllib.request.urlopen(req, timeout=30)
    usage = json.loads(resp.read().decode())["usage"]
    cr = usage.get("cache_creation_input_tokens", 0)
    rd = usage.get("cache_read_input_tokens", 0)
    inp = usage.get("input_tokens", 0)
    print(f"[{label}] cache_create={cr}  cache_read={rd}  input={inp}")
    return usage

print("=== 相同请求 x 2 ===")
r1 = call("What is the capital of France?", "T1-首次")
time.sleep(2)
r2 = call("What is the capital of France?", "T2-重复")

print("=== 同system, 不同问题 ===")
time.sleep(2)
r3 = call("What is the capital of Japan?", "T3-新问题")

print()
if r2.get("cache_read_input_tokens", 0) > 0:
    rate = r2["cache_read_input_tokens"] / (r2["cache_read_input_tokens"] + r2.get("input_tokens", 1)) * 100
    print(f">>> 缓存有效！命中率 {rate:.0f}%")
elif r3.get("cache_read_input_tokens", 0) > 0:
    print(">>> 前缀缓存部分工作（同system前缀命中）")
else:
    print(">>> 缓存无效：三次请求 cache_read 均为 0")
