import json, time, urllib.request, os

with open(os.path.expanduser('~/.claude/settings.json')) as f:
    TOKEN = json.load(f)['env']['ANTHROPIC_AUTH_TOKEN']

BASE = "https://api.deepseek.com/v1/chat/completions"
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

# Long system prompt (~500+ tokens) to exceed possible cache threshold
SYSTEM = """You are Claude, an AI assistant specialized in film directing and cinematography.

Your expertise covers:
1. Camera positioning and shot composition based on Arijon's triangle principle
2. Camera movement design with 7-DOF model (pan, tilt, roll, track, boom, dolly, zoom)
3. Lighting design following 3-point lighting methodology
4. Color theory and color temperature for emotional impact
5. Scene coverage strategies for dialogue, action, and suspense sequences
6. Murch's six criteria for editing decisions
7. Block's seven visual components for visual storytelling
8. Performance direction with anatomical precision

Key principles you follow:
- KB rules always take priority over free judgment (Constitution Article Zero)
- Safety and quality override efficiency (Article One)
- User intent overrides system suggestions (Article Two)
- Block-level findings > Warning-level > Suggestion-level (Article Three)
- Independent verification overrides self-critique (Article Four)

You always reference specific KB rule IDs in your decisions.
You never describe things outside the frame.
You never use process verbs in keyframe descriptions.
You always provide structured YAML output alongside prose explanations."""

USER = "Design a single shot for a dialogue scene: two characters facing each other across a table in a dimly lit room."

def call(question, label):
    body = {
        "model": "deepseek-v4-flash",
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question}
        ],
    }
    req = urllib.request.Request(BASE, data=json.dumps(body).encode(), headers=HEADERS, method="POST")
    resp = urllib.request.urlopen(req, timeout=60)
    data = json.loads(resp.read().decode())
    usage = data.get("usage", {})

    hit = usage.get("prompt_cache_hit_tokens", 0)
    miss = usage.get("prompt_cache_miss_tokens", 0)
    total = usage.get("prompt_tokens", 0)
    cached = usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)

    # Check for thinking/reasoning tokens
    reasoning = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)

    print(f"[{label}] prompt={total}  cache_hit={hit}  cache_miss={miss}  "
          f"cached_details={cached}  reasoning={reasoning}")
    return usage

print("=" * 60)
print("DeepSeek V4 Flash - Long Prompt Cache Test")
print(f"System prompt: ~{len(SYSTEM)//4} tokens")
print("=" * 60)

print("\n--- Round 1: identical requests (thinking OFF) ---")
r1 = call(USER, "T1-1st")
time.sleep(3)
r2 = call(USER, "T2-2nd(identical)")

print("\n--- Round 2: same system, different Q ---")
time.sleep(3)
r3 = call("Design a shot for an action chase scene in a narrow alley.", "T3-different-Q")

print("\n--- Round 3: with thinking enabled ---")
time.sleep(3)
body_think = {
    "model": "deepseek-v4-flash",
    "max_tokens": 256,
    "messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": USER}
    ],
    "thinking": {"type": "enabled"},
}
req = urllib.request.Request(BASE, data=json.dumps(body_think).encode(), headers=HEADERS, method="POST")
resp = urllib.request.urlopen(req, timeout=60)
data = json.loads(resp.read().decode())
usage = data.get("usage", {})
hit = usage.get("prompt_cache_hit_tokens", 0)
miss = usage.get("prompt_cache_miss_tokens", 0)
reasoning = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
print(f"[T4-thinking] prompt={usage.get('prompt_tokens',0)}  cache_hit={hit}  cache_miss={miss}  reasoning={reasoning}")

print()
if r2.get("prompt_cache_hit_tokens", 0) > 0:
    rate = r2["prompt_cache_hit_tokens"] / (r2["prompt_cache_hit_tokens"] + r2["prompt_cache_miss_tokens"]) * 100
    print(f">>> CACHE WORKS! Hit rate: {rate:.0f}% (threshold met with longer prompt)")
elif r3.get("prompt_cache_hit_tokens", 0) > 0:
    print(">>> Prefix cache: only works with identical system (different Q = miss)")
else:
    print(">>> STILL NO CACHE - even with ~"+str(len(SYSTEM)//4)+" token system prompt")
    print("    DeepSeek V4 Flash may not have prompt caching at all on this endpoint")
