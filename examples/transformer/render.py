"""Transformer 连续机制动画：配音和时间轴由 workflow.py 提供。"""
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw
import bisect
import json
import math
import numpy as np
from motion.fonts import font
from motion.encode import encode

W, H, FPS = 1080, 1920, 30
DATA = None
DURATION = 0.0
CUE_STARTS = []
SUB_STARTS = []
BG = (9, 18, 31)
FG = (243, 246, 242)
MUT = (155, 175, 194)
GREEN = (78, 230, 191)
BLUE = (91, 181, 255)
PURPLE = (185, 151, 255)
GOLD = (255, 192, 100)
RED = (255, 127, 121)
EDGE = (42, 65, 85)
CX = 492
WORDS = ['小猫', '饿了', '所以', '它', '找食物']
XS = [82 + i * 168 for i in range(5)]
CENTERS = [x + 72 for x in XS]
TW = 144


def clamp(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, p):
    return a + (b - a) * p


def color(a, b, p):
    return tuple(round(lerp(x, y, clamp(p))) for x, y in zip(a, b))


@lru_cache(maxsize=1400)
def label(s, size, c, bold=False, latin=False):
    f = font(size, bold, latin)
    bb = f.getbbox(s)
    im = Image.new('RGBA', (max(1, math.ceil(f.getlength(s)) + 8), bb[3] - bb[1] + 10))
    ImageDraw.Draw(im).text((4, 4 - bb[1]), s, font=f, fill=c)
    return im


def text(im, s, x, y, size=42, c=FG, bold=False, center=False, latin=False):
    pic = label(s, size, c, bold, latin)
    im.paste(pic, (round(x - pic.width / 2 if center else x), round(y - pic.height / 2 if center else y)), pic)


def rr(im, box, fill, stroke=None, radius=16, width=2):
    ImageDraw.Draw(im).rounded_rectangle(tuple(round(v) for v in box), radius=radius, fill=fill, outline=stroke, width=width)


def line(im, pts, c=EDGE, width=3):
    ImageDraw.Draw(im).line([(round(x), round(y)) for x, y in pts], fill=c, width=width, joint='curve')


def dot(im, x, y, r, c):
    ImageDraw.Draw(im).ellipse((round(x-r), round(y-r), round(x+r), round(y+r)), fill=c)


def bezier(a, b, lift, steps=50):
    mid = ((a[0] + b[0]) / 2, min(a[1], b[1]) - lift)
    return [((1-p)**2*a[0]+2*(1-p)*p*mid[0]+p*p*b[0],
             (1-p)**2*a[1]+2*(1-p)*p*mid[1]+p*p*b[1]) for p in np.linspace(0, 1, steps)]


def arrow(im, a, b, c, width=4, head=12):
    line(im, [a, b], c, width)
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    pts = [b, (b[0]-head*math.cos(angle-.55), b[1]-head*math.sin(angle-.55)),
           (b[0]-head*math.cos(angle+.55), b[1]-head*math.sin(angle+.55))]
    ImageDraw.Draw(im).polygon(pts, fill=c)


def path(im, pts, c, p=1, width=3):
    n = max(2, math.ceil(len(pts)*clamp(p)))
    line(im, pts[:n], color(BG, c, .6), width)


def packet(im, pts, phase, c, radius=6):
    at = clamp(phase)*(len(pts)-1)
    k = min(int(at), len(pts)-2)
    p = at-k
    x, y = lerp(pts[k][0], pts[k+1][0], p), lerp(pts[k][1], pts[k+1][1], p)
    dot(im, x, y, radius+5, color(BG, c, .25))
    dot(im, x, y, radius, c)


def token(im, x, y, word, c=GREEN, active=1, width=TW, height=88, size=41):
    rr(im, (x, y, x+width, y+height), color(BG, c, .08+.13*active), color(EDGE, c, .35+.65*active), 14, 3)
    text(im, word, x+width/2, y+height/2, size, FG if active>.4 else MUT, True, True)


def row(im, y, active=None, c=GREEN):
    for i, (x, word) in enumerate(zip(XS, WORDS)):
        token(im, x, y, word, c, 1 if active is None else active[i])


def mesh(im, y, t, reveal=1, focus=None, c=GREEN):
    for i in range(5):
        for j in range(i+1, 5):
            if focus is not None and focus not in (i, j):
                continue
            a, b = (CENTERS[i], y), (CENTERS[j], y)
            if focus == i:
                a, b = b, a
            pts = bezier(a, b, 72+48*(j-i))
            path(im, pts, c, reveal, 4 if focus is not None else 3)
            if reveal > .98:
                packet(im, pts, (t*.5+i*.17+j*.11)%1, c, 5)


@lru_cache(None)
def background():
    yy, xx = np.mgrid[0:H, 0:W]
    glow = np.exp(-(((xx-470)/690)**2+((yy-920)/780)**2))
    arr = np.empty((H, W, 3), dtype=np.uint8)
    for i, b in enumerate(BG):
        arr[:, :, i] = b + glow*(7+i*3)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    for x in range(84, 925, 40):
        for y in range(540, 1440, 40):
            d.point((x,y), fill=(32, 49, 66))
    text(im, '科学精神', 78, 74, 32, FG, True)
    text(im, 'TRANSFORMER / 2017', 516, 83, 25, MUT, latin=True)
    line(im, [(82,156),(906,156)], EDGE, 2)
    return im


def title(im, tag, a, b, bcolor=GREEN, asize=78, bsize=72):
    text(im, tag, 78, 212, 32, MUT)
    text(im, a, 76, 286, asize, FG, True)
    text(im, b, 76, 397, bsize, bcolor, True)


def note(im, s, y=1404):
    text(im, s, CX, y, 29, MUT, center=True)


def opening(im, u, cue):
    text(im, '从 2017 年开始', 78, 219, 38, GOLD)
    text(im, 'Transformer', 76, 300, 102, FG, True, latin=True)
    text(im, '一句话，如何同时算？', 78, 442, 61, GREEN, True)
    mesh(im, 866, u, ease((u-.15)/1.2))
    row(im, 866)
    # 所有位置同步完成一个计算周期，而不是依次点亮。
    p = ease((u-1.2)/.85)
    for x in XS:
        rr(im, (x,985,x+TW,997), EDGE, radius=6)
        if p:
            rr(im, (x,985,x+TW*p,997), GREEN, radius=6)
    text(im, '各个位置，一起计算', CX, 1110, 48, GREEN, True, True)
    text(im, '用注意力，直接连接词语', CX, 1203, 42, FG, center=True)
    rr(im, (220,1300,764,1386), color(BG,GOLD,.09), color(BG,GOLD,.5), 42)
    text(im, '看得全，为什么还逐个说？', CX, 1343, 36, GOLD, center=True)


def strip(im, u, cue):
    title(im, '核心改变', '拿掉循环', '让词语直接联系')
    cut = ease((u-1.3)/1.0)
    text(im, '循环：前一步传给后一步', CX, 596, 42, color(FG,MUT,cut), center=True)
    for i in range(4):
        c = color(BLUE, BG, cut)
        arrow(im, (XS[i]+TW+3, 872), (XS[i+1]-5, 872), c, 4, 9)
        if cut < .7:
            phase = (u*1.2)%4
            if i <= phase < i+1:
                dot(im, lerp(XS[i]+TW,XS[i+1],phase-i),872,7,BLUE)
    mesh(im, 828, u, cut)
    row(im, 828, c=color(BLUE,GREEN,cut))
    if cut > .01:
        for x in XS:
            arrow(im, (x+72,970), (x+72,1035), color(BG,GREEN,cut), 4)
        text(im, '注意力：读取相关位置的信息', CX, 1150, 44, color(BG,GREEN,cut), True, True)
    note(im, '这里展示词语之间的信息交互')


def sequential(im, u, cue):
    title(im, '以前：循环模型', '第 10 个词', '要等前 9 个')
    step = min(9, int(max(0,u-.25)/.37))
    xs = [82+i*83 for i in range(10)]
    text(im, '一个接一个，沿着顺序推进', CX, 618, 42, MUT, center=True)
    for i, x in enumerate(xs):
        done = i < step
        on = i == step
        c = GOLD if i == 9 else BLUE
        token(im,x,803,str(i+1),c,1 if done or on else .05,width=70,height=94,size=39)
        if i < 9:
            line(im,[(x+70,850),(xs[i+1],850)],color(BG,GREEN,.85 if done else .25),4)
        if on:
            p = clamp((u-.25-i*.37)/.37)
            rr(im,(x,918,x+70,928),EDGE,radius=4)
            if p:
                rr(im,(x,918,x+70*p,928),c,radius=4)
    p = clamp((u-.25)/(9*.37))
    line(im,[(117,1040),(117,1080),(864,1080),(864,1040)],EDGE,3)
    line(im,[(117,1080),(117+747*p,1080)],BLUE,5)
    text(im, '后面的位置，依赖前面的结果', CX, 1190, 42, FG, center=True)
    text(im, '串行依赖', CX, 1300, 56, GOLD, True, True)


def attention(im,u,cue):
    title(im,'现在：自注意力','整句话','同时计算')
    p = ease((u-.15)/.7)
    mesh(im,782,u,ease((u-1.6)/.8))
    row(im,782,active=[p]*5)
    for x in XS:
        rr(im,(x,903,x+TW,915),EDGE,radius=6)
        if p:
            rr(im,(x,903,x+TW*p,915),GREEN,radius=6)
    text(im,'任意两个位置，直接建立联系',CX,996,43,GREEN,True,True)
    # 每个格子是一对位置，成块并行出现。
    for r in range(5):
        for c in range(5):
            x,y=342+c*62,1080+r*49
            val=.16+.44*(.5+.5*math.sin((r*7+c*3)*1.27))
            rr(im,(x,y,x+52,y+39),color(BG,GREEN,val*p),color(BG,GREEN,.35),7)
    text(im,'两两匹配',CX,1360,40,FG,True,True)
    note(im,'此处示意双向自注意力',1420)


def equation(im,y,highlight=None):
    size=44
    labels=[('Attention',FG),(' = ',MUT),('softmax',GREEN),('(',FG)]
    widths=[font(size,True,True).getlength(s) for s,c in labels]
    fracw=130
    tail=font(size,True,True).getlength(') V')
    x=CX-(sum(widths)+fracw+tail)/2
    for (s,c),w in zip(labels,widths):
        text(im,s,x+w/2,y,size,c,True,True,True)
        if s=='softmax' and highlight=='softmax':
            line(im,[(x,y+42),(x+w,y+42)],GREEN,4)
        x+=w
    qcolor=BLUE if highlight=='qk' else FG
    text(im,'QK',x+54,y-39,48,qcolor,True,True,True)
    text(im,'T',x+99,y-65,26,qcolor,True,True,True)
    line(im,[(x+10,y+2),(x+120,y+2)],MUT,3)
    text(im,'√d',x+58,y+42,46,GOLD,True,True,True)
    text(im,'k',x+94,y+60,28,GOLD,True,True,True)
    x+=fracw
    text(im,')',x+13,y,48,FG,True,True,True)
    text(im,'V',x+61,y,54,PURPLE,True,True,True)
    if highlight=='v':
        line(im,[(x+39,y+44),(x+82,y+44)],PURPLE,4)


def formula(im,u,cue):
    title(im,'核心公式','匹配、分配','再汇总信息')
    hi = 'softmax' if u < 4.35 else 'qk' if u < 5.8 else 'scale' if u < 7.1 else 'v'
    rr(im,(76,637,916,937),color(BG,BLUE,.045),EDGE,24)
    equation(im,781,hi)
    steps=[('QKᵀ','算匹配',BLUE),('÷ √dₖ','做缩放',GOLD),('softmax','变权重',GREEN),('× V','取信息',PURPLE)]
    for i,(a,b,c) in enumerate(steps):
        x=82+i*211
        rr(im,(x,1062,x+184,1256),color(BG,c,.09),color(BG,c,.55),16)
        text(im,a,x+92,1120,38,c,True,True)
        text(im,b,x+92,1204,40,FG,True,True)
        if i<3:
            arrow(im,(x+190,1157),(x+204,1157),MUT,3,8)
    text(im,'权重，决定从哪里读取多少信息',CX,1354,40,MUT,center=True)


def qk(im,u,cue):
    title(im,'读懂 Q 和 K','“我在找什么”','遇上“我是什么”',bsize=66)
    rows=[('Q','查询','我在找什么',GREEN,644),('K','键','我是什么',BLUE,1015)]
    for i,(letter,name,desc,c,y) in enumerate(rows):
        onset=0 if i==0 else cue['anchors']['K代表']-cue['start']
        p=ease((u-onset)/.35)
        rr(im,(82,y,906,y+270),color(BG,c,.06+.06*p),color(BG,c,.4+.3*p),24)
        text(im,letter,192,y+109,110,c,True,True,True)
        text(im,name,192,y+213,36,MUT,center=True)
        text(im,desc,577,y+109,54,FG,True,True)
        text(im,'用来发起匹配' if i==0 else '用来被匹配',577,y+206,37,MUT,center=True)
    a=(490,930); b=(490,996)
    arrow(im,a,b,GREEN,5)
    if u>1:
        packet(im,[a,b],(u*.9)%1,GREEN,7)
    note(im,'Q 与 K 的匹配，决定注意力分配')


def weights(im,u,cue):
    title(im,'从匹配到读取','先分配权重','再把信息汇总')
    text(im,'以「它」为查询，关注哪些词？',CX,574,42,FG,center=True)
    ws=[.66,.10,.06,.12,.06]
    row(im,662,active=[.95,.2,.12,.4,.12])
    p=ease((u-.15)/.85)
    for i,(x,w) in enumerate(zip(XS,ws)):
        h=188*(w/.66)*p
        rr(im,(x+44,790,x+100,1000),color(BG,GREEN,.035),radius=8)
        if h>1:
            rr(im,(x+44,1000-h,x+100,1000),color(BG,GREEN,.65 if i==0 else .3),GREEN if i==0 else None,8)
        text(im,f'{w:.2f}',x+72,1043,38,GREEN if i==0 else MUT,True,True,True)
    text(im,'V：每个词携带的信息',CX,1135,40,PURPLE,True,True)
    gather=ease((u-2.45)/1.5)
    for i,(x,w) in enumerate(zip(XS,ws)):
        a=(x+72,1188); b=(CX,1295)
        pts=[(lerp(a[0],b[0],p),lerp(a[1],b[1],p)) for p in np.linspace(0,1,35)]
        line(im,pts,color(BG,PURPLE,.22),max(2,round(11*w)))
        if gather>0:
            packet(im,pts,gather,PURPLE,round(5+13*w))
    rr(im,(271,1275,713,1361),color(BG,PURPLE,.14),PURPLE,18,3)
    text(im,'加权后的信息',CX,1318,44,FG,True,True)
    note(im,'权重与分词均为机制示意，非实测',1420)


def learned(im,u,cue):
    title(im,'注意力头学到了什么','指代与词语关系','从训练中出现',asize=70)
    text(im,'不同的头，可能关注不同关系',CX,576,40,MUT,center=True)
    y=829
    row(im,y,active=[.9,.25,.15,1,.2])
    a=(CENTERS[3],y);b=(CENTERS[0],y)
    pts=bezier(a,b,280)
    p=ease((u-.8)/1.0)
    path(im,pts,GOLD,p,6)
    if p>.98:
        packet(im,pts,(u*.47)%1,GOLD,7)
        text(im,'它 → 小猫',CX,642,46,GOLD,True,True)
    # 第二个头的联系使用另一种颜色，同一组词保持身份。
    pts2=bezier((CENTERS[1],y+100),(CENTERS[0],y+100),-290)
    p2=ease((u-2.4)/.85)
    if p2:
        path(im,pts2,PURPLE,p2,5)
        if p2>.98:
            packet(im,pts2,(u*.6)%1,PURPLE,7)
            text(im,'小猫 ↔ 饿了',552,1092,43,PURPLE,True,True)
    text(im,'没有显式写入语法规则',CX,1270,43,FG,center=True)
    note(im,'关系连线为示意；不同头的分工并不固定',1390)


def parallel(im,u,cue):
    title(im,'为什么训练能并行','同一层里','各位置一起算')
    for r in range(3):
        y=678+r*210
        p=ease((u-.18-r*.6)/.46)
        if r:
            for x in XS:
                arrow(im,(x+72,y-101),(x+72,y-18),color(BG,GREEN,.25+.55*p),4)
        for i,x in enumerate(XS):
            token(im,x,y,WORDS[i] if r==0 else '计算',GREEN,p,size=41)
            if p:
                rr(im,(x,y+105,x+TW*p,y+114),GREEN,radius=4)
    text(im,'位置之间并行',CX,1317,45,GREEN,True,True)
    note(im,'层与层之间，仍然依次推进',1400)


def generation(im,u,cue):
    title(im,'但生成仍然不同','输入可以并行','输出逐个生成',bcolor=GOLD)
    rr(im,(78,594,910,959),color(BG,GREEN,.045),color(BG,GREEN,.45),23)
    text(im,'Prefill',113,633,51,GREEN,True,latin=True)
    text(im,'处理已知输入',475,643,41,FG)
    onset=cue['anchors']['Prefill']-cue['start']
    p=ease((u-onset)/.6)
    for i,x in enumerate(XS):
        token(im,x+13,756,WORDS[i],GREEN,p,width=120,height=87,size=36)
        rr(im,(x+13,872,x+133,883),EDGE,radius=4)
        if p:
            rr(im,(x+13,872,x+13+120*p,883),GREEN,radius=4)
    text(im,'这些 Token 都已经给出',CX,922,34,MUT,center=True)
    rr(im,(78,1022,910,1395),color(BG,GOLD,.045),color(BG,GOLD,.45),23)
    text(im,'Decode',113,1063,51,GOLD,True,latin=True)
    text(im,'预测下一个 Token',449,1073,37,FG)
    start=cue['anchors']['Decode']-cue['start']
    outs=['它','想','吃','鱼','。']
    for i,x in enumerate(XS):
        p=ease((u-start-i*.49)/.24)
        token(im,x+13,1178,outs[i] if p>.1 else '·',GOLD,p,width=120,height=92,size=45)
        if i<4:
            arrow(im,(x+140,1224),(x+160,1224),color(BG,GOLD,.7 if p>.99 else .18),4,9)
    text(im,'已有输出，成为下一步的条件',CX,1337,37,MUT,center=True)
    note(im,'标准自回归生成；Token 指文本片段',1437)


def closing(im,u,cue):
    title(im,'Transformer 的两面','一次看见全局','一步一步说话',asize=76,bsize=76,bcolor=GOLD)
    text(im,'已经给出的上下文',CX,601,41,GREEN,True,True)
    mesh(im,863,u,ease((u-.2)/.8),focus=4)
    row(im,863)
    p=ease((u-3.2)/.6)
    if p:
        arrow(im,(CX,987),(CX,1080),color(BG,GOLD,p),5)
    text(im,'每次预测下一个 Token',CX,1144,43,GOLD,True,True)
    start=cue['anchors']['一步一步地说话']-cue['start']-.2
    for i,(x,word) in enumerate(zip(XS,['它','想','吃','鱼','。'])):
        p=ease((u-start-i*.38)/.24)
        token(im,x,1220,word if p>.1 else '·',GOLD,p,size=46)
        if i<4:
            arrow(im,(x+149,1264),(x+163,1264),color(BG,GOLD,.75 if p>.99 else .18),3,8)
    note(im,'标准自回归生成',1410)


SCENES = dict(hook=opening,strip=strip,seq=sequential,attn=attention,formula=formula,
              qk=qk,weight=weights,learn=learned,parallel=parallel,gen=generation,close=closing)


@lru_cache(None)
def subtitle_rows(s):
    replacements={'Q代表"我在找什么"，':'Q 代表“我在找什么”','K代表"我是什么"。':'K 代表“我是什么”'}
    s=replacements.get(s,s).rstrip('，。；：')
    special={
        '都绕不开2017年的Transformer':['都绕不开 2017 年的','Transformer'],
        'Transformer让整句话同时计算':['Transformer 让整句话','同时计算'],
        '但注意力头会自己学出指代和词语关系':['但注意力头会自己学出','指代和词语关系'],
        'Decode还是一个Token接一个Token':['Decode 还是一个 Token','接一个 Token'],
        '所以Transformer最有意思的地方是':['所以 Transformer','最有意思的地方是'],
    }
    if s in special:
        return special[s]
    if font(51).getlength(s)<=815:
        return [s]
    options=[i for i in range(1,len(s)) if font(51).getlength(s[:i])<=815 and font(51).getlength(s[i:])<=815]
    k=min(options,key=lambda i:abs(font(51).getlength(s[:i])-font(51).getlength(s[i:]))) if options else len(s)//2
    return [s[:k],s[k:]]


def scene_frame(idx,t):
    cue=DATA['cues'][idx]
    im=background().copy()
    SCENES[cue['scene']](im,t-cue['start'],cue)
    return im


@lru_cache(None)
def transition_end(idx):
    return scene_frame(idx,DATA['cues'][idx]['end']-.04)


def frame(t):
    idx=max(0,bisect.bisect_right(CUE_STARTS,t)-1)
    im=scene_frame(idx,t)
    u=t-CUE_STARTS[idx]
    if idx and u<.16:
        im=Image.blend(transition_end(idx-1),im,ease(u/.16))
    line(im,[(82,156),(82+824*t/DURATION,156)],GREEN,4)
    si=bisect.bisect_right(SUB_STARTS,t)-1
    if si>=0:
        sub=DATA['subtitles'][si]
        if t<=sub['end']:
            rows=subtitle_rows(sub['text'])
            y=1540 if len(rows)==1 else 1502
            for i,s in enumerate(rows):
                text(im,s,CX,y+i*72,51,FG,center=True)
    return im


def render(output):
    global DATA, DURATION, CUE_STARTS, SUB_STARTS
    output = Path(output)
    DATA = json.loads((output/'timeline.json').read_text(encoding='utf-8'))
    DURATION = DATA['duration']
    CUE_STARTS = [c['start'] for c in DATA['cues']]
    SUB_STARTS = [s['start'] for s in DATA['subtitles']]
    transition_end.cache_clear()
    encode(frame, output/'narration.mp3', output/'transformer.mp4', DURATION,
           fps=FPS, width=W, height=H)
