import sys; sys.path.insert(0,'d:/AI_MUSIC')
from engines.gesture_engine import _classify
class LM:
    def __init__(self,x,y): self.x=x; self.y=y
def make(th,ix,mi,ri,pi,flip=False):
    def p(x,y): return LM(1-x if flip else x,y)
    lm=[p(0.5,0.5)]*21
    lm[0]=p(.5,.9);lm[2]=p(.38,.76);lm[3]=p(.30,.68)
    lm[4]=p(.20 if th else .48,.62);lm[5]=p(.52,.62)
    lm[6]=p(.52,.50);lm[8]=p(.52,.28 if ix else .68)
    lm[9]=p(.50,.60);lm[10]=p(.50,.50);lm[12]=p(.50,.26 if mi else .66)
    lm[13]=p(.48,.61);lm[14]=p(.48,.51);lm[16]=p(.48,.27 if ri else .67)
    lm[17]=p(.46,.63);lm[18]=p(.46,.53);lm[20]=p(.46,.29 if pi else .69)
    return lm
tests=[
    ('Open Hand R',True,True,True,True,True,False,'Open Hand'),
    ('Open Hand L',True,True,True,True,True,True,'Open Hand'),
    ('Fist R',False,False,False,False,False,False,'Fist'),
    ('Fist L',False,False,False,False,False,True,'Fist'),
    ('Index R',False,True,False,False,False,False,'Index Finger'),
    ('Index L',False,True,False,False,False,True,'Index Finger'),
    ('Rock R',False,True,False,False,True,False,'Rock'),
    ('Rock L',False,True,False,False,True,True,'Rock'),
    ('Peace R',False,True,True,False,False,False,'Two Fingers'),
    ('Peace L',False,True,True,False,False,True,'Two Fingers'),
]
ok=True
for l,th,ix,mi,ri,pi,fl,exp in tests:
    g,c=_classify(make(th,ix,mi,ri,pi,fl))
    r=g.value==exp
    print(f'  {"OK  " if r else "FAIL"} {l:12} -> {g.value} ({c:.0%})')
    if not r: ok=False
print()
print('ALL PASSED' if ok else 'SOME FAILED')
