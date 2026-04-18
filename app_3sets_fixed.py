import json
import os
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import streamlit as st
from streamlit_autorefresh import st_autorefresh

SUPABASE_OK = False
try:
    from supabase import create_client
    SUPABASE_OK = True
except Exception:
    create_client = None

ROOT_ADMIN_USER = "Ballbadminton"
ROOT_ADMIN_PASS = "partha@2025"

SET_POINTS    = 35
PLAYERS       = 5
ALL_PLAYERS   = 10
COURT_CHG     = [9, 18, 27]
MAX_SCORE_CAP = 39
DATA_FILE     = "bb_data.json"
USERS_FILE    = "bb_users.json"

st.set_page_config(
    page_title="🏸 Ball Badminton Live",
    page_icon="🏸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600;700;800&display=swap');
#MainMenu,header,footer,
[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stStatusWidget"],.stDeployButton,
section[data-testid="stSidebar"],[data-testid="stSidebarNav"],
a[href*="streamlit.io"],a[href*="github.com"]{display:none!important;}
:root{
  --bg:#07101f;--surf:#0d1a2e;--card:#112038;
  --bdr:rgba(255,255,255,.07);
  --acc:#f97316;--acc2:#c2410c;--blue:#3b82f6;
  --txt:#f0f4f8;--muted:#5a7090;
}
html,body,.stApp{background:var(--bg)!important;color:var(--txt)!important;font-family:'Inter',sans-serif!important;}
.block-container{max-width:100%!important;padding:.45rem .55rem 5rem!important;}

/* ── BUTTONS ── */
.stButton>button{
  background:linear-gradient(135deg,var(--acc),var(--acc2))!important;
  color:#fff!important;border:none!important;font-weight:800!important;
  border-radius:12px!important;width:100%!important;padding:.65rem .8rem!important;
  transition:all .12s!important;
}
.stButton>button:hover{transform:translateY(-1px)!important;opacity:.92!important;}
.stButton>button:disabled{opacity:.4!important;transform:none!important;}
.blue .stButton>button{background:linear-gradient(135deg,#3b82f6,#1d4ed8)!important;}
.green .stButton>button{background:linear-gradient(135deg,#22c55e,#15803d)!important;}
.grey .stButton>button{background:linear-gradient(135deg,#334155,#1e293b)!important;}
.big .stButton>button{padding:1.1rem .7rem!important;font-size:19px!important;border-radius:14px!important;}
.small .stButton>button{padding:.4rem .5rem!important;font-size:12px!important;}

/* ── INPUTS ── */
.stTextInput input,.stSelectbox>div>div,.stMultiSelect>div>div,.stNumberInput input{
  background:var(--card)!important;color:var(--txt)!important;
  border:1px solid var(--bdr)!important;border-radius:10px!important;
}
.stTextInput input::placeholder{color:var(--muted)!important;}
.stRadio label{color:var(--txt)!important;}

/* ── CONTAINER ── */
[data-testid="stContainer"]{
  background:var(--card)!important;border:1px solid var(--bdr)!important;
  border-radius:14px!important;padding:12px!important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{background:var(--surf)!important;border-radius:10px!important;padding:4px!important;gap:3px!important;}
.stTabs [data-baseweb="tab"]{color:var(--muted)!important;border-radius:8px!important;font-weight:700!important;padding:7px 12px!important;font-size:12px!important;}
.stTabs [aria-selected="true"]{background:var(--acc)!important;color:#fff!important;}

/* ── METRICS ── */
[data-testid="stMetricValue"]{color:var(--txt)!important;font-weight:800!important;}
[data-testid="stMetricLabel"]{color:var(--muted)!important;}

/* ── SCOREBOARD ── */
.scoreboard{
  background:linear-gradient(135deg,var(--surf),var(--card));
  border:1px solid rgba(249,115,22,.15);
  border-radius:18px;padding:16px 14px 14px;
  position:relative;overflow:hidden;
}
.scoreboard::before{
  content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--acc),#f59e0b,var(--acc));
}
.score-num{font-size:84px;line-height:1;font-weight:900;color:#fff;}
.score-num.hot{color:var(--acc);text-shadow:0 0 28px rgba(249,115,22,.4);}
.tname{font-size:17px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.tmeta{font-size:12px;color:var(--muted);}

/* ── ALERTS ── */
.court-alert{
  background:rgba(249,115,22,.1);border:2px solid rgba(249,115,22,.4);
  border-radius:12px;padding:12px 14px;font-weight:800;color:#fdba74;
  margin-bottom:8px;text-align:center;font-size:15px;
  animation:pulse-bdr 1.2s ease-in-out infinite;
}
@keyframes pulse-bdr{0%,100%{box-shadow:0 0 0 0 rgba(249,115,22,.3);}50%{box-shadow:0 0 0 6px rgba(249,115,22,.05);}}
.win-banner{
  background:linear-gradient(135deg,#f59e0b,#d97706);
  border-radius:14px;padding:14px;text-align:center;
  font-weight:900;font-size:22px;margin-bottom:8px;
  box-shadow:0 6px 20px rgba(245,158,11,.35);
}
.new-match-hint{
  background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.25);
  border-radius:10px;padding:10px;text-align:center;
  color:#86efac;font-weight:600;font-size:13px;margin-top:8px;
}

/* ── EVENT FEED ── */
.ev{font-size:11px;padding:5px 4px;border-bottom:1px solid var(--bdr);color:var(--muted);}
.ev:first-child{color:#fff;font-weight:700;}

/* ── STAT BOX ── */
.box{background:#0d1a2e;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:10px;text-align:center;}
.box .n{font-size:28px;font-weight:900;color:#f97316;}
.box .l{font-size:10px;color:#5a7090;text-transform:uppercase;}

/* ── SET CARD ── */
.set-card{background:var(--surf);border:1px solid var(--bdr);border-radius:10px;padding:8px;text-align:center;}

/* ── MOBILE ── */
@media(max-width:768px){
  .block-container{padding:.35rem .4rem 5rem!important;}
  .score-num{font-size:64px!important;}
  .tname{font-size:14px!important;}
  .big .stButton>button{font-size:16px!important;padding:.85rem .6rem!important;}
  .small .stButton>button{font-size:11px!important;padding:.36rem .4rem!important;}
}
@media(max-width:900px) and (orientation:landscape){
  .score-num{font-size:54px!important;}
  .scoreboard{padding:10px 12px!important;}
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════
#  SUPABASE
# ═══════════════════════════════════════════
@st.cache_resource
def get_supabase():
    if not SUPABASE_OK:
        return None
    try:
        return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
    except Exception:
        return None


# ═══════════════════════════════════════════
#  UTILS
# ═══════════════════════════════════════════
def now_str():  return datetime.now().strftime("%d %b %Y %H:%M:%S")
def now_short():return datetime.now().strftime("%d %b %Y %H:%M")
def _hash(v):   return hashlib.sha256(v.encode()).hexdigest()
def _safe(v,fb):v=(v or "").strip(); return v if v else fb
def _nxt(i,n):  return (i+1)%n

def _build_ord(p5, idxs):
    out=[]
    for idx in idxs:
        if not (1<=idx<=len(p5)): return []
        out.append(p5[idx-1])
    return out

def _new_mid(user): return f"{user}_{datetime.now().strftime('%Y%m%d%H%M%S')}"


# ═══════════════════════════════════════════
#  USER STORE
# ═══════════════════════════════════════════
def users_load() -> dict:
    sb = get_supabase()
    if sb:
        try:
            res = sb.table("viewers").select("*").execute()
            out = {}
            for row in (res.data or []):
                out[row["username"]] = {
                    "name": row.get("name",""),
                    "contact": row.get("contact",""),
                    "pw_hash": row.get("pw_hash",""),
                    "created": row.get("created_at",""),
                    "created_by_admin": row.get("created_by_admin", False),
                    "is_admin": row.get("is_admin", False),
                }
            return out
        except Exception:
            pass
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def users_save(users: dict):
    sb = get_supabase()
    if sb:
        try:
            rows = []
            for uname,u in users.items():
                rows.append({
                    "username": uname,
                    "name": u.get("name",""),
                    "contact": u.get("contact",""),
                    "pw_hash": u.get("pw_hash",""),
                    "created_at": u.get("created",""),
                    "created_by_admin": u.get("created_by_admin",False),
                    "is_admin": u.get("is_admin",False),
                })
            if rows:
                sb.table("viewers").upsert(rows).execute()
            return
        except Exception:
            pass
    with open(USERS_FILE,"w",encoding="utf-8") as f:
        json.dump(users,f,indent=2)

def user_register(name,contact,username,password,created_by_admin=False,is_admin=False):
    users=users_load()
    uname=(username or "").strip().lower()
    if not uname or not name or not contact or not password:
        return False,"All fields are required"
    if len(password)<6:
        return False,"Password min 6 chars"
    if uname in users or uname==ROOT_ADMIN_USER.lower():
        return False,"Username already exists"
    users[uname]={"name":name.strip(),"contact":contact.strip(),"pw_hash":_hash(password),
                  "created":now_short(),"created_by_admin":created_by_admin,"is_admin":is_admin}
    users_save(users)
    return True,f"Created '{uname}'"

def user_login(username,password):
    uname=(username or "").strip().lower()
    if uname==ROOT_ADMIN_USER.lower() and password==ROOT_ADMIN_PASS:
        return True,"OK",{"name":"Root Admin","is_admin":True,"root":True}
    users=users_load()
    if uname not in users: return False,"Username not found",{}
    u=users[uname]
    if u["pw_hash"]!=_hash(password): return False,"Wrong password",{}
    return True,"OK",u


# ═══════════════════════════════════════════
#  DATA LAYER
# ═══════════════════════════════════════════
def data_default():
    return {"matches":{},"history":[],"updated_at":""}

def data_load():
    sb=get_supabase()
    if sb:
        try:
            res=sb.table("matches").select("*").eq("id","app_state").execute()
            if res.data:
                payload=res.data[0].get("data") or {}
                base=data_default(); base.update(payload); return base
        except Exception:
            pass
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE,"r",encoding="utf-8") as f:
                d=json.load(f)
            base=data_default(); base.update(d); return base
        except Exception:
            pass
    return data_default()

def data_save(data:dict):
    data["updated_at"]=now_str()
    sb=get_supabase()
    if sb:
        try:
            sb.table("matches").upsert({
                "id":"app_state","data":data,
                "updated_at":datetime.now().isoformat()
            }).execute()
            return
        except Exception:
            pass
    tmp=DATA_FILE+".tmp"
    with open(tmp,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False)
    os.replace(tmp,DATA_FILE)


# ═══════════════════════════════════════════
#  MATCH DATACLASS
# ═══════════════════════════════════════════
@dataclass
class Match:
    id:str; created_by:str
    tA:str; tB:str
    allA:List[str]; allB:List[str]
    onA:List[str]; onB:List[str]
    ordA:List[str]; ordB:List[str]
    setno:int; sA:int; sB:int; scA:int; scB:int
    srv:str; swapped:bool
    curA:Optional[str]; curB:Optional[str]
    nxtA:int; nxtB:int
    subA:int; subB:int; toA:int; toB:int
    ms:Dict[int,bool]
    pending_cc:Optional[int]        # court change milestone point
    pending_cc_team:Optional[str]   # which team first reached it
    history:List[Dict]; events:List[str]
    over:bool; winner:Optional[str]
    psA:List[int]; psB:List[int]
    ppA:Dict[str,int]; ppB:Dict[str,int]
    started:str; ended:Optional[str]
    tnm:Optional[str]; trd:Optional[str]
    target:int; updated_at:Optional[str]

def _restore(d) -> Optional[Match]:
    if not d: return None
    try:
        dd=dict(d)
        # backwards compat migrations
        dd.setdefault("pending_cc", dd.pop("first_court_popup_point", None))
        dd.setdefault("pending_cc_team", dd.pop("first_court_popup_team", None))
        dd.pop("show_court_popup", None)   # old field — remove
        return Match(**dd)
    except Exception as e:
        return None

def _snap(m:Match):
    d=asdict(m); d["history"]=[]; return d

def cur_srv(m:Match):
    return (m.curA if m.srv=="A" else m.curB) or "—"

def maybe_update_target(m:Match):
    if m.scA==m.scB:
        if m.scA>=36:   m.target=39
        elif m.scA>=34: m.target=36
        else:           m.target=35

def new_match(mid,created_by,tA,tB,allA,allB,pA,pB,oA,oB,first,tnm=None,trd=None) -> Match:
    cA,cB,nA,nB=(oA[0],None,1,0) if first=="A" else (None,oB[0],0,1)
    return Match(
        id=mid,created_by=created_by,tA=tA,tB=tB,allA=allA,allB=allB,
        onA=pA,onB=pB,ordA=oA,ordB=oB,
        setno=1,sA=0,sB=0,scA=0,scB=0,
        srv=first,swapped=False,curA=cA,curB=cB,nxtA=nA,nxtB=nB,
        subA=3,subB=3,toA=1,toB=1,
        ms={9:False,18:False,27:False},
        pending_cc=None,pending_cc_team=None,
        history=[],events=[f"Match started · {tA if first=='A' else tB} serves first"],
        over=False,winner=None,psA=[],psB=[],
        ppA={p:0 for p in pA},ppB={p:0 for p in pB},
        started=now_short(),ended=None,tnm=tnm,trd=trd,
        target=35,updated_at=now_str()
    )


# ═══════════════════════════════════════════
#  MATCH ACTIONS — all load fresh from disk
# ═══════════════════════════════════════════
def save_match(m:Match,data:dict):
    data["matches"][m.id]=asdict(m)
    data_save(data)

def delete_match(mid:str,data:dict):
    data["matches"].pop(mid,None)
    data_save(data)

def list_matches(data:dict) -> List[Match]:
    items=[]
    for _,raw in (data.get("matches") or {}).items():
        m=_restore(raw)
        if m: items.append(m)
    items.sort(key=lambda x:x.updated_at or "",reverse=True)
    return items

def action_point(mid:str,winner:str):
    data=data_load()
    m=_restore(data["matches"].get(mid))
    if not m or m.over: return
    had_pending_cc = m.pending_cc is not None
    m.history.append(_snap(m)); m.history=m.history[-20:]
    if winner=="A":
        if m.scA>=MAX_SCORE_CAP: return
        m.scA+=1
        if m.curA: m.ppA[m.curA]=m.ppA.get(m.curA,0)+1
    else:
        if m.scB>=MAX_SCORE_CAP: return
        m.scB+=1
        if m.curB: m.ppB[m.curB]=m.ppB.get(m.curB,0)+1
    if winner!=m.srv:
        m.srv=winner
        if winner=="A": m.curA=m.ordA[m.nxtA]; m.nxtA=_nxt(m.nxtA,PLAYERS)
        else:           m.curB=m.ordB[m.nxtB]; m.nxtB=_nxt(m.nxtB,PLAYERS)
    m.events.insert(0,f"▸ {m.tA if winner=='A' else m.tB}  {m.scA}–{m.scB}  srv:{cur_srv(m)}")
    m.events=m.events[:60]
    if had_pending_cc:
        m.pending_cc=None
        m.pending_cc_team=None
    # ── Court change: trigger only once per milestone for the FIRST team to reach it ──
    if m.pending_cc is None:
        for p in COURT_CHG:
            if not m.ms.get(p, False):
                if m.scA == p and m.scB < p:
                    m.ms[p] = True
                    m.pending_cc = p
                    m.pending_cc_team = "A"
                    m.events.insert(0,f"🔄 Court change at {p} · {m.tA} first reached")
                    break
                elif m.scB == p and m.scA < p:
                    m.ms[p] = True
                    m.pending_cc = p
                    m.pending_cc_team = "B"
                    m.events.insert(0,f"🔄 Court change at {p} · {m.tB} first reached")
                    break
    maybe_update_target(m)
    if m.target==39 and (m.scA==39 or m.scB==39):
        m.over=True; m.winner="A" if m.scA==39 else "B"
    elif max(m.scA,m.scB)>=m.target and abs(m.scA-m.scB)>=2:
        sw="A" if m.scA>m.scB else "B"
        if sw=="A": m.sA+=1
        else:       m.sB+=1
        m.psA.append(m.scA); m.psB.append(m.scB)
        m.events.insert(0,f"✅ Set {m.setno} → {m.tA if sw=='A' else m.tB} ({m.scA}–{m.scB})")
        if m.setno >= 3:
            m.over=True
            m.winner="A" if m.sA>m.sB else "B"
        else:
            m.setno+=1; m.scA=0; m.scB=0
            m.subA=3; m.subB=3; m.toA=1; m.toB=1
            m.ms={9:False,18:False,27:False}
            m.pending_cc=None; m.pending_cc_team=None
            m.target=35
            m.events.insert(0,f"▶️ Set {m.setno} begins")
    if m.over and not m.ended:
        m.ended=now_short()
        m.events.insert(0,f"🏆 {m.tA if m.winner=='A' else m.tB} wins!")
        data["history"].append({
            "id":m.id,"date":m.started,"tA":m.tA,"tB":m.tB,
            "sA":m.sA,"sB":m.sB,
            "winner":m.tA if m.winner=="A" else m.tB,
            "tnm":m.tnm,"trd":m.trd,
            "set_scores":list(zip(m.psA,m.psB)),
            "player_points_A":dict(m.ppA),"player_points_B":dict(m.ppB),
            "created_by":m.created_by,
        })
    m.updated_at=now_str()
    save_match(m,data)

def action_undo(mid:str):
    data=data_load()
    m=_restore(data["matches"].get(mid))
    if not m or not m.history: return
    prev=m.history.pop()
    data["matches"][mid]=prev
    data_save(data)

def action_court(mid:str):
    data=data_load()
    m=_restore(data["matches"].get(mid))
    if not m: return
    m.swapped=not m.swapped
    m.pending_cc=None; m.pending_cc_team=None
    m.events.insert(0,"🔄 Court changed — confirmed")
    m.updated_at=now_str()
    save_match(m,data)

def action_timeout(mid:str,team:str):
    data=data_load()
    m=_restore(data["matches"].get(mid))
    if not m: return
    if team=="A" and m.toA>0:
        m.toA-=1; m.events.insert(0,f"⏱️ Timeout: {m.tA}")
    elif team=="B" and m.toB>0:
        m.toB-=1; m.events.insert(0,f"⏱️ Timeout: {m.tB}")
    m.updated_at=now_str()
    save_match(m,data)

def action_sub(mid:str,team:str,on:str,off:str):
    data=data_load()
    m=_restore(data["matches"].get(mid))
    if not m or not on or not off or on==off: return
    if team=="A":
        if m.subA<=0 or on in m.onA or off not in m.onA: return
        m.onA[m.onA.index(off)]=on; m.ppA.setdefault(on,0); m.subA-=1
        m.events.insert(0,f"🔁 {m.tA}: {off}→{on}")
    else:
        if m.subB<=0 or on in m.onB or off not in m.onB: return
        m.onB[m.onB.index(off)]=on; m.ppB.setdefault(on,0); m.subB-=1
        m.events.insert(0,f"🔁 {m.tB}: {off}→{on}")
    m.updated_at=now_str()
    save_match(m,data)

def action_adjust(mid:str,team:str,val:int):
    data=data_load()
    m=_restore(data["matches"].get(mid))
    if not m or m.over: return
    val=max(0,min(MAX_SCORE_CAP,int(val)))
    if team=="A": m.scA=val
    else:         m.scB=val
    maybe_update_target(m)
    m.events.insert(0,f"✏️ Score → {m.tA} {m.scA} · {m.tB} {m.scB}")
    m.updated_at=now_str()
    save_match(m,data)


# ═══════════════════════════════════════════
#  SESSION INIT
# ═══════════════════════════════════════════
for k,v in [
    ("role",None),("username",""),("user_name",""),("tab","score"),
    ("sel_mid",None),("show_adj",False),("show_subs",False),
    # setup wizard state (kept outside form so widgets work)
    ("sw_tA",""),("sw_tB",""),
    ("sw_allA",[""]*ALL_PLAYERS),("sw_allB",[""]*ALL_PLAYERS),
    ("sw_tnm",""),("sw_trd",""),
    ("sw_step",1),   # 1=teams/players, 2=starters+order+serve
]:
    if k not in st.session_state: st.session_state[k]=v


# ═══════════════════════════════════════════
#  LOGIN PAGE
# ═══════════════════════════════════════════
if st.session_state.role is None:
    st.markdown("""
    <div style='text-align:center;padding:24px 0 12px'>
      <div style='font-size:56px'>🏸</div>
      <div style='font-family:Bebas Neue,sans-serif;font-size:36px;letter-spacing:3px'>BALL BADMINTON LIVE</div>
      <div style='color:#5a7090;font-size:12px'>Mobile Scoreboard</div>
    </div>
    """, unsafe_allow_html=True)

    t1,t2,t3 = st.tabs(["🔑 Viewer Login","📝 Register","🔐 Admin"])

    with t1:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        vu = st.text_input("Username", placeholder="Your username", key="vu")
        vp = st.text_input("Password", placeholder="Your password", type="password", key="vp")
        if st.button("▶️ Open Live Score", use_container_width=True, key="viewer_login"):
            ok,msg,u = user_login(vu,vp)
            if ok and not u.get("is_admin") and not u.get("root"):
                st.session_state.role="viewer"
                st.session_state.username=(vu or "").strip().lower()
                st.session_state.user_name=u.get("name","Viewer")
                st.rerun()
            elif ok:
                st.error("This is an admin account — use Admin tab")
            else:
                st.error(msg)
        st.caption("No account? Register using the Register tab.")

    with t2:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        rn  = st.text_input("Full Name", placeholder="Your name", key="rn")
        rc  = st.text_input("Mobile / Email", placeholder="9876543210 or abc@email.com", key="rc")
        ru  = st.text_input("Username", placeholder="e.g. john_viewer", key="ru")
        rp  = st.text_input("Password", placeholder="Min 6 characters", type="password", key="rp")
        rp2 = st.text_input("Confirm Password", placeholder="Re-enter password", type="password", key="rp2")
        if st.button("✅ Create Account", use_container_width=True, key="reg_btn"):
            if rp!=rp2: st.error("Passwords do not match")
            else:
                ok,msg=user_register(rn,rc,ru,rp,created_by_admin=False,is_admin=False)
                if ok: st.success(f"✅ {msg} — now login above")
                else:  st.error(f"❌ {msg}")

    with t3:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        au = st.text_input("Admin Username", placeholder="Admin username", key="au")
        ap = st.text_input("Admin Password", placeholder="Admin password", type="password", key="ap")
        if st.button("🔐 Admin Login", use_container_width=True, key="admin_login"):
            ok,msg,u = user_login(au,ap)
            if ok and (u.get("is_admin") or u.get("root")):
                st.session_state.role="admin"
                st.session_state.username=(au or "").strip().lower()
                st.session_state.user_name=u.get("name","Admin")
                st.rerun()
            elif ok:
                st.error("Viewer-only account — use Viewer Login tab")
            else:
                st.error(msg)
    st.stop()


# ═══════════════════════════════════════════
#  VIEWER
# ═══════════════════════════════════════════
if st.session_state.role=="viewer":
    st_autorefresh(interval=2500,key="vr")
    data=data_load()
    matches=list_matches(data)

    st.markdown(f"<div style='font-size:11px;color:#5a7090;margin-bottom:6px'>👤 {st.session_state.user_name} · Auto-refresh ON</div>", unsafe_allow_html=True)

    # Logout
    if st.button("🚪 Logout", key="v_logout", use_container_width=False):
        st.session_state.role=None; st.rerun()

    if not matches:
        st.info("⏳ No live matches right now. Check back soon!")
        st.stop()

    opts = {f"{m.tA} vs {m.tB}{' · '+m.tnm if m.tnm else ''} [{m.id[-6:]}]": m.id for m in matches}
    labels=list(opts.keys())
    cur=st.session_state.sel_mid
    idx=0
    for i,lbl in enumerate(labels):
        if opts[lbl]==cur: idx=i; break
    picked=st.selectbox("Select Match",labels,index=idx,key="v_pick")
    st.session_state.sel_mid=opts[picked]

    m=_restore(data["matches"][st.session_state.sel_mid])
    if not m: st.stop()

    # Court change alert
    if m.pending_cc is not None:
        first_team=m.tA if m.pending_cc_team=="A" else m.tB
        st.markdown(f"<div class='court-alert'>🔄 COURT CHANGE — <b>{first_team}</b> reached <b>{m.pending_cc}</b> first!</div>", unsafe_allow_html=True)

    if m.over:
        st.markdown(f"<div class='win-banner'>🏆 {m.tA if m.winner=='A' else m.tB} WINS!</div>", unsafe_allow_html=True)

    lt="B" if m.swapped else "A"
    rt="A" if m.swapped else "B"
    tn=lambda t:m.tA if t=="A" else m.tB
    sc=lambda t:m.scA if t=="A" else m.scB
    ss=lambda t:m.sA if t=="A" else m.sB

    st.markdown(f"""
    <div class='scoreboard'>
      <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:10px'>
        <div style='flex:1;min-width:0'>
          <div class='tname'>{'🟠 ' if m.srv==lt else ''}{tn(lt)}</div>
          <div class='score-num {"hot" if m.srv==lt else ""}'>{sc(lt)}</div>
          <div class='tmeta'>Sets: {ss(lt)} · Left</div>
        </div>
        <div style='opacity:.32;font-size:18px;font-weight:700'>vs</div>
        <div style='flex:1;min-width:0;text-align:right'>
          <div class='tname'>{'🟠 ' if m.srv==rt else ''}{tn(rt)}</div>
          <div class='score-num {"hot" if m.srv==rt else ""}'>{sc(rt)}</div>
          <div class='tmeta'>Sets: {ss(rt)} · Right</div>
        </div>
      </div>
      <div style='text-align:center;color:#5a7090;font-size:10px;margin-top:8px'>
        SET {m.setno}/3 · TARGET {m.target} · CAP {MAX_SCORE_CAP}
      </div>
    </div>
    """, unsafe_allow_html=True)

    if m.psA:
        cols=st.columns(len(m.psA))
        for i,(a,b) in enumerate(zip(m.psA,m.psB)):
            with cols[i]:
                st.markdown(f"<div class='set-card'><div style='font-size:9px;color:#5a7090'>SET {i+1}</div><div style='font-size:18px;font-weight:800'>{a}–{b}</div></div>", unsafe_allow_html=True)

    c1,c2,c3=st.columns(3)
    with c1: st.metric("Serving",m.tA if m.srv=="A" else m.tB)
    with c2: st.metric("Server",cur_srv(m))
    with c3: st.metric("Target",m.target)

    # Viewer tabs
    vt1,vt2,vt3=st.tabs(["📋 Events","📊 Stats","📜 History"])
    with vt1:
        for e in m.events[:14]:
            st.markdown(f"<div class='ev'>{e}</div>", unsafe_allow_html=True)
    with vt2:
        p1,p2=st.columns(2)
        with p1:
            st.markdown(f"**{m.tA}**")
            for p,pts in sorted(m.ppA.items(),key=lambda x:-x[1]):
                st.write(f"{p}: {pts}")
        with p2:
            st.markdown(f"**{m.tB}**")
            for p,pts in sorted(m.ppB.items(),key=lambda x:-x[1]):
                st.write(f"{p}: {pts}")
    with vt3:
        mhist=[h for h in data.get("history",[]) if h.get("id")==m.id]
        if mhist:
            for h in reversed(mhist):
                with st.container(border=True):
                    st.write(f"**Winner:** {h['winner']} · Sets {h['sA']}–{h['sB']}")
                    st.write(f"Set scores: {h.get('set_scores')}")
        else:
            st.info("Match not completed yet.")
    st.stop()


# ═══════════════════════════════════════════
#  ADMIN NAV
# ═══════════════════════════════════════════
nav_items=[("score","🏸 Score"),("stats","📊 Stats"),("history","📜 History"),("users","👥 Users"),("admin","⚙️ Admin")]
nav_cols=st.columns(len(nav_items)+2)
for i,(k,lbl) in enumerate(nav_items):
    with nav_cols[i]:
        if st.button(lbl,key=f"nav_{k}",use_container_width=True):
            st.session_state.tab=k; st.rerun()
with nav_cols[-2]:
    if st.button("🆕 New Match",key="nav_new",use_container_width=True):
        st.session_state.sel_mid=None
        st.session_state.sw_step=1
        st.session_state.sw_tA=""; st.session_state.sw_tB=""
        st.session_state.sw_allA=[""]*ALL_PLAYERS
        st.session_state.sw_allB=[""]*ALL_PLAYERS
        st.session_state.sw_tnm=""; st.session_state.sw_trd=""
        st.session_state.tab="score"
        st.rerun()
with nav_cols[-1]:
    if st.button("🚪 Exit",key="nav_exit",use_container_width=True):
        st.session_state.role=None; st.rerun()

st.markdown("<hr style='border-color:rgba(255,255,255,.06);margin:4px 0 8px'>", unsafe_allow_html=True)
tab=st.session_state.tab

data=data_load()
matches=list_matches(data)
admin_matches=[m for m in matches if m.created_by==st.session_state.username or st.session_state.username==ROOT_ADMIN_USER.lower()]

# ── Match selector ──
with st.container(border=True):
    if admin_matches:
        opts={"<Create New Match>":None}
        for m in admin_matches:
            label=f"{m.tA} vs {m.tB}"
            if m.tnm: label+=f" · {m.tnm}"
            label+=f" [{m.id[-6:]}]"
            if m.over: label+=" ✅"
            opts[label]=m.id
        labels=list(opts.keys())
        idx=0; cur=st.session_state.sel_mid
        for i,lbl in enumerate(labels):
            if opts[lbl]==cur: idx=i; break
        picked=st.selectbox("Your Matches",labels,index=idx,key="admin_pick")
        new_sel=opts[picked]
        if new_sel!=st.session_state.sel_mid:
            st.session_state.sel_mid=new_sel; st.rerun()
    else:
        st.info("No matches yet. Click **🆕 New Match** to create one.")
        st.session_state.sel_mid=None

sel_mid=st.session_state.sel_mid
selected=_restore(data["matches"].get(sel_mid)) if sel_mid and sel_mid in data.get("matches",{}) else None


# ═══════════════════════════════════════════════════════════
#  ADMIN SCORE TAB
# ═══════════════════════════════════════════════════════════
if tab=="score":

    # ── SETUP WIZARD (no st.form — fixes START MATCH button) ──
    if selected is None:
        st.markdown("<div style='font-family:Bebas Neue,sans-serif;font-size:26px;letter-spacing:2px;margin-bottom:10px'>NEW MATCH SETUP</div>", unsafe_allow_html=True)

        step=st.session_state.sw_step

        # ── STEP 1: Teams & Players ──
        if step==1:
            with st.container(border=True):
                st.markdown("**Step 1 of 2 — Teams & Players**")
                cx,cy=st.columns(2)
                with cx: st.session_state.sw_tnm=st.text_input("Tournament Name (optional)",value=st.session_state.sw_tnm,placeholder="e.g. State Championship",key="s1_tnm")
                with cy: st.session_state.sw_trd=st.text_input("Round (optional)",value=st.session_state.sw_trd,placeholder="e.g. Final",key="s1_trd")
                c1,c2=st.columns(2)
                with c1: st.session_state.sw_tA=st.text_input("Team A Name",value=st.session_state.sw_tA,placeholder="Team A",key="s1_tA")
                with c2: st.session_state.sw_tB=st.text_input("Team B Name",value=st.session_state.sw_tB,placeholder="Team B",key="s1_tB")

                st.markdown("**Enter all 10 players per team:**")
                ca,cb=st.columns(2)
                with ca:
                    st.markdown(f"**{st.session_state.sw_tA or 'Team A'}**")
                    for i in range(ALL_PLAYERS):
                        st.session_state.sw_allA[i]=st.text_input(
                            f"Player {i+1}",value=st.session_state.sw_allA[i],
                            placeholder=f"Player {i+1}",key=f"s1_pA{i}"
                        )
                with cb:
                    st.markdown(f"**{st.session_state.sw_tB or 'Team B'}**")
                    for i in range(ALL_PLAYERS):
                        st.session_state.sw_allB[i]=st.text_input(
                            f"Player {i+1}",value=st.session_state.sw_allB[i],
                            placeholder=f"Player {i+1}",key=f"s1_pB{i}"
                        )

            if st.button("Next → Select Starters & Service Order",use_container_width=True,key="step1_next"):
                st.session_state.sw_step=2; st.rerun()

        # ── STEP 2: Starters, Order, First Serve ──
        elif step==2:
            allA_f=[_safe(v,f"A{i+1}") for i,v in enumerate(st.session_state.sw_allA)]
            allB_f=[_safe(v,f"B{i+1}") for i,v in enumerate(st.session_state.sw_allB)]

            with st.container(border=True):
                st.markdown("**Step 2 of 2 — Starters & Service Order**")
                st.caption(f"{st.session_state.sw_tA or 'Team A'} vs {st.session_state.sw_tB or 'Team B'}")

                st.markdown("**Select 5 starting players:**")
                s1,s2=st.columns(2)
                with s1:
                    mpA=st.multiselect(f"{st.session_state.sw_tA or 'Team A'}",allA_f,default=allA_f[:PLAYERS],max_selections=PLAYERS,key="s2_mpA")
                with s2:
                    mpB=st.multiselect(f"{st.session_state.sw_tB or 'Team B'}",allB_f,default=allB_f[:PLAYERS],max_selections=PLAYERS,key="s2_mpB")

                oAi,oBi=[],[]
                if len(mpA)==PLAYERS and len(mpB)==PLAYERS:
                    st.markdown("**Service Order:**")
                    o1,o2=st.columns(2)
                    with o1:
                        st.markdown(f"**{st.session_state.sw_tA or 'Team A'}**")
                        for k in range(PLAYERS):
                            opts=[f"{i+1}. {mpA[i]}" for i in range(PLAYERS)]
                            sel=st.selectbox(f"Serve {k+1}",opts,key=f"s2_oA{k}")
                            oAi.append(int(sel.split(".")[0]))
                    with o2:
                        st.markdown(f"**{st.session_state.sw_tB or 'Team B'}**")
                        for k in range(PLAYERS):
                            opts=[f"{i+1}. {mpB[i]}" for i in range(PLAYERS)]
                            sel=st.selectbox(f"Serve {k+1}",opts,key=f"s2_oB{k}")
                            oBi.append(int(sel.split(".")[0]))

                    tA_lbl=st.session_state.sw_tA or "Team A"
                    tB_lbl=st.session_state.sw_tB or "Team B"
                    fs_label=st.radio("First Serve",[tA_lbl,tB_lbl],horizontal=True,key="s2_fs")
                    first_side="A" if fs_label==tA_lbl else "B"
                else:
                    st.warning("Select exactly 5 players per team above")
                    first_side="A"; oAi=[]; oBi=[]

            c_back,c_start=st.columns(2)
            with c_back:
                st.markdown("<div class='grey'>", unsafe_allow_html=True)
                if st.button("← Back",use_container_width=True,key="step2_back"):
                    st.session_state.sw_step=1; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with c_start:
                can_start = len(mpA)==PLAYERS and len(mpB)==PLAYERS and len(set(oAi))==PLAYERS and len(set(oBi))==PLAYERS
                if st.button("▶️ START MATCH",use_container_width=True,key="start_match_btn",disabled=not can_start):
                    oA2=_build_ord(list(mpA),oAi)
                    oB2=_build_ord(list(mpB),oBi)
                    errs=[]
                    if not oA2: errs.append("Invalid Team A service order")
                    if not oB2: errs.append("Invalid Team B service order")
                    if errs:
                        for e in errs: st.error(e)
                    else:
                        mid=_new_mid(st.session_state.username)
                        m=new_match(
                            mid,st.session_state.username,
                            _safe(st.session_state.sw_tA,"Team A"),
                            _safe(st.session_state.sw_tB,"Team B"),
                            allA_f,allB_f,list(mpA),list(mpB),oA2,oB2,first_side,
                            st.session_state.sw_tnm or None,
                            st.session_state.sw_trd or None
                        )
                        save_match(m,data)
                        st.session_state.sel_mid=mid
                        st.session_state.sw_step=1
                        st.rerun()
                if not can_start and len(mpA)==PLAYERS and len(mpB)==PLAYERS:
                    st.caption("⚠️ Service order must have unique players")

    # ── ACTIVE MATCH ──
    else:
        m=selected

        # Court change alert
        if m.pending_cc is not None:
            first_team=m.tA if m.pending_cc_team=="A" else m.tB
            st.markdown(
                f"<div class='court-alert'>🔄 COURT CHANGE — <b>{first_team}</b> reached <b>{m.pending_cc}</b> first!</div>",
                unsafe_allow_html=True
            )

        if m.over:
            st.markdown(f"<div class='win-banner'>🏆 {m.tA if m.winner=='A' else m.tB} WINS THE MATCH!</div>", unsafe_allow_html=True)
            st.markdown("<div class='new-match-hint'>Match complete — click 🆕 New Match in the top bar to start a new match</div>", unsafe_allow_html=True)

        if m.tnm:
            st.markdown(f"<div style='color:#5a7090;font-size:11px;margin-bottom:5px'>🏆 {m.tnm}{(' · '+m.trd) if m.trd else ''}</div>", unsafe_allow_html=True)

        lt="B" if m.swapped else "A"
        rt="A" if m.swapped else "B"
        tn=lambda t:m.tA if t=="A" else m.tB
        sc=lambda t:m.scA if t=="A" else m.scB
        ss=lambda t:m.sA if t=="A" else m.sB

        st.markdown(f"""
        <div class='scoreboard'>
          <div style='display:flex;justify-content:space-between;align-items:flex-end;gap:10px'>
            <div style='flex:1;min-width:0'>
              <div class='tname'>{'🟠 ' if m.srv==lt else ''}{tn(lt)}</div>
              <div class='score-num {"hot" if m.srv==lt else ""}'>{sc(lt)}</div>
              <div class='tmeta'>Sets: {ss(lt)} · Left</div>
            </div>
            <div style='opacity:.32;font-size:18px;font-weight:700'>vs</div>
            <div style='flex:1;min-width:0;text-align:right'>
              <div class='tname'>{'🟠 ' if m.srv==rt else ''}{tn(rt)}</div>
              <div class='score-num {"hot" if m.srv==rt else ""}'>{sc(rt)}</div>
              <div class='tmeta'>Sets: {ss(rt)} · Right</div>
            </div>
          </div>
          <div style='text-align:center;color:#5a7090;font-size:10px;margin-top:8px'>
            SET {m.setno}/3 · TARGET {m.target} · CAP {MAX_SCORE_CAP}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Set history
        if m.psA:
            scols=st.columns(len(m.psA))
            for i,(a,b) in enumerate(zip(m.psA,m.psB)):
                with scols[i]:
                    st.markdown(f"<div class='set-card'><div style='font-size:9px;color:#5a7090'>SET {i+1}</div><div style='font-size:17px;font-weight:800'>{a}–{b}</div><div style='font-size:9px;color:#f97316'>{m.tA if a>b else m.tB}</div></div>", unsafe_allow_html=True)

        # Info metrics
        c1,c2,c3,c4=st.columns(4)
        with c1: st.metric("Serving",m.tA if m.srv=="A" else m.tB)
        with c2: st.metric("Server",cur_srv(m))
        with c3: st.metric("Target",m.target)
        with c4: st.metric("Updated",m.updated_at or "—")

        # Point buttons
        pb1,pb2=st.columns(2)
        with pb1:
            st.markdown("<div class='big'>", unsafe_allow_html=True)
            if st.button(f"＋  {m.tA}",key="ptA",use_container_width=True,disabled=(m.over or m.scA>=MAX_SCORE_CAP)):
                action_point(m.id,"A"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with pb2:
            st.markdown("<div class='big blue'>", unsafe_allow_html=True)
            if st.button(f"＋  {m.tB}",key="ptB",use_container_width=True,disabled=(m.over or m.scB>=MAX_SCORE_CAP)):
                action_point(m.id,"B"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # Control buttons
        st.markdown("<div class='small'>", unsafe_allow_html=True)
        r1=st.columns(4)
        with r1[0]:
            if st.button("↩️ Undo",key="undo_btn",use_container_width=True,disabled=not m.history):
                action_undo(m.id); st.rerun()
        with r1[1]:
            if st.button("⚙️ Score Adj",key="adj_toggle",use_container_width=True):
                st.session_state.show_adj=not st.session_state.show_adj; st.rerun()
        with r1[2]:
            if st.button("🔁 Subs/T/O",key="subs_toggle",use_container_width=True):
                st.session_state.show_subs=not st.session_state.show_subs; st.rerun()
        with r1[3]:
            if st.button("🗑️ Delete",key="del_match",use_container_width=True):
                delete_match(m.id,data)
                st.session_state.sel_mid=None; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Score adjust panel
        if st.session_state.show_adj:
            with st.container(border=True):
                st.markdown("### ✏️ Manual Score Adjust")
                a1,a2=st.columns(2)
                with a1:
                    new_a=st.number_input(f"{m.tA} Score",min_value=0,max_value=MAX_SCORE_CAP,value=int(m.scA),step=1,key="adj_a")
                    if st.button(f"Set {m.tA}",key="set_adj_a",use_container_width=True):
                        action_adjust(m.id,"A",new_a); st.rerun()
                with a2:
                    new_b=st.number_input(f"{m.tB} Score",min_value=0,max_value=MAX_SCORE_CAP,value=int(m.scB),step=1,key="adj_b")
                    if st.button(f"Set {m.tB}",key="set_adj_b",use_container_width=True):
                        action_adjust(m.id,"B",new_b); st.rerun()

        # Subs & timeout panel
        if st.session_state.show_subs:
            with st.container(border=True):
                st.markdown("### 🔁 Substitutions & Timeouts")
                sc1,sc2=st.columns(2)
                for team,col in [("A",sc1),("B",sc2)]:
                    fresh=_restore(data_load()["matches"].get(m.id)) or m
                    tname=fresh.tA if team=="A" else fresh.tB
                    subs=fresh.subA if team=="A" else fresh.subB
                    tos=fresh.toA if team=="A" else fresh.toB
                    p_on=fresh.onA if team=="A" else fresh.onB
                    all_p=fresh.allA if team=="A" else fresh.allB
                    with col:
                        sb_c="b-g" if subs>0 else "b-r"
                        to_c="b-b" if tos>0  else "b-r"
                        st.markdown(f"**{tname}** <span style='font-size:11px;background:rgba(255,255,255,.08);padding:2px 7px;border-radius:8px'>Subs:{subs} T/O:{tos}</span>", unsafe_allow_html=True)
                        bench=[p for p in all_p if p and p not in p_on]
                        if subs>0 and bench:
                            on_p=st.selectbox("In ▲",bench,key=f"in_{team}")
                            off_p=st.selectbox("Out ▼",p_on,key=f"out_{team}")
                            if st.button(f"Substitute {tname}",key=f"sub_{team}",use_container_width=True):
                                action_sub(m.id,team,on_p,off_p); st.rerun()
                        else:
                            st.caption("No subs available" if subs==0 else "No bench players")
                        if tos>0:
                            if st.button(f"⏱️ Timeout",key=f"to_{team}_{m.setno}",use_container_width=True):
                                action_timeout(m.id,team); st.rerun()
                        else:
                            st.caption("No timeouts left")

        # Service order + events
        with st.container(border=True):
            col_a,col_b=st.columns(2)
            with col_a:
                st.markdown(f"**{m.tA} Service Order**")
                for i,p in enumerate(m.ordA):
                    active=m.srv=="A" and m.curA==p
                    st.markdown(f"<div style='font-size:12px;padding:2px 0;{'color:#f97316;font-weight:700' if active else 'color:#5a7090'}'>{'🟠' if active else str(i+1)+'.'} {p}</div>", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"**{m.tB} Service Order**")
                for i,p in enumerate(m.ordB):
                    active=m.srv=="B" and m.curB==p
                    st.markdown(f"<div style='font-size:12px;padding:2px 0;{'color:#f97316;font-weight:700' if active else 'color:#5a7090'}'>{'🟠' if active else str(i+1)+'.'} {p}</div>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("**Live Events**")
            for e in m.events[:16]:
                st.markdown(f"<div class='ev'>{e}</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════
#  STATS TAB
# ═══════════════════════════════════════════
elif tab=="stats":
    if not selected:
        st.info("Select a match from the dropdown above.")
    else:
        m=selected
        total=m.scA+m.scB+sum(m.psA)+sum(m.psB)
        c1,c2,c3,c4=st.columns(4)
        for col,val,lbl in [(c1,f"Set {m.setno}","Set"),(c2,f"{m.sA}–{m.sB}","Sets"),(c3,f"{m.scA}–{m.scB}","Score"),(c4,total,"Total Pts")]:
            with col: st.markdown(f"<div class='box'><div class='n'>{val}</div><div class='l'>{lbl}</div></div>", unsafe_allow_html=True)

        if m.psA:
            st.markdown("### Set Breakdown")
            hcols=st.columns(len(m.psA)+1)
            with hcols[0]: st.markdown("**Team**"); st.write(m.tA); st.write(m.tB)
            for i,(a,b) in enumerate(zip(m.psA,m.psB)):
                with hcols[i+1]:
                    st.markdown(f"**Set {i+1}**")
                    st.write(f"{'🏆 ' if a>b else ''}{a}")
                    st.write(f"{'🏆 ' if b>a else ''}{b}")

        p1,p2=st.columns(2)
        with p1:
            st.markdown(f"**{m.tA} Player Points**")
            for p,pts in sorted(m.ppA.items(),key=lambda x:-x[1]):
                st.write(f"{p}: **{pts}**")
                st.progress(min(pts,SET_POINTS)/SET_POINTS)
        with p2:
            st.markdown(f"**{m.tB} Player Points**")
            for p,pts in sorted(m.ppB.items(),key=lambda x:-x[1]):
                st.write(f"{p}: **{pts}**")
                st.progress(min(pts,SET_POINTS)/SET_POINTS)

        c1,c2,c3,c4=st.columns(4)
        with c1: st.metric(f"{m.tA} Subs Used",3-m.subA)
        with c2: st.metric(f"{m.tB} Subs Used",3-m.subB)
        with c3: st.metric(f"{m.tA} T/O Used",1-m.toA)
        with c4: st.metric(f"{m.tB} T/O Used",1-m.toB)

        with st.expander("Full Event Log"):
            for e in m.events: st.write(e)


# ═══════════════════════════════════════════
#  HISTORY TAB
# ═══════════════════════════════════════════
elif tab=="history":
    st.markdown("<div style='font-family:Bebas Neue,sans-serif;font-size:24px;letter-spacing:2px;margin-bottom:10px'>MATCH HISTORY</div>", unsafe_allow_html=True)
    hist=data.get("history",[])
    if not hist:
        st.info("No completed matches yet.")
    else:
        st.write(f"**{len(hist)} completed match(es)**")
        for h in reversed(hist):
            with st.container(border=True):
                c1,c2=st.columns([3,1])
                with c1:
                    st.markdown(f"### {h['tA']} vs {h['tB']}")
                    if h.get("tnm"): st.caption(f"🏆 {h['tnm']} {h.get('trd','')}")
                    st.caption(f"📅 {h['date']} · by {h.get('created_by','—')}")
                    sets_s=" · ".join([f"Set {i+1}: {a}–{b}" for i,(a,b) in enumerate(h.get("set_scores",[]))])
                    st.write(f"Sets: **{h['sA']}–{h['sB']}** · {sets_s}")
                with c2:
                    st.markdown(f"<div class='win-banner' style='font-size:13px;padding:8px'>🏆<br>{h['winner']}</div>", unsafe_allow_html=True)
        if st.button("🗑️ Clear All History",use_container_width=True):
            data["history"]=[]; data_save(data); st.rerun()


# ═══════════════════════════════════════════
#  USERS TAB
# ═══════════════════════════════════════════
elif tab=="users":
    st.markdown("<div style='font-family:Bebas Neue,sans-serif;font-size:24px;letter-spacing:2px;margin-bottom:10px'>USERS</div>", unsafe_allow_html=True)
    users=users_load()
    if users:
        st.write(f"**{len(users)} registered user(s)**")
        for uname,u in users.items():
            with st.container(border=True):
                c1,c2,c3=st.columns([2,2,1])
                with c1:
                    st.markdown(f"**{u.get('name','—')}**")
                    st.caption(f"@{uname}")
                with c2:
                    st.write(u.get("contact","—"))
                    st.caption(f"Joined: {u.get('created','—')}")
                with c3:
                    role_lbl="Admin" if u.get("is_admin") else "Viewer"
                    st.write(role_lbl)
                    if st.button("🗑️",key=f"del_{uname}",use_container_width=True):
                        del users[uname]; users_save(users); st.rerun()
    else:
        st.info("No users registered yet.")

    st.markdown("---")
    st.markdown("### ➕ Add User Manually")
    with st.container(border=True):
        n=st.text_input("Name",placeholder="Full name",key="add_n")
        c=st.text_input("Contact",placeholder="Mobile/Email",key="add_c")
        u=st.text_input("Username",placeholder="username",key="add_u")
        p=st.text_input("Password",placeholder="Min 6 chars",type="password",key="add_p")
        ia=st.checkbox("Give Admin Access",key="add_ia")
        if st.button("✅ Create User",use_container_width=True,key="add_btn"):
            ok,msg=user_register(n,c,u,p,created_by_admin=True,is_admin=ia)
            if ok: st.success(f"✅ {msg}")
            else:  st.error(f"❌ {msg}")


# ═══════════════════════════════════════════
#  ADMIN TAB
# ═══════════════════════════════════════════
elif tab=="admin":
    st.markdown("<div style='font-family:Bebas Neue,sans-serif;font-size:24px;letter-spacing:2px;margin-bottom:10px'>ADMIN OVERVIEW</div>", unsafe_allow_html=True)
    all_live=list_matches(data)
    c1,c2,c3=st.columns(3)
    with c1: st.metric("Live Matches",len(all_live))
    with c2: st.metric("Completed",len(data.get("history",[])))
    with c3: st.metric("Registered Users",len(users_load()))

    if all_live:
        st.markdown("### Live Matches")
        for m in all_live:
            with st.container(border=True):
                c1,c2=st.columns([3,1])
                with c1:
                    st.write(f"**{m.tA} vs {m.tB}**")
                    st.caption(f"Created by: {m.created_by} · {m.started}")
                    st.write(f"Score: {m.scA}–{m.scB} · Sets {m.sA}–{m.sB} · Set {m.setno}/3")
                    st.write(f"Updated: {m.updated_at}")
                with c2:
                    if m.over:
                        st.markdown(f"<div style='color:#f59e0b;font-weight:700'>✅ {m.tA if m.winner=='A' else m.tB} won</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='color:#22c55e;font-weight:700'>🟢 Live</div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("### 💾 Export All Data")
        export={"matches":data.get("matches",{}),"history":data.get("history",[]),
                "exported":now_str()}
        st.download_button("⬇️ Download JSON",data=json.dumps(export,indent=2),
            file_name=f"bb_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",use_container_width=True)

    with st.container(border=True):
        st.markdown("### ℹ️ Rules")
        st.markdown("""
        - **Court change:** Alert shows only when the **first team** reaches 9/18/27, once per milestone per set, and auto-clears after the next point.
        - **Target:** 35 pts, lead by 2. At 34–34 → target 36. At 36–36 → cap 39.
        - **Subs:** 3 per set per team · **Timeouts:** 1 per set per team
        - **New Match:** Click 🆕 New Match anytime in top bar
        - **Data:** Saved to Supabase (if configured) or local JSON
        """)
