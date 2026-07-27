from __future__ import annotations
from datetime import datetime, timezone
import json
from typing import Any
from owrp.core.hashing import stable_hash
from owrp.core.types import Interaction

def _int(v):
    try: return int(v or 0)
    except (ValueError,TypeError): return 0
def _float(v):
    try: return float(v or 0)
    except (ValueError,TypeError): return 0.0
def _now(): return datetime.now(timezone.utc).isoformat()
def _tuple(v): return tuple(str(x) for x in v) if isinstance(v,list) else (() if v in (None,'') else (str(v),))

def canonical(raw:dict[str,Any])->Interaction:
    pt=_int(raw.get('prompt_tokens')); ct=_int(raw.get('completion_tokens'))
    event_id=str(raw.get('event_id') or raw.get('interaction_id') or stable_hash(json.dumps(raw, sort_keys=True, separators=(',', ':'), default=str), 24))
    return Interaction(event_id,str(raw.get('timestamp') or _now()),str(raw.get('user_id') or 'unknown'),str(raw.get('repo_id') or 'unknown'),str(raw.get('source') or 'canonical_jsonl'),str(raw.get('model_name') or raw.get('model') or 'unknown'),str(raw.get('prompt') or ''),str(raw.get('response') or ''),pt,ct,_int(raw.get('total_tokens') if raw.get('total_tokens') is not None else pt+ct),_float(raw.get('cost_usd')),str(raw.get('classification') or 'unclassified'),_tuple(raw.get('files_read')),_tuple(raw.get('files_modified')),raw.get('metadata') if isinstance(raw.get('metadata'), dict) else {})

def openai_usage(raw:dict[str,Any])->Interaction:
    usage=raw.get('usage') or {}; req=raw.get('request') or {}; resp=raw.get('response') or {}
    merged={'event_id':raw.get('id'),'timestamp':raw.get('timestamp'),'user_id':raw.get('user_id'),'repo_id':raw.get('repo_id'),'source':'openai_usage','model_name':raw.get('model') or resp.get('model'),'prompt':raw.get('prompt') or req.get('prompt') or req.get('input'),'response':raw.get('output') or resp.get('output_text'),'prompt_tokens':usage.get('prompt_tokens') or usage.get('input_tokens'),'completion_tokens':usage.get('completion_tokens') or usage.get('output_tokens'),'total_tokens':usage.get('total_tokens'),'cost_usd':raw.get('cost_usd'),'classification':raw.get('classification'),'files_read':raw.get('files_read'),'files_modified':raw.get('files_modified'),'metadata':{'provider_id':raw.get('id')}}
    return canonical(merged)

def generic(raw:dict[str,Any], mapping:dict[str,str]|None=None)->Interaction:
    mapping=mapping or {}; mapped={dst:raw.get(src) for dst,src in mapping.items()}; mapped.update({k:v for k,v in raw.items() if k not in mapped}); return canonical(mapped)

ADAPTERS={'canonical':canonical,'openai':openai_usage,'generic':generic}
def adapt(raw,fmt='canonical',mapping=None):
    if fmt not in ADAPTERS: raise ValueError(f"unsupported format: {fmt}")
    return generic(raw,mapping) if fmt=='generic' else ADAPTERS[fmt](raw)
