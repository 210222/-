
import yaml
N=chr(10)
with open("C:/Users/JT/Desktop/枪王/场景/第二集/_pipeline/scene_design_v2.yml","r",encoding="utf-8") as f:
    d=yaml.safe_load(f)
ga=d["global_anchors"]; segs=d["time_skeleton"]
env_desc=ga.get("environment",{}).get("description","")[:300]
lit_desc=ga.get("lighting",{}).get("description","")[:200]
pal=ga.get("style_spine",{}).get("palette_anchors",[])
pal_str=" / ".join(pal) if pal else "warm amber / cool steel blue / brick red / cream / dark walnut"
sty_desc=ga.get("style_spine",{}).get("description","")

all_kb=[]
for seg in segs:
    for r in seg.get("kb_rule_ids",[]):
        if r not in all_kb: all_kb.append(r)

lines=[]
lines.append("# 黑白手绘线稿故事板 — 第2集《咖啡馆》· 场景A（Cafe da Isa）")
lines.append("")
lines.append("> **格式:** storyboard_planner §2E.4 方式C · 每秒冻结帧 · 主格式")
lines.append("> **场景:** Cafe da Isa · 凌晨5:00 — 18镜 · 168s")
lines.append("> **编号系统:** ①-⑱ = 18镜首帧冻结")
lines.append("> **颜色标注:** 🔴红=身体运动 🔵蓝=相机运动 🟢绿=构图 🟠橙=光线 ⚫黑=时间+景别+运镜")
lines.append("> **生成策略:** 黑白手绘线稿 → 上传模型作为分镜构图参考")
lines.append("> **管道:** MODE:P v7.0")
lines.append("> **生成日期:** 2026-07-08")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 场景A: Cafe da Isa — 18镜 · 168s")
lines.append("")

with open("C:/Users/JT/Desktop/枪王/场景/第二集/STORYBOARD_EP2_Cafe.md","w",encoding="utf-8") as f:
    f.write(N.join(lines))
print("Header written")
