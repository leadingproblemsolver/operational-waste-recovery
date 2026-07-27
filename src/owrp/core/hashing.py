from __future__ import annotations
import hashlib, re

def stable_hash(text:str,length:int=32)->str: return hashlib.sha256(text.encode('utf-8')).hexdigest()[:length]
def normalized_tokens(text:str)->set[str]: return {t for t in re.findall(r"[a-z0-9_./-]+",text.lower()) if len(t)>2}
def similarity(a:str,b:str)->float:
    x,y=normalized_tokens(a),normalized_tokens(b)
    return len(x&y)/len(x|y) if x and y else 0.0
