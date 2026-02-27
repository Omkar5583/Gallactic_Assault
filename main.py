"""
GALACTIC ASSAULT v2.0 — Space Shooter
Controls: WASD/Arrows=Move  SPACE=Shoot  P/ESC=Pause  X=Quit
"""

import pygame, random, math, sys, json

# ── Constants ───────────────────────────────────────────────
W, H   = 420, 720
FPS    = 60
SAVE   = "save_data.json"

BLK  = (0,0,10);    WHT  = (255,255,255); DGRAY= (30,30,50)
DBLU = (5,10,40);   GRAY = (80,80,100)
NBLU = (0,200,255); NGRN = (0,255,140);  NPNK = (255,50,180)
NYEL = (255,240,0); NORA = (255,140,0);  NRED = (255,60,60)
PURP = (120,0,220); GOLD = (255,215,0);  CYAN = (0,255,255)

S_MENU="menu"; S_PLAY="play"; S_PAUSE="pause"
S_LVL="lvlup"; S_OVER="over"; S_AD="ad"; S_SHOP="shop"; S_HI="hi"

LEVELS = {
    1:{"name":"Rookie Space",   "asp":1.0,"sr":80,"ufo":False,"bw":5},
    2:{"name":"Asteroid Belt",  "asp":1.2,"sr":70,"ufo":False,"bw":5},
    3:{"name":"Danger Zone",    "asp":1.4,"sr":62,"ufo":True, "bw":5},
    4:{"name":"Deep Space",     "asp":1.6,"sr":55,"ufo":True, "bw":5},
    5:{"name":"Nebula Storm",   "asp":1.8,"sr":50,"ufo":True, "bw":4},
    6:{"name":"Void Sector",    "asp":2.0,"sr":45,"ufo":True, "bw":4},
    7:{"name":"Black Hole Ring","asp":2.2,"sr":40,"ufo":True, "bw":3},
    8:{"name":"Warp Core",      "asp":2.5,"sr":36,"ufo":True, "bw":3},
    9:{"name":"Galactic Core",  "asp":2.8,"sr":32,"ufo":True, "bw":3},
   10:{"name":"FINAL FRONTIER", "asp":3.2,"sr":26,"ufo":True, "bw":2},
}
SPL = 1500  # score per level

PUPS = {
    "shield":{"col":NGRN, "ic":"S","txt":"SHIELD — Blocks 1 hit",      "dur":8},
    "rapid": {"col":NYEL, "ic":"R","txt":"RAPID — 3x fire rate",        "dur":7},
    "triple":{"col":NBLU, "ic":"3","txt":"TRIPLE — 3 bullets",          "dur":8},
    "laser": {"col":CYAN, "ic":"L","txt":"LASER — Piercing shots",      "dur":5},
    "bomb":  {"col":NORA, "ic":"B","txt":"BOMB — Clears screen",        "dur":0},
    "magnet":{"col":NPNK, "ic":"M","txt":"MAGNET — Auto-collect coins", "dur":6},
    "speed": {"col":(0,255,200),"ic":"V","txt":"SPEED — 2x movement",   "dur":6},
    "coin":  {"col":GOLD, "ic":"C","txt":"+10 Coins",                   "dur":0},
}

SKINS=[
    {"name":"Falcon", "col":NBLU,"eng":NORA,"price":0},
    {"name":"Phoenix","col":NPNK,"eng":NYEL,"price":200},
    {"name":"Viper",  "col":NGRN,"eng":NBLU,"price":350},
    {"name":"Thunder","col":GOLD,"eng":NRED,"price":500},
    {"name":"Ghost",  "col":CYAN,"eng":WHT, "price":750},
]

# ── Save/Load ────────────────────────────────────────────────
def load_save():
    try:
        with open(SAVE) as f: return json.load(f)
    except: return {"hs":0,"coins":0,"games":0,"skin":0,"maxlv":1}

def save_game(d):
    try:
        with open(SAVE,"w") as f: json.dump(d,f)
    except: pass

# ── Font helper (uses default font — FAST, no system scan) ──
_FC={}
def F(size, bold=False):
    k=(size,bold)
    if k not in _FC:
        _FC[k]=pygame.font.SysFont(None,size,bold=bold)
    return _FC[k]

def T(surf,text,sz,x,y,col=WHT,mid=True,bold=False):
    r=F(sz,bold).render(str(text),True,col)
    surf.blit(r, r.get_rect(center=(x,y)) if mid else (x,y))

def RR(surf,col,rect,rad=10,a=255):
    s=pygame.Surface((rect[2],rect[3]),pygame.SRCALPHA)
    pygame.draw.rect(s,(*col,a),(0,0,rect[2],rect[3]),border_radius=rad)
    surf.blit(s,(rect[0],rect[1]))

def BTN(surf,lbl,x,y,w,h,col,tc=WHT,mp=None):
    hov=pygame.Rect(x,y,w,h).collidepoint(mp) if mp else False
    c=tuple(min(255,v+40) for v in col) if hov else col
    RR(surf,c,(x,y,w,h),rad=10,a=220)
    pygame.draw.rect(surf,WHT,(x,y,w,h),1,border_radius=10)
    T(surf,lbl,18,x+w//2,y+h//2,tc,bold=True)
    return pygame.Rect(x,y,w,h)

# ── Particle ─────────────────────────────────────────────────
class P:
    __slots__=["x","y","vx","vy","col","life","ml","sz"]
    def __init__(self,x,y,col,vx=None,vy=None,life=40,sz=4):
        self.x,self.y=float(x),float(y); self.col=col
        self.vx=vx if vx is not None else random.uniform(-3,3)
        self.vy=vy if vy is not None else random.uniform(-4,1)
        self.life=self.ml=life; self.sz=sz
    def upd(self):
        self.x+=self.vx; self.y+=self.vy
    def draw(self,surf):
        a=int(255*(self.life/self.ml)); r=max(1,int(self.sz*(self.life/self.ml)))
        s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(*self.col,a),(r,r),r); surf.blit(s,(int(self.x)-r,int(self.y)-r))

def boom(pl,x,y,col,n=18,sz=5):
    pl+=[P(x,y,col,sz=sz) for _ in range(n)]

# ── Stars ────────────────────────────────────────────────────
class Stars:
    def __init__(self):
        self.s=[[random.randint(0,W),random.randint(0,H),
                 random.uniform(.3,2.5),random.randint(1,3),random.randint(100,255)] for _ in range(130)]
    def upd(self):
        for s in self.s:
            s[1]+=s[2]
            if s[1]>H: s[0]=random.randint(0,W);s[1]=0;s[2]=random.uniform(.3,2.5)
    def draw(self,surf):
        for s in self.s:
            b=s[4]; pygame.draw.circle(surf,(b,b,min(255,b+60)),(int(s[0]),int(s[1])),s[3])

# ── Bullet ───────────────────────────────────────────────────
class Bullet:
    def __init__(self,x,y,ang=0,col=NBLU,spd=12,pierce=False):
        self.x,self.y=float(x),float(y); self.ang=ang; self.col=col
        self.spd=spd; self.pierce=pierce; self.alive=True
    def upd(self):
        r=math.radians(self.ang)
        self.x+=math.sin(r)*self.spd; self.y-=math.cos(r)*self.spd
        if not(-20<self.y<H+20 and -20<self.x<W+20): self.alive=False
    def draw(self,surf):
        x,y=int(self.x),int(self.y)
        pygame.draw.rect(surf,self.col,(x-2,y-8,4,16),border_radius=2)
        pygame.draw.rect(surf,WHT,(x-1,y-8,2,8))
    def R(self): return pygame.Rect(self.x-2,self.y-8,4,16)

class EB:  # enemy bullet
    def __init__(self,x,y,tx,ty,spd=4.5):
        self.x,self.y=float(x),float(y); d=max(1,math.hypot(tx-x,ty-y))
        self.vx=(tx-x)/d*spd; self.vy=(ty-y)/d*spd; self.alive=True
    def upd(self):
        self.x+=self.vx; self.y+=self.vy
        if not(0<self.x<W and 0<self.y<H): self.alive=False
    def draw(self,surf):
        pygame.draw.circle(surf,NPNK,(int(self.x),int(self.y)),5)
        pygame.draw.circle(surf,WHT,(int(self.x),int(self.y)),2)
    def R(self): return pygame.Rect(self.x-5,self.y-5,10,10)

# ── PowerUp ──────────────────────────────────────────────────
class PUp:
    def __init__(self,x,y,kind=None):
        self.x,self.y=float(x),float(y)
        self.kind=kind or random.choice(list(PUPS))
        self.col=PUPS[self.kind]["col"]; self.ic=PUPS[self.kind]["ic"]
        self.alive=True; self.r=17; self.p=random.uniform(0,6.28)
    def upd(self):
        self.y+=2.2; self.p+=0.12
        if self.y>H+30: self.alive=False
    def draw(self,surf):
        pr=int(self.r+5*abs(math.sin(self.p)))
        gs=pygame.Surface((pr*2+4,pr*2+4),pygame.SRCALPHA)
        pygame.draw.circle(gs,(*self.col,55),(pr+2,pr+2),pr+2); surf.blit(gs,(int(self.x)-pr-2,int(self.y)-pr-2))
        pygame.draw.circle(surf,self.col,(int(self.x),int(self.y)),self.r)
        pygame.draw.circle(surf,WHT,(int(self.x),int(self.y)),self.r,2)
        lbl=F(15,True).render(self.ic,True,WHT)
        surf.blit(lbl,(int(self.x)-lbl.get_width()//2,int(self.y)-lbl.get_height()//2))
    def R(self): return pygame.Rect(self.x-self.r,self.y-self.r,self.r*2,self.r*2)

# ── Asteroid ─────────────────────────────────────────────────
class Asteroid:
    CFG={"large":{"r":(28,38),"hp":3,"sc":50,"col":(140,100,70)},
         "medium":{"r":(15,23),"hp":2,"sc":30,"col":(120,90,60)},
         "small": {"r":(7,13), "hp":1,"sc":15,"col":(100,80,60)}}
    def __init__(self,x=None,y=None,size="large",spd=1.0):
        self.size=size; c=self.CFG[size]
        self.rad=random.randint(*c["r"]); self.hp=self.mhp=c["hp"]
        self.sv=c["sc"]; self.bc=c["col"]
        self.x=float(x or random.randint(self.rad,W-self.rad))
        self.y=float(y or random.randint(-80,-self.rad))
        self.sp=random.uniform(1.2,2.6)*spd; self.vx=random.uniform(-1,1)
        self.rot=0; self.rs=random.uniform(-3,3); self.alive=True
        n=random.randint(7,11)
        self.pts=[(math.cos(2*math.pi/n*i)*self.rad*random.uniform(.75,1),
                   math.sin(2*math.pi/n*i)*self.rad*random.uniform(.75,1)) for i in range(n)]
    def rpts(self):
        rad=math.radians(self.rot); c,s=math.cos(rad),math.sin(rad)
        return [(int(self.x+px*c-py*s),int(self.y+px*s+py*c)) for px,py in self.pts]
    def upd(self):
        self.y+=self.sp; self.x+=self.vx; self.rot+=self.rs
        if self.x<self.rad: self.vx=abs(self.vx)
        elif self.x>W-self.rad: self.vx=-abs(self.vx)
        if self.y>H+self.rad+20: self.alive=False
    def draw(self,surf):
        pts=self.rpts()
        if len(pts)<3: return
        ratio=self.hp/self.mhp
        col=(int(self.bc[0]*ratio+60*(1-ratio)),int(self.bc[1]*ratio),int(self.bc[2]*ratio))
        pygame.draw.polygon(surf,(30,20,10),[(p[0]+3,p[1]+3) for p in pts])
        pygame.draw.polygon(surf,col,pts)
        pygame.draw.polygon(surf,(200,170,130),pts,2)
    def hit(self,d=1):
        self.hp-=d
        if self.hp<=0: self.alive=False; return True
        return False
    def R(self): return pygame.Rect(self.x-self.rad,self.y-self.rad,self.rad*2,self.rad*2)

# ── UFO ──────────────────────────────────────────────────────
class UFO:
    def __init__(self,lv=1):
        self.x=float(random.choice([30,W-30])); self.y=float(random.randint(80,260))
        self.hp=self.mhp=4+lv; self.sv=120+lv*20
        self.sp=1.2+lv*.1; self.dr=1 if self.x<W//2 else -1
        self.st=0; self.sr=max(60,120-lv*8); self.alive=True
        self.bob=random.uniform(0,6.28); self.yd=self.y; self.rad=22
    def upd(self):
        self.x+=self.sp*self.dr; self.bob+=.06; self.yd=self.y+math.sin(self.bob)*8
        if self.x>W-30: self.dr=-1
        if self.x<30:   self.dr=1
        self.st+=1
    def shoot(self):
        if self.st>=self.sr: self.st=0; return True
        return False
    def draw(self,surf):
        x,y=int(self.x),int(self.yd)
        pygame.draw.ellipse(surf,(60,200,60),(x-22,y-10,44,20))
        pygame.draw.ellipse(surf,NGRN,(x-22,y-10,44,20),2)
        pygame.draw.ellipse(surf,(100,255,150),(x-12,y-20,24,16))
        pygame.draw.ellipse(surf,WHT,(x-12,y-20,24,16),1)
        bw=44; bx=x-22; by=int(self.yd)+16
        pygame.draw.rect(surf,GRAY,(bx,by,bw,6),border_radius=3)
        fw=int(bw*(self.hp/self.mhp))
        if fw>0: pygame.draw.rect(surf,NGRN if self.hp/self.mhp>.5 else NYEL,(bx,by,fw,6),border_radius=3)
    def hit(self,d=1):
        self.hp-=d
        if self.hp<=0: self.alive=False; return True
        return False
    def R(self): return pygame.Rect(self.x-22,self.yd-10,44,20)

# ── Boss ─────────────────────────────────────────────────────
class Boss:
    def __init__(self,wave,lv):
        self.x=float(W//2); self.y=90.0
        self.hp=self.mhp=25+wave*8+lv*5
        self.r=58; self.sp=1.6+lv*.1; self.dr=1; self.alive=True
        self.sv=600+wave*100+lv*50; self.st=0
        self.srate=max(25,75-wave*4-lv*2); self.ang=0; self.phase=1
    def upd(self):
        self.x+=self.sp*self.dr; self.ang+=1.5
        if self.x>W-self.r-10: self.dr=-1
        if self.x<self.r+10:   self.dr=1
        if self.hp<=self.mhp//2 and self.phase==1:
            self.phase=2; self.sp*=1.4; self.srate=max(18,self.srate-15)
        self.st+=1
    def shoot(self):
        if self.st>=self.srate: self.st=0; return True
        return False
    def draw(self,surf):
        x,y=int(self.x),int(self.y)
        col=NPNK if self.phase==2 else PURP
        ratio=self.hp/self.mhp
        bc=(int(150+105*(1-ratio)),0,int(220*ratio))
        pygame.draw.circle(surf,bc,(x,y),self.r)
        norbs=4 if self.phase==2 else 3
        for i in range(norbs):
            rad=math.radians(self.ang+i*(360//norbs))
            ox=int(x+math.cos(rad)*(self.r-12)); oy=int(y+math.sin(rad)*(self.r-12))
            pygame.draw.circle(surf,NPNK,(ox,oy),8); pygame.draw.circle(surf,WHT,(ox,oy),3)
        pygame.draw.circle(surf,col,(x,y),self.r,3)
        if self.phase==2: T(surf,"PHASE 2!",13,x,y-self.r-16,NPNK,bold=True)
        bw=130; bh=10; bx=x-bw//2; by=y+self.r+8
        pygame.draw.rect(surf,GRAY,(bx,by,bw,bh),border_radius=5)
        fw=int(bw*ratio)
        if fw>0:
            bc2=NGRN if ratio>.5 else NYEL if ratio>.25 else NRED
            pygame.draw.rect(surf,bc2,(bx,by,fw,bh),border_radius=5)
        pygame.draw.rect(surf,WHT,(bx,by,bw,bh),1,border_radius=5)
        T(surf,"BOSS",12,x,by+bh+5,NPNK,bold=True)
    def hit(self,d=1):
        self.hp-=d
        if self.hp<=0: self.alive=False; return True
        return False
    def R(self): return pygame.Rect(self.x-self.r,self.y-self.r,self.r*2,self.r*2)

# ── Player ───────────────────────────────────────────────────
class Player:
    def __init__(self,skin=0):
        self.x,self.y=float(W//2),float(H-110); self.sk=SKINS[skin]
        self.lives=3; self.maxlv=5; self.score=0; self.coins=0
        self.scd=0; self.srate=18; self.buls=[]; self.parts=[]
        self.inv=0; self.pw={k:0 for k in PUPS}
        self.alive=True; self.combo=0; self.ct=0; self.ta=0
    def has(self,k): return self.pw[k]>0
    def upd(self,keys,pups):
        spd=5*(2.0 if self.has("speed") else 1.0)
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.x-=spd
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.x+=spd
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.y-=spd
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.y+=spd
        self.x=max(18,min(W-18,self.x)); self.y=max(24,min(H-24,self.y))
        if self.scd>0: self.scd-=1
        if keys[pygame.K_SPACE] and self.scd==0: self.fire()
        self.srate=7 if self.has("rapid") else 18
        for k in self.pw:
            if self.pw[k]>0: self.pw[k]-=1
        if self.ct>0: self.ct-=1
        else: self.combo=0
        if self.has("magnet"):
            for pu in pups:
                dx=self.x-pu.x; dy=self.y-pu.y; d=max(1,math.hypot(dx,dy))
                if d<200: pu.x+=dx/d*5; pu.y+=dy/d*5
        if self.inv>0: self.inv-=1
        self.ta+=0.3
        if random.random()<.65:
            self.parts.append(P(self.x+random.uniform(-6,6),self.y+22,self.sk["eng"],
                vx=random.uniform(-.5,.5),vy=random.uniform(1,4),
                life=random.randint(10,20),sz=random.randint(2,5)))
        for b in self.buls[:]:
            b.upd()
            if not b.alive: self.buls.remove(b)
        for p in self.parts[:]:
            p.upd()
            if p.life<=0: self.parts.remove(p)
    def fire(self):
        self.scd=self.srate; c=CYAN if self.has("laser") else self.sk["col"]; pi=self.has("laser")
        if self.has("triple"):
            for a in [-18,0,18]: self.buls.append(Bullet(self.x,self.y-14,a,c,pierce=pi))
        else: self.buls.append(Bullet(self.x,self.y-14,0,c,pierce=pi))
    def add_score(self,v):
        self.combo+=1; self.ct=130; mult=1+min((self.combo//5)*.5,3.0)
        e=int(v*mult); self.score+=e; return e,self.combo
    def dmg(self):
        if self.inv>0: return False
        if self.has("shield"): self.pw["shield"]=0; return False
        self.lives-=1; self.inv=100; self.combo=0
        if self.lives<=0: self.alive=False
        return True
    def draw(self,surf):
        for p in self.parts: p.draw(surf)
        if self.inv>0 and (self.inv//6)%2==0: return
        x,y=int(self.x),int(self.y); c=self.sk["col"]; ec=self.sk["eng"]
        fh=int(20+9*abs(math.sin(self.ta)))
        pygame.draw.polygon(surf,ec,[(x-10,y+18),(x,y+18+fh),(x+10,y+18)])
        pygame.draw.polygon(surf,WHT,[(x-5,y+18),(x,y+18+fh//2),(x+5,y+18)])
        pts=[(x,y-24),(x+20,y+18),(x+11,y+11),(x,y+6),(x-11,y+11),(x-20,y+18)]
        pygame.draw.polygon(surf,c,pts); pygame.draw.polygon(surf,WHT,pts,1)
        pygame.draw.ellipse(surf,(180,230,255),(x-7,y-15,14,18))
        pygame.draw.line(surf,ec,(x+4,y-6),(x+18,y+15),2)
        pygame.draw.line(surf,ec,(x-4,y-6),(x-18,y+15),2)
        if self.has("shield"):
            p2=int(190+65*math.sin(pygame.time.get_ticks()*.01))
            ss=pygame.Surface((84,84),pygame.SRCALPHA)
            pygame.draw.circle(ss,(0,255,140,70),(42,42),40)
            pygame.draw.circle(ss,(0,255,140,p2),(42,42),40,3)
            surf.blit(ss,(x-42,y-42))
        if self.has("magnet"):
            ms=pygame.Surface((100,100),pygame.SRCALPHA)
            pygame.draw.circle(ms,(255,50,180,int(30+20*abs(math.sin(self.ta)))),(50,50),48,2)
            surf.blit(ms,(x-50,y-50))
    def R(self): return pygame.Rect(self.x-14,self.y-20,28,42)

# ── Floating text ────────────────────────────────────────────
class FT:
    def __init__(self,x,y,txt,col=WHT,sz=18,life=65):
        self.x,self.y=float(x),float(y); self.txt=txt; self.col=col; self.sz=sz; self.life=self.ml=life
    def upd(self): self.y-=1.1; self.life-=1
    def draw(self,surf):
        a=int(255*(self.life/self.ml)); r=F(self.sz,True).render(self.txt,True,self.col); r.set_alpha(a)
        surf.blit(r,(int(self.x)-r.get_width()//2,int(self.y)))

# ── HUD ──────────────────────────────────────────────────────
def draw_hud(surf,pl,wave,lv,lp):
    RR(surf,DBLU,(5,5,W-10,60),rad=10,a=185)
    T(surf,"SCORE",10,55,14,GRAY,bold=True); T(surf,f"{pl.score:,}",19,55,29,WHT,bold=True)
    T(surf,f"WAVE {wave}",13,W//2,14,GRAY,bold=True); T(surf,f"LVL {lv}",20,W//2,31,NYEL,bold=True)
    pygame.draw.circle(surf,GOLD,(W-92,22),9); T(surf,f"{pl.coins}",16,W-70,22,GOLD,mid=False,bold=True)
    for i in range(pl.maxlv):
        c=NGRN if i<pl.lives else (40,40,60); hx=8+i*22
        pygame.draw.polygon(surf,c,[(hx+10,47),(hx+18,43),(hx+20,50),(hx+10,58),(hx,50),(hx+2,43)])
    # Level bar
    bw=W-10
    RR(surf,DBLU,(5,67,bw,6),rad=3,a=200)
    fw=int(bw*lp)
    if fw>0: RR(surf,NBLU,(5,67,fw,6),rad=3,a=240)
    pygame.draw.rect(surf,GRAY,(5,67,bw,6),1,border_radius=3)
    T(surf,f"Level Progress: {int(lp*100)}%",9,W//2,70,WHT)
    # Active power-ups
    active=[(k,v) for k,v in pl.pw.items() if v>0]
    for i,(k,v) in enumerate(active[:4]):
        ix=6+i*83; RR(surf,DBLU,(ix,76,79,22),rad=5,a=200)
        T(surf,f"{PUPS[k]['ic']} {v//FPS+1}s",12,ix+40,87,PUPS[k]["col"],bold=True)
    if pl.combo>=3: T(surf,f"x{pl.combo} COMBO!",14,W-8,76,NPNK,mid=False,bold=True)

# ── Level Up Screen ──────────────────────────────────────────
def draw_levelup(surf,lv,choices):
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,20,215)); surf.blit(ov,(0,0))
    RR(surf,(5,30,10),(38,90,W-76,H-170),rad=18,a=245)
    pygame.draw.rect(surf,NGRN,(38,90,W-76,H-170),2,border_radius=18)
    T(surf,"LEVEL UP!",36,W//2,132,NGRN,bold=True)
    T(surf,f"Level {lv} — {LEVELS[min(lv,10)]['name']}",16,W//2,172,NYEL,bold=True)
    T(surf,"Choose your reward:",14,W//2,205,GRAY)
    for i,pw in enumerate(choices):
        y=228+i*96; col=PUPS[pw]["col"]
        RR(surf,(10,20,50),(50,y,W-100,84),rad=12,a=230)
        pygame.draw.rect(surf,col,(50,y,W-100,84),2,border_radius=12)
        pygame.draw.circle(surf,col,(86,y+42),22)
        T(surf,PUPS[pw]["ic"],20,86,y+42,WHT,bold=True)
        T(surf,PUPS[pw]["txt"],14,W//2+12,y+30,WHT,mid=False)
        T(surf,"TAP TO SELECT",11,W//2+12,y+54,col,mid=False,bold=True)
    T(surf,"ESC to skip",11,W//2,H-76,GRAY)

# ── Ad Screen ────────────────────────────────────────────────
class AdScr:
    def __init__(self): self.t=0; self.dur=5*FPS; self.ready=False
    def upd(self):
        self.t+=1
        self.ready=(self.t>=self.dur-FPS)
    def draw(self,surf):
        surf.fill((10,10,30))
        RR(surf,(20,20,60),(18,55,W-36,H-110),rad=14,a=245)
        T(surf,"ADVERTISEMENT",13,W//2,78,GRAY,bold=True)
        T(surf,"SUPER BLAST GAME",24,W//2,160,NYEL,bold=True)
        T(surf,"Download FREE — 10M+ players!",15,W//2,205,WHT)
        T(surf,"* * * * *",30,W//2,275,GOLD)
        T(surf,"#1 Space Shooter",14,W//2,325,WHT)
        rem=max(0,(self.dur-self.t)//FPS)
        if self.ready:
            BTN(surf,"Skip & Claim Extra Life",W//2-125,H-112,250,48,NGRN,(0,0,0))
            T(surf,"Your extra life is waiting!",14,W//2,H-50,NGRN)
        else:
            RR(surf,DBLU,(W-68,63,56,26),rad=6,a=220)
            T(surf,f"{rem}s",15,W-40,76,WHT,bold=True)
            T(surf,"Watching ad for extra life...",13,W//2,H-68,GRAY)
    def skip_R(self): return pygame.Rect(W//2-125,H-112,250,48)

# ── Shop ─────────────────────────────────────────────────────
class Shop:
    def __init__(self,sv): self.sv=sv
    def draw(self,surf,coins,mp):
        surf.fill(DBLU)
        T(surf,"SHIP SHOP",30,W//2,45,GOLD,bold=True)
        T(surf,f"Your Coins: {coins}",17,W//2,78,NYEL)
        for i,sk in enumerate(SKINS):
            y=105+i*116; sel=(self.sv.get("skin",0)==i)
            RR(surf,(10,30,60) if sel else (10,20,40),(18,y,W-36,104),rad=12,a=230)
            pygame.draw.rect(surf,NYEL if sel else GRAY,(18,y,W-36,104),2,border_radius=12)
            mx,my=70,y+52
            pts=[(mx,my-18),(mx+14,my+12),(mx,my+4),(mx-14,my+12)]
            pygame.draw.polygon(surf,sk["col"],pts); pygame.draw.polygon(surf,WHT,pts,1)
            T(surf,sk["name"],18,mx+76,y+22,sk["col"],mid=False,bold=True)
            T(surf,"FREE" if sk["price"]==0 else f"{sk['price']} coins",14,mx+76,y+46,GOLD,mid=False)
            if sel: T(surf,"SELECTED",13,W-100,y+22,NGRN,bold=True)
            elif coins>=sk["price"]: T(surf,"TAP TO BUY",12,W-120,y+22,WHT,mid=False)
            else: T(surf,f"Need {sk['price']-coins} more",11,W-136,y+22,NRED,mid=False)
        BTN(surf,"BACK",W//2-72,H-60,144,42,PURP,mp=mp)
    def click(self,pos,coins):
        for i,sk in enumerate(SKINS):
            if pygame.Rect(18,105+i*116,W-36,104).collidepoint(pos) and coins>=sk["price"]:
                self.sv["skin"]=i; save_game(self.sv); return "bought"
        if pygame.Rect(W//2-72,H-60,144,42).collidepoint(pos): return "back"

# ── Main Menu ────────────────────────────────────────────────
def draw_menu(surf,sv,stars,tick,mp):
    stars.draw(surf)
    T(surf,"GALACTIC",50,W//2,118,NBLU,bold=True)
    T(surf,"ASSAULT",50,W//2,165,NPNK,bold=True)
    T(surf,"SPACE SHOOTER  v2.0",13,W//2,194,NYEL)
    sx=int(W//2+75*math.sin(tick*.022)); sy=270
    fh=int(14+8*abs(math.sin(tick*.25)))
    pygame.draw.polygon(surf,NORA,[(sx-8,sy+16),(sx,sy+16+fh),(sx+8,sy+16)])
    pygame.draw.polygon(surf,NBLU,[(sx,sy-26),(sx+18,sy+16),(sx,sy+6),(sx-18,sy+16)])
    pygame.draw.polygon(surf,WHT, [(sx,sy-26),(sx+18,sy+16),(sx,sy+6),(sx-18,sy+16)],1)
    by=316
    BTN(surf,"PLAY",      W//2-110,by,    220,52,PURP,mp=mp)
    BTN(surf,"SHIP SHOP", W//2-110,by+64, 220,46,(20,80,150),mp=mp)
    BTN(surf,"HIGH SCORE",W//2-110,by+122,220,46,(60,40,10),mp=mp)
    BTN(surf,"QUIT",      W//2-110,by+180,220,42,(80,20,20),mp=mp)
    T(surf,f"Best:{sv.get('hs',0):,}  Coins:{sv.get('coins',0)}  Games:{sv.get('games',0)}",
      12,W//2,H-34,GRAY)
    RR(surf,(15,15,30),(0,H-22,W,22),rad=0,a=230)
    T(surf,"AD | SuperBlast — Download Free!",11,W//2,H-11,GOLD)

# ── Game Over ────────────────────────────────────────────────
def draw_over(surf,pl,wave,lv,hs,mp):
    ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,20,200)); surf.blit(ov,(0,0))
    RR(surf,(10,10,40),(28,108,W-56,H-185),rad=16,a=245)
    pygame.draw.rect(surf,NRED,(28,108,W-56,H-185),2,border_radius=16)
    T(surf,"GAME OVER",38,W//2,152,NRED,bold=True)
    T(surf,f"Level {lv}  |  Wave {wave}",18,W//2,198,WHT)
    T(surf,f"Score: {pl.score:,}",24,W//2,230,NYEL,bold=True)
    if pl.score>=hs and pl.score>0: T(surf,"NEW HIGH SCORE!",17,W//2,265,GOLD,bold=True)
    else: T(surf,f"Best: {hs:,}",16,W//2,265,GRAY)
    T(surf,f"Coins Earned: {pl.coins}",16,W//2,294,GOLD)
    y0=322
    BTN(surf,"Watch Ad — Get Extra Life",W//2-130,y0,260,46,(20,120,60),NGRN,mp=mp)
    BTN(surf,"PLAY AGAIN",W//2-110,y0+58, 220,44,PURP,mp=mp)
    BTN(surf,"MAIN MENU", W//2-110,y0+112,220,44,(30,50,100),mp=mp)
    return y0

# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════
def main():
    # ── Window opens HERE — fast ──────────────────────────────
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Galactic Assault v2.0")
    clock  = pygame.time.Clock()

    sv=load_save(); stars=Stars(); state=S_MENU; tick=0; mp=(0,0)
    pl=None; asts=[]; ufos=[]; ebs=[]; pups=[]; parts=[]; fts=[]
    boss=None; wave=1; lv=1; lsb=0; st=0; ut=0; bs=False; bwc=0
    adscr=None; adrs=None; shop=Shop(sv); lup=[]

    def cfg(): return LEVELS[min(lv,10)]

    def start():
        nonlocal pl,asts,ufos,ebs,pups,parts,fts,boss,wave,lv,lsb,st,ut,bs,bwc
        pl=Player(sv.get("skin",0))
        asts=[]; ufos=[]; ebs=[]; pups=[]; parts=[]; fts=[]
        boss=None; wave=1; lv=1; lsb=0; st=0; ut=0; bs=False; bwc=0
        sv["games"]=sv.get("games",0)+1
        do_wave()

    def do_wave():
        c=cfg()
        for _ in range(min(4+wave*2,16)):
            sz=random.choices(["large","medium","small"],weights=[3,4,3])[0]
            asts.append(Asteroid(size=sz,spd=c["asp"]))

    def end():
        nonlocal state
        hs=sv.get("hs",0)
        if pl.score>hs: sv["hs"]=pl.score
        sv["coins"]=sv.get("coins",0)+pl.coins
        sv["maxlv"]=max(sv.get("maxlv",1),lv)
        save_game(sv); state=S_OVER

    running=True
    while running:
        tick+=1; clock.tick(FPS); mp=pygame.mouse.get_pos()

        # ── Events ──────────────────────────────────────────
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                running=False; break

            elif ev.type==pygame.KEYDOWN:
                k=ev.key
                if k==pygame.K_ESCAPE:
                    if state==S_PLAY:                        state=S_PAUSE
                    elif state in(S_PAUSE,S_LVL):           state=S_PLAY
                    elif state in(S_MENU,S_HI,S_SHOP,S_OVER): running=False
                elif k==pygame.K_p:
                    if state==S_PLAY: state=S_PAUSE
                    elif state==S_PAUSE: state=S_PLAY
                elif k==pygame.K_RETURN and state==S_OVER:
                    start(); state=S_PLAY

            elif ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                pos=ev.pos; by=316

                if state==S_MENU:
                    if pygame.Rect(W//2-110,by,220,52).collidepoint(pos):     start(); state=S_PLAY
                    elif pygame.Rect(W//2-110,by+64,220,46).collidepoint(pos):  state=S_SHOP
                    elif pygame.Rect(W//2-110,by+122,220,46).collidepoint(pos): state=S_HI
                    elif pygame.Rect(W//2-110,by+180,220,42).collidepoint(pos): running=False

                elif state==S_SHOP:
                    r=shop.click(pos,sv.get("coins",0))
                    if r=="back": state=S_MENU

                elif state==S_HI:
                    if pygame.Rect(W//2-80,H-80,160,44).collidepoint(pos): state=S_MENU

                elif state==S_PAUSE:
                    if pygame.Rect(W//2-95,H//2+5,190,44).collidepoint(pos): state=S_PLAY
                    elif pygame.Rect(W//2-95,H//2+60,190,44).collidepoint(pos): state=S_MENU

                elif state==S_LVL:
                    for i,pw in enumerate(lup):
                        if pygame.Rect(50,228+i*96,W-100,84).collidepoint(pos):
                            if PUPS[pw]["dur"]>0: pl.pw[pw]=PUPS[pw]["dur"]*FPS
                            elif pw=="bomb":
                                for a in asts: boom(parts,a.x,a.y,NORA,8)
                                asts.clear(); ufos.clear()
                            fts.append(FT(W//2,H//2,PUPS[pw]["txt"].split("—")[0].strip(),PUPS[pw]["col"],15,90))
                            state=S_PLAY; break

                elif state==S_OVER:
                    y0=322
                    if pygame.Rect(W//2-130,y0,260,46).collidepoint(pos):
                        adscr=AdScr(); adrs="revive"; state=S_AD
                    elif pygame.Rect(W//2-110,y0+58,220,44).collidepoint(pos): start(); state=S_PLAY
                    elif pygame.Rect(W//2-110,y0+112,220,44).collidepoint(pos): state=S_MENU

                elif state==S_AD:
                    if adscr and adscr.ready and adscr.skip_R().collidepoint(pos):
                        if adrs=="revive": pl.lives=1; pl.alive=True; pl.inv=200; state=S_PLAY
                        adscr=None; adrs=None

        if not running: break

        # ── Game Update ─────────────────────────────────────
        if state==S_PLAY:
            keys=pygame.key.get_pressed(); c=cfg()
            pl.upd(keys,pups); st+=1; ut+=1

            if st>=c["sr"]:
                st=0
                if not boss or not boss.alive:
                    sz=random.choices(["large","medium","small"],weights=[3,4,3])[0]
                    asts.append(Asteroid(size=sz,spd=c["asp"]))

            if c["ufo"] and ut>=max(80,220-lv*10) and len(ufos)<2+lv//2:
                ut=0; ufos.append(UFO(lv))

            if wave>0 and wave%c["bw"]==0 and not bs:
                bs=True; bwc+=1; boss=Boss(bwc,lv)
                fts.append(FT(W//2,H//2,"BOSS INCOMING!",NRED,24,130))

            if boss and boss.alive:
                boss.upd()
                if boss.shoot():
                    angs=[-22,0,22] if lv>=4 else [0]
                    for a in angs: ebs.append(EB(boss.x,boss.y+boss.r,pl.x+math.sin(math.radians(a))*50,pl.y,spd=4+lv*.3))
                    if boss.phase==2: ebs.append(EB(boss.x,boss.y,pl.x,pl.y,spd=5+lv*.2))

            for u in ufos:
                u.upd()
                if u.shoot(): ebs.append(EB(u.x,int(u.yd),pl.x,pl.y,spd=3+lv*.25))

            for lst in (asts,ebs,pups,ufos):
                for obj in lst[:]:
                    obj.upd()
                    if not obj.alive: lst.remove(obj)
            for p in parts[:]:
                p.upd()
                if p.life<=0: parts.remove(p)
            for f in fts[:]:
                f.upd()
                if f.life<=0: fts.remove(f)

            # bullets vs asteroids
            for b in pl.buls[:]:
                if not b.alive: continue
                for a in asts[:]:
                    if b.R().colliderect(a.R()):
                        if not b.pierce: b.alive=False
                        if a.hit():
                            sc,cb=pl.add_score(a.sv)
                            fts.append(FT(a.x,a.y,f"+{sc}",NYEL if cb<5 else NPNK,15 if cb<5 else 21,55))
                            boom(parts,a.x,a.y,(200,140,80),10 if a.size=="small" else 20)
                            if a.size=="large": asts+=[Asteroid(a.x,a.y,"medium") for _ in range(2)]
                            elif a.size=="medium":
                                if random.random()<.5: asts.append(Asteroid(a.x,a.y,"small"))
                            roll=random.random()
                            if roll<.13: pups.append(PUp(a.x,a.y,random.choice([k for k in PUPS if k!="coin"])))
                            elif roll<.43: pups.append(PUp(a.x,a.y,"coin"))
                        if not b.alive: break

            # bullets vs UFOs
            for b in pl.buls[:]:
                if not b.alive: continue
                for u in ufos[:]:
                    if b.R().colliderect(u.R()):
                        if not b.pierce: b.alive=False
                        if u.hit():
                            sc,_=pl.add_score(u.sv); boom(parts,u.x,int(u.yd),NGRN,25)
                            fts.append(FT(u.x,int(u.yd),f"+{sc} UFO!",NGRN,17,60))
                            ufos.remove(u)
                            if random.random()<.25: pups.append(PUp(u.x,int(u.yd)))
                        break

            # bullets vs boss
            if boss and boss.alive:
                for b in pl.buls[:]:
                    if b.alive and b.R().colliderect(boss.R()):
                        if not b.pierce: b.alive=False
                        if boss.hit():
                            sc,_=pl.add_score(boss.sv)
                            fts.append(FT(boss.x,boss.y,f"+{sc} BOSS!",GOLD,20,120))
                            boom(parts,boss.x,boss.y,NPNK,60,7); boom(parts,boss.x,boss.y,NORA,40,5)
                            boss=None; wave+=1; bs=False; do_wave()

            # player collisions
            for a in asts[:]:
                if pl.R().colliderect(a.R()):
                    if pl.dmg(): boom(parts,pl.x,pl.y,NRED,25)
                    a.alive=False; asts.remove(a)
            for u in ufos[:]:
                if pl.R().colliderect(u.R()):
                    if pl.dmg(): boom(parts,pl.x,pl.y,NRED,20)
                    ufos.remove(u)
            for eb in ebs[:]:
                if eb.R().colliderect(pl.R()):
                    if pl.dmg(): boom(parts,pl.x,pl.y,NRED,15)
                    eb.alive=False; ebs.remove(eb)

            # powerup collection
            for pu in pups[:]:
                if pl.R().colliderect(pu.R()):
                    k=pu.kind
                    if k=="bomb":
                        for a in asts: boom(parts,a.x,a.y,NORA,8); pl.add_score(a.sv//2)
                        asts.clear(); ufos.clear()
                        fts.append(FT(W//2,H//2,"BOMB!",NORA,32,80))
                    elif k=="coin": pl.coins+=10; fts.append(FT(pu.x,pu.y,"+10 COINS",GOLD,14,50))
                    elif PUPS[k]["dur"]>0: pl.pw[k]=PUPS[k]["dur"]*FPS; fts.append(FT(pu.x,pu.y,PUPS[k]["ic"]+"!",PUPS[k]["col"],14,50))
                    pu.alive=False; pups.remove(pu)

            # wave clear
            if not asts and not ufos and (boss is None or not boss.alive) and not bs:
                wave+=1; bs=False; do_wave()
                fts.append(FT(W//2,H//2,f"WAVE {wave}!",NGRN,30,90))

            # level up
            lp=min((pl.score-lsb)/SPL,1.0)
            if lp>=1.0 and lv<10:
                lv+=1; lsb=pl.score; lup=random.sample(list(PUPS.keys()),3); state=S_LVL

            if not pl.alive: end()

        elif state==S_AD and adscr: adscr.upd()

        # ── Draw ────────────────────────────────────────────
        screen.fill(DBLU); stars.upd(); stars.draw(screen)

        if state==S_MENU:
            draw_menu(screen,sv,stars,tick,mp)

        elif state in(S_PLAY,S_LVL):
            for p in parts: p.draw(screen)
            for a in asts: a.draw(screen)
            for u in ufos: u.draw(screen)
            if boss and boss.alive: boss.draw(screen)
            for pu in pups: pu.draw(screen)
            for eb in ebs: eb.draw(screen)
            pl.draw(screen)
            for b in pl.buls: b.draw(screen)
            for f in fts: f.draw(screen)
            lp=min((pl.score-lsb)/SPL,1.0)
            draw_hud(screen,pl,wave,lv,lp)
            RR(screen,(15,15,30),(0,H-22,W,22),rad=0,a=220)
            T(screen,"AD | SuperBlast — Download Free!",11,W//2,H-11,GOLD)
            if state==S_LVL: draw_levelup(screen,lv,lup)

        elif state==S_PAUSE:
            for a in asts: a.draw(screen)
            pl.draw(screen)
            ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,0,20,180)); screen.blit(ov,(0,0))
            RR(screen,(10,10,40),(W//2-125,H//2-90,250,215),rad=16,a=245)
            pygame.draw.rect(screen,NBLU,(W//2-125,H//2-90,250,215),2,border_radius=16)
            T(screen,"PAUSED",30,W//2,H//2-58,WHT,bold=True)
            BTN(screen,"RESUME",W//2-95,H//2+5, 190,44,NGRN,mp=mp)
            BTN(screen,"MENU",  W//2-95,H//2+60,190,44,PURP,mp=mp)
            if pygame.Rect(W//2-95,H//2+5, 190,44).collidepoint(mp) and pygame.mouse.get_pressed()[0]: state=S_PLAY
            if pygame.Rect(W//2-95,H//2+60,190,44).collidepoint(mp) and pygame.mouse.get_pressed()[0]: state=S_MENU

        elif state==S_OVER:
            pl.draw(screen)
            draw_over(screen,pl,wave,lv,sv.get("hs",0),mp)

        elif state==S_AD:
            if adscr: adscr.draw(screen)

        elif state==S_SHOP:
            shop.draw(screen,sv.get("coins",0),mp)

        elif state==S_HI:
            screen.fill(DBLU)
            T(screen,"HIGH SCORES",30,W//2,70,GOLD,bold=True)
            RR(screen,(10,30,60),(28,108,W-56,215),rad=12,a=220)
            T(screen,"BEST SCORE",13,W//2,130,GRAY)
            T(screen,f"{sv.get('hs',0):,}",44,W//2,175,NYEL,bold=True)
            T(screen,f"Highest Level: {sv.get('maxlv',1)}",15,W//2,222,WHT)
            T(screen,f"Games Played: {sv.get('games',0)}",15,W//2,355,WHT)
            T(screen,f"Total Coins: {sv.get('coins',0)}",15,W//2,385,GOLD)
            BTN(screen,"BACK",W//2-80,H-80,160,44,PURP,mp=mp)
            if pygame.Rect(W//2-80,H-80,160,44).collidepoint(mp) and pygame.mouse.get_pressed()[0]: state=S_MENU

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__=="__main__":
    main()
