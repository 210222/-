import json, time, urllib.request, os

with open(os.path.expanduser('~/.claude/settings.json')) as f:
    TOKEN = json.load(f)['env']['ANTHROPIC_AUTH_TOKEN']

BASE = "https://api.deepseek.com/anthropic/v1/messages"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
    "anthropic-version": "2023-06-01",
}

SYSTEM = """You are an AI assistant specialized in film directing and cinematography.
Your expertise covers camera positioning, shot composition, lighting design,
color theory, scene coverage strategies, and performance direction.
You always follow KB rules and provide structured output.
You reference specific rule IDs in your decisions.
You never describe things outside the frame.
You always answer in exactly one sentence."""

USER = "Design a single shot for a dialogue scene: two characters facing each other across a table."

def call(system, user_msg, label):
    body = json.dumps({
        "model": "deepseek-v4-flash",
        "max_tokens": 128,
        "system": [{"type": "text", "text": system}],
        "messages": [{"role": "user", "content": user_msg}],
    }).encode()
    req = urllib.request.Request(BASE, data=body, headers=HEADERS, method="POST")
    t0 = time.time()
    resp = urllib.request.urlopen(req, timeout=30)
    elapsed = time.time() - t0
    data = json.loads(resp.read().decode())
    usage = data.get("usage", {})
    inp = usage.get("input_tokens", 0)
    cc = usage.get("cache_creation_input_tokens", 0)
    cr = usage.get("cache_read_input_tokens", 0)
    print(f"[{label}] {elapsed:.2f}s | input={inp} create={cc} read={cr} | stop={data.get('stop_reason','?')}")
    return usage

print("=" * 60)
print("Anthropic Endpoint - Long Prompt Cache Test")
print(f"System: ~{len(SYSTEM)//4} tokens")
print("=" * 60)

# Test 1: identical x 2
print("\n--- Round 1: identical ---")
u1 = call(SYSTEM, USER, "T1-first")
time.sleep(3)
u2 = call(SYSTEM, USER, "T2-identical")

# Test 2: same system, diff user
print("\n--- Round 2: same system, new Q ---")
time.sleep(3)
u3 = call(SYSTEM, "Design an action chase scene in a narrow alley.", "T3-newQ")

# Test 3: back to original (prefix should still be cached)
print("\n--- Round 3: back to original Q (system prefix cached?) ---")
time.sleep(3)
u4 = call(SYSTEM, USER, "T4-back-to-original")

print()
print("=" * 60)
for label, u in [("T1-first", u1), ("T2-identical", u2), ("T3-newQ", u3), ("T4-back", u4)]:
    cr = u.get("cache_read_input_tokens", 0)
    cc = u.get("cache_creation_input_tokens", 0)
    inp = u.get("input_tokens", 0)
    print(f"  {label:15s} in={inp:>5} create={cc:>5} read={cr:>5}  {'HIT' if cr>0 else 'MISS'}")

if u2.get("cache_read_input_tokens", 0) > 0:
    print("\n>>> Anthropic endpoint CACHE WORKS (my earlier test failed due to 22-token threshold)")
elif u3.get("cache_read_input_tokens", 0) > 0:
    print("\n>>> Prefix caching works (system prefix hit on different question)")
else:
    print("\n>>> Anthropic endpoint still no cache even with longer prompt")
