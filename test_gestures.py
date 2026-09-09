import sys, math
sys.path.insert(0, 'd:/AI_MUSIC')
from engines.gesture_engine import _classify, _finger_states

class LM:
    def __init__(self, x, y): self.x=x; self.y=y

def make_hand(thumb, idx, mid, ring, pinky, left=False):
    """
    Build 21 landmarks.
    thumb=True  → thumb tip is far from index MCP (extended)
    thumb=False → thumb tip is close to index MCP (folded)
    left=True   → mirror x coords (left hand)
    """
    def m(x, y): return LM(1-x if left else x, y)

    lm = [m(0.5, 0.5)] * 21
    # WRIST=0
    lm[0]  = m(0.5, 0.90)
    # THUMB: CMC=1 MCP=2 IP=3 TIP=4
    lm[1]  = m(0.42, 0.82)
    lm[2]  = m(0.38, 0.76)
    lm[3]  = m(0.33, 0.70)
    # INDEX_MCP=5 — reference for thumb extension
    lm[5]  = m(0.52, 0.62)
    # Thumb tip: extended = far from index MCP, folded = close
    lm[4]  = m(0.22 if thumb else 0.44, 0.65)
    # INDEX MCP=5 PIP=6 TIP=8
    lm[6]  = m(0.52, 0.52)
    lm[7]  = m(0.52, 0.42)
    lm[8]  = m(0.52, 0.28 if idx else 0.58)
    # MIDDLE MCP=9 PIP=10 TIP=12
    lm[9]  = m(0.50, 0.60)
    lm[10] = m(0.50, 0.50)
    lm[11] = m(0.50, 0.40)
    lm[12] = m(0.50, 0.26 if mid else 0.56)
    # RING MCP=13 PIP=14 TIP=16
    lm[13] = m(0.48, 0.61)
    lm[14] = m(0.48, 0.51)
    lm[15] = m(0.48, 0.41)
    lm[16] = m(0.48, 0.27 if ring else 0.57)
    # PINKY MCP=17 PIP=18 TIP=20
    lm[17] = m(0.46, 0.63)
    lm[18] = m(0.46, 0.53)
    lm[19] = m(0.46, 0.43)
    lm[20] = m(0.46, 0.29 if pinky else 0.59)
    return lm

tests = [
    # (label, thumb, idx, mid, ring, pinky, left)
    ("Open Hand   RIGHT", True,  True,  True,  True,  True,  False),
    ("Open Hand   LEFT",  True,  True,  True,  True,  True,  True),
    ("Fist        RIGHT", False, False, False, False, False, False),
    ("Fist        LEFT",  False, False, False, False, False, True),
    ("Thumb Up    RIGHT", True,  False, False, False, False, False),
    ("Thumb Up    LEFT",  True,  False, False, False, False, True),
    ("Index Fing  RIGHT", False, True,  False, False, False, False),
    ("Index Fing  LEFT",  False, True,  False, False, False, True),
    ("Rock        RIGHT", False, True,  False, False, True,  False),
    ("Rock        LEFT",  False, True,  False, False, True,  True),
    ("Two Fingers RIGHT", False, True,  True,  False, False, False),
    ("Two Fingers LEFT",  False, True,  True,  False, False, True),
]

expected_map = {
    "Open Hand":    "Open Hand",
    "Fist":         "Fist",
    "Thumb Up":     "Thumb Up",
    "Index Fing":   "Index Finger",
    "Rock":         "Rock",
    "Two Fingers":  "Two Fingers",
}

all_ok = True
for label, thumb, idx, mid, ring, pinky, left in tests:
    lm = make_hand(thumb, idx, mid, ring, pinky, left)
    g, c = _classify(lm)
    key = label.split()[0] + (" " + label.split()[1] if label.split()[0] in ("Index","Two","Open","Thumb") else "")
    key = key.strip()
    exp_key = label.rsplit("  ", 1)[0].strip()
    # find expected
    exp = next((v for k,v in expected_map.items() if exp_key.startswith(k)), None)
    ok = g.value == exp
    print(f"  {'OK  ' if ok else 'FAIL'} {label:22s} -> {g.value:15s} ({c:.0%})")
    if not ok: all_ok = False

print()
print("ALL PASSED" if all_ok else "SOME TESTS FAILED")
