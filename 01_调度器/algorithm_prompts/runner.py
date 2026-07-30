#!/usr/bin/env python3
"""
MODE:P 算法设计提示词 → DeepSeek V4 Pro / V4 Flash 执行器
用法: python runner.py [A1|A2|A3|A4|A5|A6|A7|A8|all] [--model pro|flash]
      python runner.py A1 --model flash   # 用 Flash 跑 A1
      python runner.py all --model flash  # 全部用 Flash

模型选择策略 (v1.0):
  Pro (deepseek-v4-pro):  深度推理·thinking=ON·低温度 → A1,A2,A3,A5,A7,A8
  Flash (deepseek-v4-flash): 确定性·thinking=OFF / 简单推理 → A4,A6
                           也可用于 A1-A8 的迭代/重跑 (成本 1/3)
"""
import os, sys, json, time
from openai import OpenAI

API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-xxxxxxxx")
BASE_URL = "https://api.deepseek.com"

PROMPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── 模型配置 ─────────────────────────────────────────

MODELS = {
    "pro": {
        "id": "deepseek-v4-pro",
        "input_price_per_mtok": 0.435,
        "output_price_per_mtok": 0.87,
        "cache_hit_price_per_mtok": 0.003625,
    },
    "flash": {
        "id": "deepseek-v4-flash",
        "input_price_per_mtok": 0.14,
        "output_price_per_mtok": 0.28,
        "cache_hit_price_per_mtok": 0.0028,
    },
}

# ─── 任务定义 + 推荐模型路由 ──────────────────────────

TASKS = {
    "A1": {"file": "A1_shot_classifier_redesign.md",
           "thinking": True, "temperature": 0.1, "max_tokens": 16000,
           "recommended_model": "pro",   # 深度推理·4类失败模式分析
           "fallback_model": "flash"},   # 迭代/重跑可用Flash省钱
    "A2": {"file": "A2_intent_mapper_redesign.md",
           "thinking": True, "temperature": 0.1, "max_tokens": 20000,
           "recommended_model": "pro",   # 最复杂节点·信息损失补偿
           "fallback_model": "flash"},
    "A3": {"file": "A3_performance_matcher_upgrade.md",
           "thinking": True, "temperature": 0.1, "max_tokens": 12000,
           "recommended_model": "pro",
           "fallback_model": "flash"},
    "A4": {"file": "A4_script_assembler_review.md",
           "thinking": False, "temperature": 0.0, "max_tokens": 8000,
           "recommended_model": "flash",  # 纯逻辑·不需要深度推理
           "fallback_model": "pro"},
    "A5": {"file": "A5_intent_strategies_redesign.md",
           "thinking": True, "temperature": 0.1, "max_tokens": 16000,
           "recommended_model": "pro",
           "fallback_model": "flash"},
    "A6": {"file": "A6_gate0_scanner.md",
           "thinking": False, "temperature": 0.0, "max_tokens": 8000,
           "recommended_model": "flash",  # 纯正则·零推理需求 → Flash 完美匹配
           "fallback_model": "pro"},
    "A7": {"file": "A7_confidence_calibration.md",
           "thinking": True, "temperature": 0.1, "max_tokens": 10000,
           "recommended_model": "pro",
           "fallback_model": "flash"},
    "A8": {"file": "A8_strategy_coverage_expansion.md",
           "thinking": True, "temperature": 0.1, "max_tokens": 10000,
           "recommended_model": "pro",
           "fallback_model": "flash"},
}

def estimate_cost(task_id, model_key, prompt_chars, output_chars):
    """估算单次调用的token成本"""
    model = MODELS[model_key]
    # 粗略估算: 中英混合 ~3.5 chars/token
    input_tokens = prompt_chars / 3.5
    output_tokens = output_chars / 3.5

    # 假设首轮无缓存 (cache miss)
    input_cost = (input_tokens / 1_000_000) * model["input_price_per_mtok"]
    output_cost = (output_tokens / 1_000_000) * model["output_price_per_mtok"]

    # 如果有缓存命中 (第2+次相同前缀)
    cache_hit_input_cost = (input_tokens / 1_000_000) * model["cache_hit_price_per_mtok"]

    return {
        "model": model["id"],
        "input_tokens_est": int(input_tokens),
        "output_tokens_est": int(output_tokens),
        "cost_first_call": input_cost + output_cost,
        "cost_cached_call": cache_hit_input_cost + output_cost,
    }


# ─── 缓存预热 ─────────────────────────────────────────

def warmup(task_id, model_key, warmup_rounds=3):
    """缓存预热：发送相同的极小请求 N 次，触发 DeepSeek 缓存落盘。

    DeepSeek 缓存三步落盘机制:
      1. 请求结束位置落盘 — 首次请求后在用户输入结束位置缓存
      2. 公共前缀检测落盘 — 2-3 次请求后系统自动检测公共前缀并单独缓存
      3. 固定 token 间隔落盘 — 长输入按间隔截取

    关键约束 (来自官方文档):
      - enable_thinking 是缓存 key 的一部分 — thinking=ON/OFF 的缓存互不共享
      - temperature 也是缓存 key 的一部分 — 必须与实际调用完全一致
      - 缓存是前缀匹配 — 从第0个token开始必须完全相同

    预热策略:
      - thinking=OFF: max_tokens=1 (最小输出·触发落盘·成本可忽略)
      - thinking=ON:  max_tokens=512 (需给推理留空间·否则 reasoning overflow 导致空输出)
      - 3轮预热触发: 请求结束落盘 + 缓存验证 + 公共前缀检测落盘

    Pro 成本: 3 × (input + ~300 reasoning) ≈ $0.01 (vs 实际调用 $0.02-0.05)
    Flash 成本: 3 × 1 output ≈ $0.000001
    """
    task = TASKS[task_id]
    if model_key is None:
        model_key = task["recommended_model"]
    model = MODELS[model_key]

    prompt_path = os.path.join(PROMPT_DIR, task["file"])
    if not os.path.exists(prompt_path):
        print(f"   ❌ 找不到预热文件: {prompt_path}")
        return False

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    prompt_tokens_est = len(prompt) // 4

    # thinking=ON 需要足够空间给推理链, thinking=OFF 只需1 token
    warmup_max_tokens = 512 if task["thinking"] else 1
    think_label = "thinking=ON" if task["thinking"] else "thinking=OFF"

    print(f"   🔥 缓存预热 {task_id} → {model['id']} ({think_label}) "
          f"{warmup_rounds}轮·max_tokens={warmup_max_tokens}·~{prompt_tokens_est} tokens/轮")

    hits = 0
    for round_num in range(1, warmup_rounds + 1):
        response = client.chat.completions.create(
            model=model["id"],
            messages=[{"role": "user", "content": prompt}],
            temperature=task["temperature"],
            max_tokens=warmup_max_tokens,
            extra_body={"enable_thinking": task["thinking"]},
        )

        usage = response.usage
        hit_tokens = getattr(usage, 'prompt_cache_hit_tokens', 0) or 0
        miss_tokens = getattr(usage, 'prompt_cache_miss_tokens', 0) or 0
        total = getattr(usage, 'prompt_tokens', 0) or 0
        reasoning = getattr(usage, 'completion_tokens_details', None)
        reasoning_tokens = getattr(reasoning, 'reasoning_tokens', 0) if reasoning else 0

        if hit_tokens > 0:
            hits += 1
            rate = hit_tokens / (hit_tokens + miss_tokens) * 100 if (hit_tokens + miss_tokens) > 0 else 0
            print(f"     第{round_num}轮: ✅ HIT {hit_tokens}/{total}t ({rate:.0f}%)"
                  f"{'·reasoning='+str(reasoning_tokens) if reasoning_tokens else ''}")
        else:
            print(f"     第{round_num}轮: ❌ MISS {miss_tokens}/{total}t (首次写入)"
                  f"{'·reasoning='+str(reasoning_tokens) if reasoning_tokens else ''}")

        if round_num < warmup_rounds:
            time.sleep(2)

    if hits >= warmup_rounds - 1:
        print(f"   ✅ {task_id} 缓存预热完成 ({hits}/{warmup_rounds}轮命中)")
        return True
    elif hits > 0:
        print(f"   ⚠️  {task_id} 缓存部分命中 ({hits}/{warmup_rounds}轮)")
        return True
    else:
        print(f"   ⚠️  {task_id} 缓存未命中 (检查: thinking/temperature/model是否与实际调用一致)")
        return False


# ─── 缓存统计 ─────────────────────────────────────────

class CacheStats:
    """跨任务缓存统计"""
    def __init__(self):
        self.total_hit = 0
        self.total_miss = 0
        self.calls = 0

    def record(self, usage):
        hit = getattr(usage, 'prompt_cache_hit_tokens', 0) or 0
        miss = getattr(usage, 'prompt_cache_miss_tokens', 0) or 0
        self.total_hit += hit
        self.total_miss += miss
        self.calls += 1

    def summary(self):
        total = self.total_hit + self.total_miss
        if total == 0:
            return "无缓存数据"
        rate = self.total_hit / total * 100
        return (f"{self.calls}次调用 · 缓存命中{self.total_hit}/{total} tokens ({rate:.1f}%) "
                f"· 节省约{rate*0.9:.0f}%输入成本")

    def hit_rate(self):
        total = self.total_hit + self.total_miss
        return self.total_hit / total * 100 if total > 0 else 0


_cache_stats = CacheStats()


def run(task_id, model_key=None):
    """执行单个算法设计任务"""
    task = TASKS[task_id]

    # 模型选择: CLI参数 > 推荐模型
    if model_key is None:
        model_key = task["recommended_model"]
    model = MODELS[model_key]

    prompt_path = os.path.join(PROMPT_DIR, task["file"])

    if not os.path.exists(prompt_path):
        print(f"❌ 找不到: {prompt_path}")
        return

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()

    # ── 发送 ──
    print(f"📤 发送 {task_id} → {model['id']}")
    print(f"   thinking={task['thinking']} temp={task['temperature']} max_tokens={task['max_tokens']}")
    print(f"   提示词长度: {len(prompt)} 字符 ≈ {len(prompt)//4} tokens")
    if model_key != task["recommended_model"]:
        print(f"   ⚠️ 模型覆盖: 推荐={task['recommended_model']}·实际={model_key}")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    response = client.chat.completions.create(
        model=model["id"],
        messages=[{"role": "user", "content": prompt}],
        temperature=task["temperature"],
        max_tokens=task["max_tokens"],
        extra_body={"enable_thinking": task["thinking"]},
    )

    output = response.choices[0].message.content

    # ── 缓存统计 ──
    _cache_stats.record(response.usage)
    hit = getattr(response.usage, 'prompt_cache_hit_tokens', 0) or 0
    miss = getattr(response.usage, 'prompt_cache_miss_tokens', 0) or 0

    # ── 成本估算 ──
    cost = estimate_cost(task_id, model_key, len(prompt), len(output))
    reasoning_tokens = 0
    if hasattr(response.choices[0].message, 'reasoning_content') and response.choices[0].message.reasoning_content:
        reasoning_tokens = len(response.choices[0].message.reasoning_content) // 4

    # ── 保存输出 ──
    output_path = os.path.join(PROMPT_DIR, f"output_{task_id}.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    # ── 输出 ──
    cache_info = ""
    if hit > 0:
        rate = hit / (hit + miss) * 100 if (hit + miss) > 0 else 0
        cache_info = f" 🟢缓存命中{hit}t ({rate:.0f}%)"
    elif miss > 0:
        cache_info = f" 🔴缓存未命中{miss}t"
    print(f"✅ {task_id} 完成 · 输出: {output_path}{cache_info}")
    print(f"   输出长度: {len(output)} 字符")
    print(f"   💰 预估成本: 首轮 ${cost['cost_first_call']:.4f} · 缓存命中 ${cost['cost_cached_call']:.4f}")
    if reasoning_tokens > 0:
        print(f"   🧠 reasoning tokens: ~{reasoning_tokens}")

    # ── 质量检查 ──
    try:
        if "```json" in output:
            json_start = output.index("```json") + 7
            json_end = output.index("```", json_start)
            data = json.loads(output[json_start:json_end])
        elif output.strip().startswith("{"):
            data = json.loads(output)
        else:
            data = None

        if data:
            if "recommendation" in data:
                impl = data["recommendation"].get("full_implementation", "")
                candidates = data.get("candidates", [])
                print(f"   📊 候选数: {len(candidates)}")
                print(f"   📊 实现长度: {len(impl)} 字符")
                if len(candidates) < 3:
                    print(f"   ⚠️ 候选数不足 3 (AP-5 风险)")
            elif "full_implementation" in data:
                impl = data.get("full_implementation", "")
                print(f"   📊 实现长度: {len(impl)} 字符")
    except Exception:
        print(f"   ℹ️ 输出非 JSON 格式·手动检查")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MODE:P 算法设计 → DeepSeek V4 Pro / Flash",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python runner.py A1                  # 用推荐模型(Pro)跑A1
  python runner.py A1 --model flash    # 用Flash跑A1 (省成本)
  python runner.py A6 --model flash    # A6推荐就是Flash·纯正则不需要Pro
  python runner.py all --model flash   # 全部用Flash跑 (迭代/重跑场景)
  python runner.py all                 # 全部用推荐模型
  python runner.py --cost              # 显示所有任务的成本预估

模型路由策略:
  Pro:  A1,A2,A3,A5,A7,A8 (深度推理·thinking=ON·低温度)
  Flash: A4,A6 (确定性逻辑·thinking=OFF / 简单推理·成本1/3)
  缓存命中后 Flash 输入仅 $0.0028/M tokens
        """
    )
    parser.add_argument("task", nargs="?", default=None,
                        help="任务ID: A1-A8 或 all")
    parser.add_argument("--model", "-m", choices=["pro", "flash"], default=None,
                        help="模型选择 (默认: 使用推荐模型)")
    parser.add_argument("--warmup", "-w", action="store_true",
                        help="执行前先缓存预热 (3轮·触发DeepSeek前缀缓存落盘)")
    parser.add_argument("--warmup-only", action="store_true",
                        help="仅缓存预热·不执行实际任务")
    parser.add_argument("--warmup-rounds", type=int, default=3,
                        help="预热轮数 (默认3·最小2)")
    parser.add_argument("--cache-stats", action="store_true",
                        help="运行后显示缓存命中统计")
    parser.add_argument("--cost", action="store_true",
                        help="仅显示成本预估·不执行")
    args = parser.parse_args()

    if args.cost:
        print("💰 成本预估 (基于提示词文件大小·首轮·无缓存):")
        print(f"{'任务':<6} {'推荐模型':<8} {'提示词':>8} {'输入tokens':>10} {'首轮成本':>10} {'缓存成本':>10}")
        print("-" * 58)
        total_first = 0
        total_cached = 0
        for tid, task in TASKS.items():
            prompt_path = os.path.join(PROMPT_DIR, task["file"])
            if not os.path.exists(prompt_path):
                continue
            prompt_len = len(open(prompt_path, encoding="utf-8").read())
            cost = estimate_cost(tid, task["recommended_model"], prompt_len, task["max_tokens"] * 4)
            total_first += cost["cost_first_call"]
            total_cached += cost["cost_cached_call"]
            print(f"{tid:<6} {task['recommended_model']:<8} {prompt_len:>6}chars {cost['input_tokens_est']:>8}tok  ${cost['cost_first_call']:>8.4f}  ${cost['cost_cached_call']:>8.4f}")
        print("-" * 58)
        print(f"{'合计':<6} {'':<8} {'':>6} {'':>10}  ${total_first:>8.4f}  ${total_cached:>8.4f}")

        # Flash 对比
        print(f"\n💰 全部用 Flash 的成本:")
        total_flash_first = 0
        for tid, task in TASKS.items():
            prompt_path = os.path.join(PROMPT_DIR, task["file"])
            if not os.path.exists(prompt_path):
                continue
            prompt_len = len(open(prompt_path, encoding="utf-8").read())
            cost = estimate_cost(tid, "flash", prompt_len, task["max_tokens"] * 4)
            total_flash_first += cost["cost_first_call"]
        print(f"   全部Flash首轮: ${total_flash_first:.4f} (Pro的 {total_flash_first/total_first*100:.0f}%)")
        sys.exit(0)

    if args.task is None:
        parser.print_help()
        sys.exit(1)

    target = args.task.upper()

    # 确定要执行的任务列表
    if target == "ALL":
        task_list = ["A6", "A1", "A2", "A5", "A7", "A3", "A4", "A8"]
    elif target in TASKS:
        task_list = [target]
    else:
        print(f"❌ 未知任务: {target} · 可用: {list(TASKS.keys())}")
        sys.exit(1)

    # ── 缓存预热 ──
    if args.warmup or args.warmup_only:
        print("=" * 60)
        print("🔥 缓存预热阶段")
        print(f"   模型: {MODELS[args.model or 'pro']['id']}")
        print(f"   轮数: {args.warmup_rounds}")
        print("=" * 60)
        for tid in task_list:
            warmup(tid, model_key=args.model, warmup_rounds=args.warmup_rounds)
            print()
        if args.warmup_only:
            print("✅ 预热完成·跳过实际执行 (--warmup-only)")
            sys.exit(0)
        print("=" * 60)
        print("📤 开始实际执行")
        print("=" * 60)

    # ── 执行 ──
    for tid in task_list:
        run(tid, model_key=args.model)
        print()

    # ── 缓存统计 ──
    if args.cache_stats or args.warmup:
        print("=" * 60)
        print(f"📊 缓存统计: {_cache_stats.summary()}")
        print("=" * 60)
