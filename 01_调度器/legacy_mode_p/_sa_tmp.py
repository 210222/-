import yaml, re, argparse

def load_plan(p):
    with open(p,encoding="utf-8") as f: d=yaml.safe_load(f)
    return d.get("scene",{}), d.get("global_anchors",{}), d.get("time_skeleton",[])

LIGHT={"A":"L1+L4","B":"L2+L5","C":"L4+L2","D":"L3+L4","AD":"L1->L3"}
MODEL={("CU",0):"Jimeng4",("MS",0):"Jimeng4/VEO",("WS",0):"Kling/VEO",("MS",1):"Hailuo"}
REF={("D","WS"):"@bar_wide",("D","MS"):"@bar_mid",("D","CU"):"@bar_cu",("B","CU"):"@window_cu",("A","MS"):"@door_mid"}
CH={"#1":[],"#2":["I"],"#3":[],"#4":["I"],"#5":["S"],"#6":["I","S"],"#7":["I"],"#8":[],"#9":["R"],"#10":["I"],"#11":["R","I"],"#12":["R"],"#13":["I"],"#14":["R"],"#15":[],"#16":["B"],"#17":["I","R"],"#18":[]}
PFAL_G=["no txt","no mm","no pupil","no sub-sec"]
PFAL_CU=["no face drift"]; PFAL_WS=["max2 audio"]; PFAL_DLG=["no2+mouth"]; PFAL_SCR=["no rendered txt"]; PFAL_MOV=["no limb deform"]; PFAL_WIN=["no flicker"]
DLG_S={"#6","#10","#12","#13","#14","#15","#17"}

def zone(pos):
    if "A" in pos: return "AD" if ("bar" in pos.lower() or "counter" in pos.lower()) else "A"
    for z in ["B","C","D"]:
        if z in pos: return z
    return "D"

def stk(st):
    if "te" in st or "jin" in st: return "CU"
    if "zhong" in st: return "MS"
    if "quan" in st: return "WS"
    return "MS"

def wc(t): return len(re.sub(r"[\s,.;:?!()]","",t))

def card(seg):
    mt=not seg.get("actor_fixed",True); sk=stk(seg.get("shot_type",""))
    mod=MODEL.get((sk,mt),"Jimeng4")
    ls=[f"-Shot:{seg.get("shot_type","")}",f"-Focal:{seg.get("focal_length","")}",f"-Aperture:{seg.get("dof","")}",f"-Angle:{seg.get("angle","")}",f"-Camera:{seg.get("camera_type","")}",f"-Position:{seg.get("camera_position","")}",f"-Movement:{seg.get("movement","static")}({seg.get("movement_speed_tier","S0")})",f"-Axis:{seg.get("axis_side","A")}",f"-Model:{mod}"]
    kb=seg.get("kb_rule_ids",[])
    if kb: ls.append(f"-KB:{chr(44).join(kb)}")
    return "
".join(ls)

def refs(seg):
    z=zone(seg.get("camera_position","")); sk=stk(seg.get("shot_type","")); stk2="ECU" if "te" in seg.get("shot_type","") else sk
    k=(z,stk2); r=[]
    if k in REF: r.append(REF[k])
    else:
        for (zz,sst),rr in REF.items():
            if zz==z: r.append(rr); break
    if not r: r.append("@scene_ref")
    return "
".join(r)

def frames(seg,ga,dial):
    sid=seg.get("shot_id",""); dur=seg.get("duration_s",6); start=seg.get("global_sec_start",0)
    z=zone(seg.get("camera_position","")); lit=LIGHT.get(z,"L3"); chars=CH.get(sid,[])
    sps=seg.get("actor_movement",{}).get("sub_phases",[])
    ls=[f"#CAM:{seg.get("angle","")} {seg.get("camera_type","")} static" if seg.get("camera_fixed",True) else f"#CAM:{seg.get("movement","")}",f"#ZONE:{z} | {seg.get("camera_position","")[:50]}",f"#LIGHT:{lit}",f"#CHARS:{chr(44).join(chars) if chars else "none"}"]
    if dial:
        ls.append("#DIALOGUE:")
        for d in dial: ls.append(f"#  {d[chr(115)]}: "{d[chr(116)][:40]}" @~{start+d.get(chr(111),0.5)*dur:.0f}s")
    ls.append("")
    if sps:
        for sp in sps: ls.append(f"{sp.get(chr(103)+chr(108)+chr(111)+chr(98)+chr(97)+chr(108)+chr(95)+chr(115)+chr(101)+chr(99),0)}s: [{sp.get(chr(108)+chr(105)+chr(103)+chr(104)+chr(116)+chr(105)+chr(110)+chr(103),chr(34)+chr(34))}] {sp.get(chr(100)+chr(101)+chr(115)+chr(99)+chr(114)+chr(105)+chr(112)+chr(116)+chr(105)+chr(111)+chr(110),chr(34)+chr(34))}")
    else:
        if dur<=6: rng=[(0,dur)]
        elif dur<=10: h=dur//2; rng=[(0,h),(h,dur)]
        else: r3=dur//3; rng=[(0,r3),(r3,2*r3),(2*r3,dur)]
        for s,e in rng:
            a,b=start+s,start+e-1; sd=[d for d in dial if s<=d.get(chr(111),0.5)*dur<e]
            cam_status = chr(115)+chr(116)+chr(97)+chr(116)+chr(105)+chr(99) if seg.get(chr(99)+chr(97)+chr(109)+chr(101)+chr(114)+chr(97)+chr(95)+chr(102)+chr(105)+chr(120)+chr(101)+chr(100),True) else seg.get(chr(109)+chr(111)+chr(118)+chr(101)+chr(109)+chr(101)+chr(110)+chr(116),chr(115)+chr(116)+chr(97)+chr(116)+chr(105)+chr(99))
            ls.append(f"{a}-{b}s: [{seg.get(chr(115)+chr(104)+chr(111)+chr(116)+chr(95)+chr(116)+chr(121)+chr(112)+chr(101),chr(34)+chr(34))} {cam_status}] {seg.get(chr(102)+chr(111)+chr(99)+chr(97)+chr(108)+chr(95)+chr(108)+chr(101)+chr(110)+chr(103)+chr(116)+chr(104),chr(34)+chr(34))} {seg.get(chr(100)+chr(111)+chr(102),chr(34)+chr(34))} light:{lit}")
            for d in sd: ls.append(f"  CV:{d[chr(115)]} "{d[chr(116)][:40]}"")
            ls.append("")
    return "
".join(ls)