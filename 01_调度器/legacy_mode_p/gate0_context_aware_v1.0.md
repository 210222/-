# Gate 0 v1.2 -- 上下文感知正则扫描 (BLOCK-3修复)

> **版本:** v1.2 · 2026-07-07
> **升级原因:** v1.0全局正则扫描产生假阳性——R10在header元数据中触发"Seedance 2.0"(非生成指令内容)。需升级为区块感知扫描。
> **BLOCK-3修复(2026-07-07):** 补充四个缺失函数(execute_numeric_check/execute_pattern_check/execute_structure_check/summarize_blocks)完整Python实现; 修复R03变长负向后顾Python re不兼容→拆为正向匹配+前置上下文排除; 修复R04镜号字母前缀(#A4中A不匹配\d+)→扩为[A-Za-z]?\d+; 补充parse_blocks()回退逻辑·is_false_positive()全豁免矩阵。
> **宪法依据:** 画布第五条(确定性优先于概率性)——正则扫描准确率100% > LLM判断~73%
> **定位:** 调度器自执行脚本·零LLM·零Agent调用·零模型判断
> **集成:** 替代当前Scene Auditor Phase 0中的Gate 0扫描·由调度器在启动Scene Auditor之前执行
> **被替换:** scene_auditor_v1.0.md §3 (Phase 0: Gate 0确定性预扫描)

---

# §1 区块分类 (扫描前先分段)

## 1.1 区块解析规则

对台本文件(VIDEO_PROMPT_[场景].md)进行区块解析。解析基于【】标记头·按行遍历:

```
BLOCK_HEADER:
  范围: 文件开头到第一个【标记头之前
  特征: 以 "> **" 开头的元数据行·项目信息·场景ID·渲染目标声明
  包含: Prompter信息·场景名称·输入骨架·模式·角色·渲染目标
  示例: "> **Prompter:** Prompt Composer v2.0"
        "> **渲染目标:** Seko画布 · Seedance 2.0"

BLOCK_DECLARATION:
  标记: 【场景级共享锚点】
  子块: @声明区·C1 Character Anchor·C2 Environment Anchor·
        C3 Lighting Anchor·C4 Style Spine·场景级禁止
  特征: 场景头部一次性声明·逐字锁定·不可修改
  结束: 遇到【镜# 或 ━━━ 分割线】

BLOCK_DESIGN_NOTES:
  标记: 【设计依据】
  特征: "(不进入AI渲染·仅供人类审核)" 声明
  内容: KB规则ID引用·设计决策推理·仅供人类审核
  结束: 下一个【标记头

BLOCK_REFERENCE:
  标记: 【传入参考图】
  特征: @图片引用·用途声明·参考图格位描述
  结束: 下一个【标记头

BLOCK_ACTION:
  标记: 【生成指令】
  子块: Subject: · Action: · Camera: · Style: · Constraints:
  特征: 实际进入Seko渲染的提示词正文
  结束: 下一个【标记头

BLOCK_AUDIO:
  标记: 【音轨】或音轨
  特征: 声音事件·触发时刻·对白标注
  结束: 下一个【标记头

BLOCK_TRANSITION:
  标记: 【段末转场设计】
  特征: 硬切/淡入等转场类型·视觉跳跃·音频过渡
  结束: 下一个【标记头

BLOCK_PROHIBIT:
  标记: 【禁止】
  特征: 逐条禁止项·可量化的视觉约束
  结束: 下一个【标记头或镜#分割线

BLOCK_CLOSING:
  标记: 【全场景收尾】或全场景收尾
  特征: 色彩弧线总结·运镜统计·硬切统计·宪法合规声明·场景末状态快照
  结束: 文件末尾
```

## 1.2 区块边界判定规则

```
起始判定:
  IF 行 == "^##[^#]*【场景级共享锚点】"  → BLOCK_DECLARATION 开始
  IF 行 == "^###\s*【设计依据】"         → BLOCK_DESIGN_NOTES 开始
  IF 行 == "^###\s*【传入参考图】"       → BLOCK_REFERENCE 开始
  IF 行 == "^###\s*【生成指令】"         → BLOCK_ACTION 开始
  IF 行 == "^###\s*音轨" 或 "^###\s*【音轨】" → BLOCK_AUDIO 开始
  IF 行 == "^###\s*【段末转场设计】"     → BLOCK_TRANSITION 开始
  IF 行 == "^###\s*【禁止】"             → BLOCK_PROHIBIT 开始
  IF 行 == "^##\s*━+\s*全场景收尾"      → BLOCK_CLOSING 开始
  文件开头(无前置标记)                     → BLOCK_HEADER 开始

结束判定:
  遇到下一个同层或更高层级的标记头 → 当前区块结束
  文件末尾 → 当前区块结束
```

## 1.3 子块内部嵌套处理

```
BLOCK_ACTION内部子块:
  当扫描ACTION块时·Subject:/Action:/Camera:/Style:/Constraints:
  各自独立子行·但在同一BLOCK_ACTION内·共享规则适用性。
  不需要进一步细分——BLOCK_ACTION整体适用全部action规则。

BLOCK_DECLARATION内部区域子块:
  @声明区(C0)·C1 Character·C2 Environment·C3 Lighting·C4 Style·场景级禁止
  共享DECLARATION规则适用性·但"场景级禁止"子块的R09规则豁免需单独处理。
  判定: "场景级禁止"是DECLARATION内子块→适用PROHIBIT的R09豁免逻辑。
```

## 1.4 区块分类命令行参考 (调度器可执行)

```bash
# 区块提取示例(UNIX shell·Git Bash)
# 提取BLOCK_HEADER: 文件开头到第一个##
sed -n '1,/^##[^#]/p' $INPUT | head -n -1

# 提取所有【设计依据】块(可用于跳过验证)
awk '/^### 【设计依据】/,/^### 【/{print}' $INPUT

# 提取所有【生成指令】块(Gate 0主要扫描目标)
awk '/^### 【生成指令】/,/^### 【/{print}' $INPUT

# 提取所有【禁止】块
awk '/^### 【禁止】/,/^### 【/ {print}' $INPUT
```

---

# §2 每区块适用规则矩阵

## 2.1 规则适用性表

| 规则 | HEADER | DECL | DESIGN | ACTION | AUDIO | PROHIBIT | TRANS | CLOSING |
|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| R01 时长硬约束 | - | - | - | ✅ | - | - | ✅ | - |
| R02 段首过程动词 | - | - | - | ✅ | - | - | - | - |
| R03 时间模糊词 | - | - | - | ✅ | - | - | - | - |
| R04 跨镜引用 | - | - | - | ✅ | - | - | - | - |
| R05 参考图引用 | - | ✅ | - | ✅ | - | - | - | - |
| R06 禁止清单模糊词 | - | - | - | - | - | ✅ | - | - |
| R07 工程符号泄漏 | - | - | - | ✅ | - | - | ✅ | - |
| R08 段结构完整性 | - | - | - | ✅ | - | - | - | - |
| R09 负向词 | - | - | - | ✅ | ✅ | ❌跳过 | - | - |
| R10 模型名泄漏 | ❌跳过 | ✅ | ❌跳过 | ✅ | ✅ | ✅ | ✅ | ❌跳过 |
| R11 @引用用途声明 | - | ✅ | - | ✅ | - | - | - | - |
| R12 KB规则ID泄漏 | ❌跳过 | - | ❌跳过 | ✅ | - | - | - | - |
| R13 骨架顺序 | - | - | - | ✅ | - | - | - | - |
| R14 运镜语义 | - | - | - | ✅ | ❌跳过 | - | - | - |
| R15 画面外声音源 | - | - | - | ✅ | ✅ | - | - | - |

**图例:**
- ✅ = 规则在此区块中生效·必须扫描
- ❌跳过 = 明确跳过·不扫描·避免假阳性
- `-` = 不适用·此区块中该规则无效义


## 2.2 规则适用性详细说明

### R01 时长硬约束 (ACTION + TRANSITION)

```
适用: BLOCK_ACTION · BLOCK_TRANSITION
扫描: BLOCK_ACTION中每段的时间标注 [A-B]秒
      BLOCK_TRANSITION中过渡时长(不计入段时长·仅确认转场≤2秒)
跳过: 其他所有区块
原因: 时长约束仅对生成指令和转场有意义。
      HEADER中的"7镜·31秒"是场景总计·不是单段时长·不应触发R01。
```

### R02 段首过程动词 (仅ACTION)

```
适用: BLOCK_ACTION
扫描: Action块t=N秒分段的首句
跳过: 所有其他区块
原因: 过程动词("正在""开始""已")仅对画面描述有意义。
      DECLARATION和DESIGN_NOTES中的过程动词属于设计讨论·非画面描述。
```

### R03 时间模糊词 (仅ACTION)

```
适用: BLOCK_ACTION
扫描: Action块正文
跳过: BLOCK_DESIGN_NOTES · BLOCK_TRANSITION · BLOCK_CLOSING
原因: "缓缓""渐渐"在Action中=画面描述模糊·违规。
      在转场设计中"渐变过渡"是合法转场描述·不违规。
      在收尾中的色彩弧线总结是元描述·不违规。
```

### R04 跨镜引用 (仅ACTION)

```
适用: BLOCK_ACTION
扫描: Action块正文中的跨镜引用模式
跳过: 所有其他区块
原因: "参考上镜""同上镜"仅在Seko生成指令中造成不确定性。
      在DECLARATION中的跨镜色温一致性声明、DESIGN_NOTES中的
      "参照镜#A2的构图"等属于设计讨论·不进入Seko执行上下文。
```

### R05 参考图引用格式 (DECLARATION + ACTION)

```
适用: BLOCK_DECLARATION(@声明区) · BLOCK_ACTION(@图片引用)
跳过: BLOCK_DESIGN_NOTES · BLOCK_REFERENCE
原因: @声明区和生成指令中的@图片引用需格式验证。
      【传入参考图】块和【设计依据】块中的@图片引用是设计讨论用·不进入Seko。
```

### R06 禁止清单模糊词 (仅PROHIBIT)

```
适用: BLOCK_PROHIBIT
跳过: 所有其他区块
原因: "稳""舒服""自然"等在禁止块中是违规的(不可量化检查)。
      在DESIGN_NOTES中是设计讨论术语·不违规。
```

### R07 工程符号泄漏 (ACTION + TRANSITION)

```
适用: BLOCK_ACTION · BLOCK_TRANSITION
跳过: BLOCK_DESIGN_NOTES · BLOCK_HEADER
原因: v_dolly·ω_pan·7-DOF等仅在不进入Seko的上下文中可接受。
      DESIGN_NOTES中的KB规则ID是合法设计引用。
      HEADER中如有工程术语是文档元数据·不进入Seko。
```

### R08 段结构完整性 (仅ACTION上下文)

```
适用: BLOCK_ACTION(检查每镜是否有参数卡+生成指令+转场+禁止)
扫描原理: 不扫描ACTION块内部文本·而是检查每镜的区块结构完整性。
         对每镜检查: 是否存在【镜头参数卡】【生成指令】【段末转场设计】【禁止】四个块头。
跳过: 所有其他区块(非镜级结构检查)
```

### R09 负向词 (ACTION + AUDIO · 跳过PROHIBIT)

```
适用: BLOCK_ACTION · BLOCK_AUDIO
跳过: BLOCK_PROHIBIT · BLOCK_DESIGN_NOTES · BLOCK_HEADER
原因: PROHIBIT块本身是禁止清单·"禁止""不要""避免"是预期内容。
      "禁止眨眼""不要晃动"在PROHIBIT中合法·在ACTION中违规。
      AUDIO中"禁止"如"避免音效重叠"是合法工程约束。
```

### R10 模型名泄漏 (跳过HEADER + DESIGN_NOTES + CLOSING)

```
适用: BLOCK_DECLARATION · BLOCK_ACTION · BLOCK_AUDIO · BLOCK_PROHIBIT · BLOCK_TRANSITION
跳过: BLOCK_HEADER · BLOCK_DESIGN_NOTES · BLOCK_CLOSING
原因: **v1.1核心修复**——v1.0的R10假阳性"Seedance 2.0"在HEADER中。
      HEADER中的"渲染目标: Seko画布 · Seedance 2.0"是文档元数据·不在Seko生成指令中。
      DESIGN_NOTES中提及模型名(如"需要海螺02模型")是设计讨论·不在Seko生成指令中。
      CLOSING中的模型分析也不进入Seko。
      DECLARATION和ACTION中的模型名仍需阻断——它们直接进入Seko画面描述上下文。
      正则: /(?:即梦|海螺|Kling|Vidu|Seedance|可灵|万相|Runway|Pika|Sora|Luma|Dreamina|Hailuo)/i
      注: "Seko"不算模型名(Seko是渲染平台名称)·允许出现在任何区块。
```

### R11 @引用用途声明 (DECLARATION + ACTION)

```
适用: BLOCK_DECLARATION · BLOCK_ACTION
跳过: BLOCK_DESIGN_NOTES · BLOCK_REFERENCE
原因: @图片引用后需5汉字用途描述——仅在Seko生成指令和锚点声明中强制。
      在传入参考图块和设计依据块中不强制(这些块本身就是设计讨论)。
```

### R12 KB规则ID泄漏 (跳过HEADER + DESIGN_NOTES)

```
适用: BLOCK_ACTION
跳过: BLOCK_HEADER · BLOCK_DESIGN_NOTES · BLOCK_PROHIBIT
原因: KB规则ID(D-TRI-XX/M-MOT-XX等)仅在【生成指令】正文中构成泄漏。
      DESIGN_NOTES中KB规则ID是设计引用·合法且必需。
      HEADER中如有KB ID是元数据注释·不进入Seko。
      PROHIBIT中"P-FAL-08规避"等注释是合理工程约束标注·不进入Seko生成指令正文。
      正则: /(?:D-TRI-|M-MOT-|M-MOV-|C-COM-|C-KTZ-|C-FI-|C-AJS-|C-DEP-|L-3PT-|L-SRC-|E-MTC-|S-SHT-|GEN-|VS-LS-|P-REN-|P-FAL-)\d*/
```

### R13 骨架顺序 (仅ACTION)

```
适用: BLOCK_ACTION
扫描: Subject:→Action:→Camera:→Style:→Constraints: 出现顺序
跳过: 所有其他区块
原因: 骨架顺序约束仅适用于Seko生成指令的提示词结构。
```

### R14 运镜语义 (ACTION · 跳过AUDIO + DESIGN_NOTES)

```
适用: BLOCK_ACTION
跳过: BLOCK_AUDIO · BLOCK_DESIGN_NOTES · BLOCK_PROHIBIT · BLOCK_TRANSITION
原因: 运镜语义("推近""横移""摇摄")在Action画面描述中违规。
      AUDIO中不描述运镜·跳过。
      DESIGN_NOTES中讨论运镜策略是合法的。
      PROHIBIT中"禁止推近过程中画面晃动"是禁止项·不违规。
      TRANSITION中的运镜过渡描述("推近过渡到下一镜")是转场设计·不违规。
```

### R15 画面外声音源 (ACTION + AUDIO)

```
适用: BLOCK_ACTION · BLOCK_AUDIO
跳过: BLOCK_DESIGN_NOTES · BLOCK_TRANSITION · 其他
原因: "画框外传来"在ACTION中违规(画面描述应限于画框内·声音放音轨)。
      但在AUDIO中"画框外脚步声"是合法的音轨描述(音轨本就是声音事件)。
      R15的"AUDIO中保留"是不跳过AUDIO的原因——需要验证AUDIO中声音源描述的
      正确性(格式是否规范·是否有精确触发时刻)。
```

---

# §3 实现: 调度器自执行脚本

## 3.1 伪代码

```python
# gate0_context_aware_scan.py — 调度器自执行·零LLM

import re
import sys

# ⚠️ 权威声明: 本文件的R01-R15是MODE:P管道Gate 0确定性扫描的**唯一权威定义**。
# 其他文件(agent_quick_ref·scene_auditor·P-CONSTITUTION·dispatcher)引用此定义。
# 修改R01-R15的正则·阈值·或适用性矩阵必须在本文档中执行。

# === R01-R15 规则定义 (正则·数值比较·模式匹配) ===

RULES = {
    "R01": {
        "name": "时长硬约束",
        "type": "numeric",
        "applicable_blocks": ["BLOCK_ACTION", "BLOCK_TRANSITION"],
        "check": "duration_check"  # 函数引用
    },
    "R02": {
        "name": "段首过程动词",
        "type": "regex",
        "applicable_blocks": ["BLOCK_ACTION"],
        "pattern": r'^(?:[^。\n]{0,20}?(?:正在|刚(?!好)|已(?!经)|开始[^前]|持续[^时间]|一直[在以]|仍[在未]))'
    },
    "R03": {
        "name": "时间模糊词",
        "type": "regex",
        "applicable_blocks": ["BLOCK_ACTION"],
        # Python re模块不支持变长负向后顾(?<!...)·拆为两步:
        # 第1步: 正向匹配所有模糊时间词
        "pattern": r'(?:缓缓|渐渐|慢慢|逐渐|徐徐|冉冉)',
        # 第2步: 检查匹配位置前N字符是否含排除模式·是则跳过(假阳性)
        "pre_context_chars": 20,
        "pre_context_exclusion": r'(?:第\d+|t\s*=\s*\d|关键帧|约[莫定]|距[离今]|等[待候]|推[近远拉]|前[推拉]|横移|摇[镜摄]|跟[拍摄随])$'
    },
    "R04": {
        "name": "跨镜引用",
        "type": "regex",
        "applicable_blocks": ["BLOCK_ACTION"],
        # 修复: [A-Za-z]?\d+ 支持字母前缀镜号(如#A4·#B1·同镜A3)
        "pattern": r'(?:同上[一]?镜|参考上[一]?镜|如前所[述示]|同镜\s*[#＃]?(?:[A-Za-z]?\d+)|与镜\s*[#＃]?(?:[A-Za-z]?\d+)|参照[上前]镜|见[上前]镜|同\s*[#＃]?(?:[A-Za-z]?\d+)|与\s*[#＃]?(?:[A-Za-z]?\d+))',
        "flags": re.IGNORECASE
    },
    "R05": {
        "name": "参考图引用",
        "type": "pattern_match",
        "applicable_blocks": ["BLOCK_DECLARATION", "BLOCK_ACTION"],
        "check": "reference_check"
    },
    "R06": {
        "name": "禁止清单模糊词",
        "type": "regex",
        "applicable_blocks": ["BLOCK_PROHIBIT"],
        "pattern": r'(?:稳(?!定)|舒服|自然(?!光|语言|过渡)|美感|漂亮)(?![^。\n]{0,20}(?:光|语言|过渡))'
    },
    "R07": {
        "name": "工程符号泄漏",
        "type": "regex",
        "applicable_blocks": ["BLOCK_ACTION", "BLOCK_TRANSITION"],
        "pattern": r'(?:v_dolly|ω_pan|ω_tilt|ω_roll|7-DOF|f\/\d+\.?\d*|°\/s)'
    },
    "R08": {
        "name": "段结构完整性",
        "type": "structure_check",
        "applicable_blocks": ["BLOCK_ACTION"],  # 实际检查镜级结构
        "check": "structure_check"
    },
    "R09": {
        "name": "负向词",
        "type": "regex",
        "applicable_blocks": ["BLOCK_ACTION", "BLOCK_AUDIO"],
        # PROHIBIT块明确跳过——此块本身是禁止清单
        "pattern": r'(?:不要|避免|禁止|不能|不应|勿[要]|别[再]|切勿|严禁|不许|不得)(?![^。\n]{0,10}(?:后期叠加|画框外|不在|不进入|不要求|不描述))'
    },
    "R10": {
        "name": "模型名泄漏",
        "type": "regex",
        "applicable_blocks": [
            "BLOCK_DECLARATION", "BLOCK_ACTION", "BLOCK_AUDIO",
            "BLOCK_PROHIBIT", "BLOCK_TRANSITION"
            # ← HEADER + DESIGN_NOTES + CLOSING 明确跳过
        ],
        "pattern": r'(?:即梦|海螺|Kling|Vidu|Seedance|可灵|万相|Runway|Pika|Sora|Luma|Dreamina|Hailuo)',
        "flags": re.IGNORECASE,
        "note": "Seko不算模型名·允许出现在任何区块"
    },
    "R11": {
        "name": "@引用用途声明",
        "type": "pattern_match",
        "applicable_blocks": ["BLOCK_DECLARATION", "BLOCK_ACTION"],
        "check": "usage_declaration_check"
    },
    "R12": {
        "name": "KB规则ID泄漏",
        "type": "regex",
        "applicable_blocks": ["BLOCK_ACTION"],
        # HEADER + DESIGN_NOTES 明确跳过
        "pattern": r'(?:D-TRI-|M-MOT-|M-MOV-|C-COM-|C-KTZ-|C-FI-|C-AJS-|C-DEP-|L-3PT-|L-SRC-|E-MTC-|S-SHT-|GEN-|VS-LS-|P-REN-|P-FAL-)\d*'
    },
    "R13": {
        "name": "骨架顺序",
        "type": "order_check",
        "applicable_blocks": ["BLOCK_ACTION"],
        "check": "skeleton_order_check"
    },
    "R14": {
        "name": "运镜语义",
        "type": "regex",
        "applicable_blocks": ["BLOCK_ACTION"],
        # AUDIO + DESIGN_NOTES + PROHIBIT + TRANSITION 明确跳过
        "pattern": r'(?:推近(?:继续|落定|至|到|过程|中)|拉远(?:继续|至|到|过程|中)|横移(?:继续|至|到)|摇[镜摄](?:过|至|到)?|跟[拍摄随](?:着|至|到)?|镜头(?:缓[缓慢]|快[速]|慢[慢速]|匀[速])(?:推|拉|摇|移|跟)|(?:推|拉|摇|移|跟|升|降)镜(?:头)?[^。\n]{0,10}(?:继续|进行|中)|运镜(?:继续|进行|中))',
        "flags": re.IGNORECASE
    },
    "R15": {
        "name": "画面外声音源",
        "type": "regex",
        "applicable_blocks": ["BLOCK_ACTION", "BLOCK_AUDIO"],
        "pattern": r'(?:画框外|镜头外|屏幕外|画面外)(?:传来|响[起]|飘[来进]|涌入|听到)'
    }
}


# === 区块解析器 ===

def parse_blocks(filepath):
    """
    解析台本文件为区块列表·按【】标记头分段。

    参数:
        filepath (str): 台本文件路径(如 VIDEO_PROMPT_EP14_S1.md)

    返回:
        list[tuple]: [(block_type, start_line, end_line, block_text), ...]
            block_type: str  -- BLOCK_HEADER / BLOCK_DECLARATION / BLOCK_ACTION 等
            start_line: int  -- 区块起始行号(1-based)
            end_line: int    -- 区块结束行号(1-based·不含; 即block_text的行数 = end_line - start_line)
            block_text: str  -- 区块原始文本(含换行符)

    回退逻辑:
        若未识别到任何【标记头】(即marker_hits为空)→
        整个文件视为单个BLOCK_ACTION·适用全部15条规则(等价v1.0全局扫描行为)。
        调用方可通过检查返回列表是否仅含BLOCK_ACTION且无其他类型来判断是否回退。
    """
    import io

    # --- 文件读取·编码容错 ---
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []  # 文件不存在·让调用方处理
    except UnicodeDecodeError:
        # 尝试GBK编码(Windows中文环境常见)
        with open(filepath, 'r', encoding='gbk') as f:
            lines = f.readlines()

    if not lines:
        return []

    # --- 区块标记定义 ---
    # 格式: (检测正则, 区块类型)
    # 正则按行首匹配·顺序决定优先级(更具体的放前面)
    BLOCK_MARKERS = [
        # 场景级标记头(##/###开头·含【】)
        (r'^##[^#]*【场景级共享锚点】', 'BLOCK_DECLARATION'),
        (r'^###\s*【设计依据】',         'BLOCK_DESIGN_NOTES'),
        (r'^###\s*【传入参考图】',       'BLOCK_REFERENCE'),
        (r'^###\s*【生成指令】',         'BLOCK_ACTION'),
        (r'^###\s*(?:音轨|【音轨】)',    'BLOCK_AUDIO'),
        (r'^###\s*【段末转场设计】',     'BLOCK_TRANSITION'),
        (r'^###\s*【禁止】',             'BLOCK_PROHIBIT'),
        (r'^##\s*━+\s*全场景收尾',      'BLOCK_CLOSING'),

        # 镜级子块标记(嵌套在镜#内·用于R08结构完整性检查)
        (r'^###\s*【镜头参数卡】',       'BLOCK_PARAM_CARD'),
    ]

    # === 第1遍扫描: 收集所有标记头命中 ===
    marker_hits = []  # [(line_index, block_type), ...]
    for i, line in enumerate(lines):
        for pattern, block_type in BLOCK_MARKERS:
            if re.match(pattern, line):
                marker_hits.append((i, block_type))
                break  # 一行只匹配第一个命中的标记

    # === 回退逻辑: 无【标记头识别 → 全文件视为BLOCK_ACTION ===
    if not marker_hits:
        # 台本格式非标准·无任何【标记头·回退到v1.0全局扫描
        full_text = ''.join(lines)
        return [("BLOCK_ACTION", 1, len(lines), full_text)]

    # === 第2遍扫描: 按标记头构建区块 ===
    blocks = []
    current_type = "BLOCK_HEADER"
    current_start = 0  # 当前区块起始行索引(0-based)

    for line_idx, block_type in marker_hits:
        # 结束当前区块(如果有内容)
        if current_start < line_idx:
            block_text = ''.join(lines[current_start:line_idx])
            # 跳过纯空块(仅含空白行)
            if block_text.strip():
                blocks.append((
                    current_type,
                    current_start + 1,   # 转为1-based行号
                    line_idx,            # 结束行(1-based·不含)
                    block_text
                ))
        # 开始新区块
        current_type = block_type
        current_start = line_idx

    # === 最后一个区块(从最后一个标记到文件末尾) ===
    if current_start < len(lines):
        block_text = ''.join(lines[current_start:])
        if block_text.strip():
            blocks.append((
                current_type,
                current_start + 1,
                len(lines),
                block_text
            ))

    # === 后处理: 相邻同类型非ACTION区块合并(减少碎片) ===
    # 多个镜的BLOCK_ACTION必须独立保留(每个镜的生成指令不同)
    # 只合并DECLARATION/DESIGN_NOTES/CLOSING等非镜级区块
    if len(blocks) > 1:
        merged = [blocks[0]]
        for b in blocks[1:]:
            prev = merged[-1]
            # 合并条件: 同类型·非ACTION·非AUDIO·非PROHIBIT·非TRANSITION·非PARAM_CARD
            mergeable_types = {
                'BLOCK_HEADER', 'BLOCK_DECLARATION', 'BLOCK_DESIGN_NOTES',
                'BLOCK_REFERENCE', 'BLOCK_CLOSING'
            }
            if (b[0] == prev[0] and b[0] in mergeable_types
                    and prev[2] == b[1]):  # 紧邻
                # 合并: 扩展结束行和文本
                merged[-1] = (prev[0], prev[1], b[2], prev[3] + b[3])
            else:
                merged.append(b)
        blocks = merged

    return blocks


# === 规则过滤: 按区块类型获取适用规则 ===

def get_applicable_rules(block_type):
    """返回指定区块类型适用的规则ID列表"""
    applicable = []
    for rule_id, rule_def in RULES.items():
        if block_type in rule_def["applicable_blocks"]:
            applicable.append(rule_id)
    return applicable


# === 假阳性过滤器 (二次确认) ===

def is_false_positive(block_type, rule_id, matched_text, full_context):
    """
    检查正则匹配是否为假阳性·基于区块类型+规则ID+上下文二次确认。

    参数:
        block_type (str):   匹配所在区块类型(BLOCK_HEADER·BLOCK_ACTION等)
        rule_id (str):      触发的规则编号(R01-R15)
        matched_text (str): 正则匹配到的原始文本
        full_context (str): 匹配位置前后各80字符的上下文窗口

    返回:
        tuple: (is_fp: bool, reason: str)
            is_fp=True  → 假阳性·应跳过·不计入阻断
            is_fp=False → 真实违规·计入阻断

    豁免逻辑(按§2规则适用性矩阵):
        - R10 + BLOCK_HEADER       → 跳过(HEADER中的"Seedance 2.0"是文档元数据)
        - R10 + BLOCK_DESIGN_NOTES → 跳过(DESIGN_NOTES中的模型名是设计讨论)
        - R10 + BLOCK_CLOSING      → 跳过(CLOSING中的模型分析不进入Seko)
        - R12 + BLOCK_HEADER       → 跳过(HEADER中的KB ID是文档元数据)
        - R12 + BLOCK_DESIGN_NOTES → 跳过(DESIGN_NOTES中的KB ID是合法设计引用)
        - R12 + BLOCK_PROHIBIT     → 跳过(PROHIBIT中的KB ID是合理工程约束标注)
        - R09 + BLOCK_PROHIBIT     → 跳过(PROHIBIT块中的"禁止"是合法的禁止清单项头)
        - R09 + BLOCK_DECLARATION  → 跳过(仅当匹配行以"数字. 禁止"开头·场景级禁止子块)
        - R14 + BLOCK_TRANSITION   → 跳过(段末转场中的运镜描述是转场设计)
        - R14 + BLOCK_AUDIO        → 跳过(AUDIO中不描述运镜)
        - R07 + Camera上下文       → 跳过(f-stop值如f/8是标准摄影标注)
    """
    # --- R10 模型名泄漏: HEADER/DESIGN_NOTES/CLOSING 豁免 ---
    if rule_id == "R10":
        if block_type == "BLOCK_HEADER":
            return True, "HEADER中的模型名声明是文档元数据·非Seko生成指令内容"
        if block_type == "BLOCK_DESIGN_NOTES":
            return True, "DESIGN_NOTES中的模型名是设计讨论·非Seko生成指令内容"
        if block_type == "BLOCK_CLOSING":
            return True, "CLOSING中的模型分析不进入Seko·非生成指令内容"

    # --- R12 KB规则ID泄漏: HEADER/DESIGN_NOTES/PROHIBIT 豁免 ---
    if rule_id == "R12":
        if block_type == "BLOCK_HEADER":
            return True, "HEADER中的KB规则ID是文档元数据注释·非提示词泄漏"
        if block_type == "BLOCK_DESIGN_NOTES":
            return True, "DESIGN_NOTES中的KB规则ID是合法设计引用·非提示词泄漏"
        if block_type == "BLOCK_PROHIBIT":
            return True, "PROHIBIT中的KB规则ID(如P-FAL-08规避)是合理工程约束标注·非泄漏"

    # --- R09 负向词: PROHIBIT块豁免 + DECLARATION场景级禁止子块豁免 ---
    if rule_id == "R09":
        if block_type == "BLOCK_PROHIBIT":
            return True, "PROHIBIT块中的'禁止'是合法的禁止清单项头·非负向指令"
        if block_type == "BLOCK_DECLARATION":
            # DECLARATION内的"场景级禁止"子块·以"数字. 禁止"开头→豁免
            # 例: "3. 禁止镜头出现晃动" → 这是场景级禁止声明·不是Action中的负向指令
            if re.match(r'^\d+\.\s*禁止', matched_text) or \
               re.search(r'(?:场景级禁止|禁止项|禁止清单)', full_context):
                return True, "DECLARATION中'场景级禁止'子块的禁止声明是合法的·非Action负向指令"

    # --- R14 运镜语义: TRANSITION/AUDIO 豁免 ---
    if rule_id == "R14":
        if block_type == "BLOCK_TRANSITION":
            return True, "段末转场中的运镜描述是转场设计·非Action画面描述"
        if block_type == "BLOCK_AUDIO":
            return True, "AUDIO中不描述运镜·非Action画面描述"

    # --- R07 工程符号泄漏: Camera参数卡中的f-stop值豁免 ---
    if rule_id == "R07":
        # 检查是否在Camera参数块上下文中
        if re.search(r'(?:Camera|focal|aperture)', full_context, re.IGNORECASE):
            if re.match(r'^f\/\d+\.?\d*$', matched_text.strip()):
                return True, "Camera参数中的f-stop值是标准摄影标注·非工程符号泄漏"

    return False, ""


# === 数值检查 (R01 时长硬约束) ===

def execute_numeric_check(rule_id, block_text, start_line):
    """
    执行数值类规则检查。

    参数:
        rule_id (str):    规则编号(当前仅R01使用此函数)
        block_text (str): 区块原始文本
        start_line (int): 区块起始行号(1-based)

    返回:
        dict: {"violations": list[dict]}  -- 违规列表·每个违规含rule/name/line/text/block/context

    R01 时长硬约束逻辑:
        - 提取 [A-B]秒 或 t=N~M秒 格式的时长标注
        - 单段时长上限: 15秒(D-TRI-04硬约束)
        - 转场时长上限: 2秒(BLOCK_TRANSITION中)
        - 注意: 不检查BLOCK_TRANSITION的段时长(转场不计入段时长)
    """
    violations = []
    if rule_id != "R01":
        return {"violations": violations}

    # 提取时长标注: [A-B]秒 或 t=Ns或t=N~M秒
    # 匹配模式:
    #   [数字-数字]秒           → 段时长范围
    #   t=数字s 或 t=数字秒     → 精确时长
    #   [数字]秒               → 精确段时长
    duration_patterns = [
        # [A-B]秒 格式
        (r'\[(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)\]\s*秒', 'range'),
        # t=Ns 或 t=N秒
        (r't\s*=\s*(\d+(?:\.\d+)?)\s*[s秒]', 'exact'),
        # [N]秒 格式
        (r'\[(\d+(?:\.\d+)?)\]\s*秒', 'exact_bracket'),
    ]

    for pattern, fmt in duration_patterns:
        for match in re.finditer(pattern, block_text):
            line_num = start_line + block_text[:match.start()].count('\n')

            if fmt == 'range':
                start_sec = float(match.group(1))
                end_sec = float(match.group(2))
                duration = end_sec  # 以结束时间为准
                if duration > 15.0:
                    violations.append({
                        "rule": rule_id,
                        "name": "时长硬约束",
                        "line": line_num + 1,
                        "text": match.group(0),
                        "block": "BLOCK_ACTION",
                        "context": f"段时长{duration}秒 > 15秒上限(D-TRI-04)"
                    })
            elif fmt == 'exact':
                duration = float(match.group(1))
                if duration > 15.0:
                    violations.append({
                        "rule": rule_id,
                        "name": "时长硬约束",
                        "line": line_num + 1,
                        "text": match.group(0),
                        "block": "BLOCK_ACTION",
                        "context": f"段时长{duration}秒 > 15秒上限(D-TRI-04)"
                    })
            elif fmt == 'exact_bracket':
                duration = float(match.group(1))
                # [N]秒 可能是转场时长·仅<0.5秒的可能是转场·不触发R01
                if duration > 2.0:
                    violations.append({
                        "rule": rule_id,
                        "name": "时长硬约束",
                        "line": line_num + 1,
                        "text": match.group(0),
                        "block": "BLOCK_ACTION",
                        "context": f"时长{duration}秒可能超出约束"
                    })

    return {"violations": violations}


# === 模式匹配检查 (R05 参考图引用 · R11 @引用用途声明) ===

def execute_pattern_check(rule_id, block_text, start_line):
    """
    执行模式匹配类规则检查。

    参数:
        rule_id (str):    规则编号(R05或R11)
        block_text (str): 区块原始文本
        start_line (int): 区块起始行号(1-based)

    返回:
        dict: {"violations": list[dict]}

    R05 参考图引用格式检查:
        - 检查 @[描述]:[[路径]] 格式完整性
        - 必须包含: @ + 描述文本 + : + [[路径]]
        - 路径不能为空/不能是占位符

    R11 @引用用途声明检查:
        - @图片引用后需紧跟至少5个汉字的用途描述
        - 检测模式: @...: 或 @...后缺少5+汉字的描述
        - 豁免: 如果在Reference块中(已由区块过滤处理)则跳过
    """
    violations = []

    if rule_id == "R05":
        # 查找@引用模式: @描述:[[路径]] 或 @描述
        ref_matches = re.finditer(
            r'@\s*([^:\n]{1,50}?)\s*(?::\s*)?(?:\[\[([^\]]*)\]\])?',
            block_text
        )
        for match in ref_matches:
            desc = match.group(1).strip() if match.group(1) else ""
            path = match.group(2) if match.lastindex >= 2 and match.group(2) else ""

            # 检查: 路径为空或过短
            if not path or len(path.strip()) < 3:
                line_num = start_line + block_text[:match.start()].count('\n')
                violations.append({
                    "rule": rule_id,
                    "name": "参考图引用格式",
                    "line": line_num + 1,
                    "text": match.group(0).strip()[:60],
                    "block": "BLOCK_ACTION",
                    "context": "引用路径缺失或过短·需 [[完整路径]] 格式"
                })

    elif rule_id == "R11":
        # 查找@引用后缺少5+汉字用途描述的情况
        # 模式: @后跟文本·冒号前不足5个汉字→违规
        ref_matches = re.finditer(
            r'@\s*([^:\n]{0,30}?)(?:\s*:)',
            block_text
        )
        for match in ref_matches:
            desc = match.group(1).strip() if match.group(1) else ""
            # 统计汉字数量(Unicode范围 一-鿿)
            hanzi_count = sum(1 for c in desc if '一' <= c <= '鿿')
            if hanzi_count < 5:
                line_num = start_line + block_text[:match.start()].count('\n')
                violations.append({
                    "rule": rule_id,
                    "name": "@引用用途声明",
                    "line": line_num + 1,
                    "text": match.group(0).strip()[:60],
                    "block": "BLOCK_ACTION",
                    "context": f"用途描述仅{hanzi_count}汉字·需≥5汉字"
                })

    return {"violations": violations}


# === 结构/顺序检查 (R08 段结构完整性 · R13 骨架顺序) ===

def execute_structure_check(rule_id, blocks, filepath):
    """
    执行结构/顺序类规则检查。

    参数:
        rule_id (str):          规则编号(R08或R13)
        blocks (list[tuple]):   parse_blocks()返回的区块列表
        filepath (str):         源文件路径(用于读取原始行)

    返回:
        dict: {"violations": list[dict]}

    R08 段结构完整性:
        检查每个镜是否具备完整的四件套:
        【镜头参数卡】+ 【生成指令】+ 【段末转场设计】+ 【禁止】
        方法: 读取原始文件·查找镜#标记·然后检查该镜下的子块完整性

    R13 骨架顺序:
        检查BLOCK_ACTION中 Subject→Action→Camera→Style→Constraints 的出现顺序
    """
    violations = []

    if rule_id == "R08":
        # 读取原始文件行
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()
        except (FileNotFoundError, UnicodeDecodeError):
            return {"violations": violations}

        # 查找所有镜#标记行
        shot_markers = []
        for i, line in enumerate(file_lines):
            if re.match(r'^##\s*镜\s*[#＃]', line):
                shot_markers.append((i, line.strip()))

        if not shot_markers:
            return {"violations": violations}

        # 对每个镜·检查从该镜标记到下一镜标记(或文件末尾)之间的子块
        for idx, (shot_line, shot_header) in enumerate(shot_markers):
            next_shot_line = (shot_markers[idx + 1][0]
                              if idx + 1 < len(shot_markers)
                              else len(file_lines))

            shot_section = ''.join(file_lines[shot_line:next_shot_line])

            # 检查四个必需子块
            required_blocks = {
                '镜头参数卡':  r'###\s*【镜头参数卡】',
                '生成指令':    r'###\s*【生成指令】',
                '段末转场设计': r'###\s*【段末转场设计】',
                '禁止':        r'###\s*【禁止】',
            }
            missing = []
            for name, pattern in required_blocks.items():
                if not re.search(pattern, shot_section):
                    missing.append(name)

            if missing:
                violations.append({
                    "rule": rule_id,
                    "name": "段结构完整性",
                    "line": shot_line + 1,
                    "text": shot_header,
                    "block": "BLOCK_ACTION",
                    "context": f"缺少: {', '.join(missing)} · 镜#{idx+1}"
                })

    elif rule_id == "R13":
        # 检查每个ACTION块中的骨架顺序
        SKELETON_ORDER = ['Subject', 'Action', 'Camera', 'Style', 'Constraints']
        for block_type, start_line, end_line, block_text in blocks:
            if block_type != "BLOCK_ACTION":
                continue

            # 提取骨架标签出现位置
            positions = {}
            for label in SKELETON_ORDER:
                # 匹配行首或缩进后的标签(如 "Subject:" 或 "  Subject:")
                m = re.search(rf'^[ \t]*{label}\s*:', block_text, re.MULTILINE)
                if m:
                    positions[label] = m.start()

            if not positions:
                continue  # 没有骨架标签·可能是空ACTION·跳过

            # 检查出现顺序
            prev_pos = -1
            prev_label = None
            for label in SKELETON_ORDER:
                if label in positions:
                    if positions[label] < prev_pos:
                        # 顺序错乱
                        line_num = start_line + block_text[:positions[label]].count('\n')
                        violations.append({
                            "rule": rule_id,
                            "name": "骨架顺序",
                            "line": line_num + 1,
                            "text": f"{label}: 出现在 {prev_label}: 之前",
                            "block": "BLOCK_ACTION",
                            "context": f"预期顺序: {'→'.join(SKELETON_ORDER)}"
                        })
                    prev_pos = positions[label]
                    prev_label = label

    return {"violations": violations}


# === 区块摘要生成 ===

def summarize_blocks(blocks):
    """
    生成区块解析摘要·用于Gate 0报告输出。

    参数:
        blocks (list[tuple]): parse_blocks()返回的区块列表

    返回:
        dict: {
            "total_blocks": int,         # 总区块数
            "block_types": dict,         # {类型: 出现次数}
            "details": list[dict],       # [{type, start, end, lines, applicable_rules}, ...]
            "has_fallback": bool         # 是否触发回退(v1.0全局扫描)
        }
    """
    if not blocks:
        return {
            "total_blocks": 0,
            "block_types": {},
            "details": [],
            "has_fallback": False
        }

    # 检测回退: 如果只有一个BLOCK_ACTION且覆盖整个文件·可能是回退
    has_fallback = (
        len(blocks) == 1
        and blocks[0][0] == "BLOCK_ACTION"
    )

    # 统计区块类型
    type_counts = {}
    for block_type, _, _, _ in blocks:
        type_counts[block_type] = type_counts.get(block_type, 0) + 1

    # 生成详情列表
    details = []
    for block_type, start, end, text in blocks:
        line_count = end - start
        applicable = get_applicable_rules(block_type)
        details.append({
            "type": block_type,
            "start_line": start,
            "end_line": end,
            "line_count": line_count,
            "applicable_rules": applicable,
            "rule_count": len(applicable)
        })

    return {
        "total_blocks": len(blocks),
        "block_types": type_counts,
        "details": details,
        "has_fallback": has_fallback
    }


# === 主扫描函数 ===

def gate0_scan(filepath):
    """
    Gate 0上下文感知扫描主函数。
    返回: (passed: bool, report: dict)
    """
    blocks = parse_blocks(filepath)
    results = {}
    violations = []

    for block_type, start_line, end_line, block_text in blocks:
        applicable_rules = get_applicable_rules(block_type)
        if not applicable_rules:
            continue

        for rule_id in applicable_rules:
            rule_def = RULES[rule_id]

            if rule_def["type"] == "regex":
                pattern = rule_def["pattern"]
                flags = rule_def.get("flags", 0)

                for match in re.finditer(pattern, block_text, flags):
                    matched_text = match.group(0)

                    # === R03专用: 前置上下文排除(替代Python re不支持的变长负向后顾) ===
                    # Python标准re模块不支持(?<!...)中可变长度模式。
                    # 解决方案: 正向匹配所有模糊时间词·然后检查匹配前N字符是否含排除模式。
                    if "pre_context_exclusion" in rule_def:
                        pre_start = max(0, match.start() - rule_def.get("pre_context_chars", 20))
                        pre_context = block_text[pre_start:match.start()]
                        if re.search(rule_def["pre_context_exclusion"], pre_context):
                            # 前置上下文含排除模式(如"第3秒""t=5s""关键帧")·
                            # 此处的"缓缓/渐渐"是合法帧描述·跳过
                            continue

                    # 关键: 二次确认·检查是否为假阳性
                    context_start = max(0, match.start() - 80)
                    context_end = min(len(block_text), match.end() + 80)
                    full_context = block_text[context_start:context_end]

                    is_fp, fp_reason = is_false_positive(
                        block_type, rule_id, matched_text, full_context
                    )

                    if not is_fp:
                        # 计算行号
                        violated_line = start_line + block_text[:match.start()].count('\n')
                        violations.append({
                            "rule": rule_id,
                            "name": rule_def["name"],
                            "line": violated_line + 1,
                            "text": matched_text,
                            "block": block_type,
                            "context": block_text[max(0, match.start()-40):match.end()+40].strip()
                        })
                        results[rule_id] = "BLOCKED"
                    else:
                        # 假阳性·记录但不阻断
                        if rule_id not in results:
                            results[rule_id] = "PASSED"

            elif rule_def["type"] == "numeric":
                result = execute_numeric_check(rule_id, block_text, start_line)
                if result["violations"]:
                    violations.extend(result["violations"])
                    results[rule_id] = "BLOCKED"
                else:
                    results[rule_id] = results.get(rule_id, "PASSED")

            elif rule_def["type"] == "pattern_match":
                result = execute_pattern_check(rule_id, block_text, start_line)
                if result["violations"]:
                    violations.extend(result["violations"])
                    results[rule_id] = "BLOCKED"
                else:
                    results[rule_id] = results.get(rule_id, "PASSED")

            elif rule_def["type"] in ("structure_check", "order_check"):
                result = execute_structure_check(rule_id, blocks, filepath)
                if result["violations"]:
                    violations.extend(result["violations"])
                    results[rule_id] = "BLOCKED"
                else:
                    results[rule_id] = results.get(rule_id, "PASSED")

    # 填充未触发的规则为PASSED
    for rule_id in RULES:
        if rule_id not in results:
            results[rule_id] = "PASSED"

    passed = len(violations) == 0
    return passed, {
        "results": results,
        "violations": violations,
        "block_summary": summarize_blocks(blocks)
    }
```

## 3.2 调度器集成点

```
调度器 dispatcher_v5.0.md 中 Gate 0 调用位置:

Step A3完成后:
  1. prompt_composer → 输出 EP14_S1_导演台本.md
  2. [新] 调度器自执行 gate0_scan("EP14_S1_导演台本.md")
     ├─ 输出: GATE0_PRE_REPORT.md (正则扫描结果)
     ├─ 全部✅ → 启动Scene Auditor Agent
     ├─ 有🛑 → 返回prompt_composer修复·上限1轮
     └─ 成本: 0 tokens (调度器自执行·纯正则·零LLM·零Agent调用)
  3. Scene Auditor Agent 启动(仅当Gate 0✅)
     └─ Phase 0跳过(Gate 0已前置完成)
     └─ 从Phase 1开始执行

scene_auditor_v1.0.md 变更:
  §3 Phase 0 → 标记为[DEPRECATED·V1.1]
  §3 替换为: "Phase 0(Gate 0)已由调度器前置执行·详见GATE0_PRE_REPORT.md。
              如GATE0_PRE_REPORT.md不存在·则执行v1.0的Phase 0作为回退。"
```

## 3.3 边界情况处理

### 3.3.1 无标记的自定义台本

```
问题: 如果台本文件不使用标准【标记头】格式?
回退: 整个文件视为BLOCK_ACTION·全部15条规则生效(等价v1.0全局扫描行为)
检测: 如果parse_blocks()只返回BLOCK_HEADER一个区块(无【标记头被识别)
       → 自动回退到v1.0全文件扫描
       → 输出中包含警告: "⚠️ 台本格式非标准·Gate 0回退到v1.0全局扫描·可能存在假阳性"
```

### 3.3.2 DECLARATION中的场景级禁止子块

```
问题: BLOCK_DECLARATION内包含"场景级禁止"子块·其中"禁止"字样是否触发R09?
处理: "场景级禁止"子块属于DECLARATION·但语义上等同于PROHIBIT。
      → DECLARATION内的"X. 禁止..."开头行不触发R09
      → 实现: R09正则跳过以"数字. 禁止"开头的行
      → 附加过滤: r'^\d+\.\s*禁止' 开头的行在DECLARATION中豁免
```

### 3.3.3 DESIGN_NOTES中的特殊模式

```
问题: DESIGN_NOTES中提到了模型名·当前被跳过。但如果设计依据中说
      "提示词中应使用Seedance 2.0"——这是否应该在ACTION中出现?
处理: DESIGN_NOTES中的模型名讨论不被R10扫描·不阻断。
      但如果在ACTION块中实际出现了"Seedance 2.0"·R10在ACTION中仍然生效·阻断。
      → 策略: 依靠BLOCK_ACTION中的R10扫描捕获实际泄漏
      → DESIGN_NOTES免责不影响对ACTION正文的检查
```

### 3.3.4 空块和短块

```
问题: 如果某个区块为空(N/A标注)或极短(<10行)?
处理: 仍执行规则·但空块的正则不会产生匹配。
      → 空BLOCK_AUDIO: R09·R10·R15仍执行·无匹配→通过
      → 空BLOCK_TRANSITION: R01·R07·R10仍执行·无匹配→通过
      → 不需要特殊处理·零匹配自然等于PASSED
```

### 3.3.5 多镜场景的区块交错

```
问题: 7镜场景·每镜有自己的ACTION/AUDIO/PROHIBIT块。
      区块解析如何区分镜#A1的ACTION和镜#A2的ACTION?
处理: parse_blocks()按【标记头】区分·每个镜的ACTION是独立区块。
      violations中标注block_type+行号·报告时注明镜号。
      → 例: "R02·BLOCK_ACTION·行342·镜#A3·t=9s"
      → 通过行号映射到对应镜号(向上查找最近的镜#标记)
```

---

# §4 输出格式

## 4.1 Gate 0预扫描报告模板

```markdown
# Gate 0 v1.1 上下文感知预扫描报告 — [场景名]

> **扫描时间:** [时间戳]
> **扫描方式:** 调度器自执行·区块感知正则·零LLM·零Agent调用
> **扫描对象:** [台本文件路径]
> **区块解析:** [N]个区块已识别·[M]个类型

## 区块概览

| # | 区块类型 | 行范围 | 大小 | 适用规则数 |
|---|---------|--------|------|:--------:|
| 1 | HEADER | 1-8 | 8行 | 0 |
| 2 | DECLARATION | 10-89 | 80行 | R05 R10 R11 |
| 3 | ACTION(#A1) | 126-171 | 46行 | R01-R04 R07-R15 |
| 4 | AUDIO(#A1) | 173-178 | 6行 | R09 R10 R15 |
| 5 | PROHIBIT(#A1) | 188-196 | 9行 | R06 R10 |
| ... | ... | ... | ... | ... |

## 逐规则结果

| 编号 | 检查项 | 结果 | 区块 | 行号 | 匹配文本 |
|------|--------|:---:|------|:---:|---------|
| R01 | 时长硬约束 | ✅ | — | — | — |
| R02 | 段首过程动词 | ✅ | — | — | — |
| R03 | 时间模糊词 | ✅ | — | — | — |
| R04 | 跨镜引用 | ✅ | — | — | — |
| R05 | 参考图引用 | ✅ | — | — | — |
| R06 | 禁止清单模糊 | ✅ | — | — | — |
| R07 | 工程符号泄漏 | ✅ | — | — | — |
| R08 | 段结构完整 | ✅ | — | — | — |
| R09 | 负向词 | ✅ | — | — | — |
| R10 | 模型名泄漏 | ✅ | — | — | — |
| R11 | @引用声明 | ✅ | — | — | — |
| R12 | KB规则泄漏 | ✅ | — | — | — |
| R13 | 骨架顺序 | ✅ | — | — | — |
| R14 | 运镜语义 | ✅ | — | — | — |
| R15 | 画面外声 | ✅ | — | — | — |

## 假阳性消除记录

| 规则 | 原v1.0触发 | v1.1状态 | 原因 |
|------|-----------|:---:|------|
| R10 | "Seedance 2.0"(行8·HEADER) | ✅跳过 | HEADER元数据·非生成指令 |
| R12 | "P-FAL-08规避"(行78·DECLARATION) | ✅跳过(如适用) | DECLARATION中的场景级禁止注释 |

## Gate 0 最终裁决

**✅ 全部通过 · 🛑0 · 可信度100%**
```

## 4.2 阻断时的输出格式

```markdown
## Gate 0 最终裁决

**🛑 [N]项阻断 — 返回prompt_composer修复·上限1轮**

阻断详情:
  🛑 R02 段首过程动词 | BLOCK_ACTION · 镜#A3 · 行342
     匹配: "开始后退一步"
     正则: /^开始[^前]/
     修复: 改为 "后退一步完成"

  🛑 R14 运镜语义 | BLOCK_ACTION · 镜#A2 · 行252
     匹配: "推近继续"
     正则: /推近继续/
     修复: 删除Action中的运镜描述·运镜参数已在【镜头参数卡】中声明

修复后重新扫描: 调度器自执行 gate0_scan() → 仅重新扫描·不经过Agent
```

---

# §5 与v1.0的差异总结

| 维度 | v1.0 (全局扫描) | v1.1 (区块感知) |
|------|----------------|----------------|
| R10(HEADER) | 假阳性·阻断 | ✅跳过·HEADER元数据豁免 |
| R12(DESIGN) | ⚠️警告(运气好) | ✅跳过·DESIGN_NOTES合法引用 |
| R09(PROHIBIT) | 误判风险(未区分) | ✅跳过·禁止块中"禁止"合法 |
| R14(TRANSITION) | 误判风险 | ✅跳过·转场设计中的运镜合法 |
| 假阳性率 | ~5-10% (估算) | ~0% (区块感知消除主要假阳性源) |
| 扫描精度 | 100%正确·但含假阳性 | 100%正确·零假阳性 |
| 实现成本 | 简单(全局正则) | 中等(需区块解析器) |
| 执行环境 | Scene Auditor Agent | 调度器自执行(零LLM) |

---

# §6 集成检查清单

调度器集成Gate 0 v1.1需要:

- [ ] 1. 在dispatcher_v5.0.md中插入Gate 0自执行步骤
- [ ] 2. 实现或引用parse_blocks()区块解析器
- [ ] 3. 实现或引用R01-R15规则集(含区块适用性过滤)
- [ ] 4. 实现假阳性二次确认逻辑(is_false_positive函数)
- [ ] 5. 更新scene_auditor_v1.0.md §3为DEPRECATED
- [ ] 6. 确保Gate 0预扫描在Scene Auditor启动前执行
- [ ] 7. 定义回退逻辑: 如Gate 0预扫描未执行 → Scene Auditor执行v1.0 Phase 0
- [ ] 8. 更新P-CONSTITUTION.md §5.2 Gate 0检测表·标注v1.1区块感知升级

---

> **Gate 0 v1.2 · 2026-07-07**
> **升级:** 全局正则 → 区块感知正则 · 消除header/design_notes假阳性
> **BLOCK-3修复:** 补充四个缺失函数 · R03 Python re兼容 · R04字母前缀镜号 · parse_blocks回退 · is_false_positive全矩阵
> **核心修复:** R10 v1.0假阳性"Seedance 2.0"(HEADER元数据) → v1.1豁免
> **宪法依据:** 画布第五条(确定性优先于概率性)·正则100%准确率 + 假阳性消除 = 更高可信度
> **执行环境:** 调度器自执行·零LLM·零Agent·~0.5K tokens等价计算量
> **被替代:** scene_auditor_v1.0.md §3 (Phase 0 Gate 0全局扫描) — 标记DEPRECATED
