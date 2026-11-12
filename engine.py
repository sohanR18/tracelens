"""TraceLens: interpretable incident ranking with Bayesian text classification."""
import math, re, random
from collections import Counter

CAUSES = {
 "connection_pool": {"title":"Database connection pool exhaustion", "service":"database", "signals":["connection pool exhausted", "too many connections", "connection acquire timeout", "database waiting clients"], "action":"Compare active connections with the configured pool limit; inspect unreturned connections before increasing capacity."},
 "bad_release": {"title":"Application release regression", "service":"api", "signals":["new release exception", "deployment followed by error spike", "undefined attribute exception", "version regression stacktrace"], "action":"Compare error rates by release version and canary traffic; test rollback in a controlled environment."},
 "cache_failure": {"title":"Cache disruption", "service":"cache", "signals":["redis connection refused", "cache miss surge", "cache eviction memory", "redis timeout unavailable"], "action":"Inspect cache health and hit rate, then check whether database traffic increased after cache failures."},
 "resource_pressure": {"title":"Compute resource saturation", "service":"worker", "signals":["cpu throttling saturation", "out of memory killed", "memory pressure restart", "worker queue backlog"], "action":"Inspect CPU throttling, memory limits, and queue age; isolate the workload responsible before scaling."},
 "upstream_failure": {"title":"External dependency failure", "service":"upstream", "signals":["upstream gateway timeout", "external provider unavailable", "third party rate limit", "upstream circuit breaker open"], "action":"Check provider status and outbound request traces; validate bounded retries and circuit-breaker behavior."}
}
GRAPH={"upstream":["api"],"database":["api","worker"],"cache":["api"],"worker":["api"],"api":["gateway"],"gateway":[]}

def tokens(text): return re.findall(r"[a-z]+", text.lower())

class Classifier:
 def __init__(self):
  self.counts={k:Counter(tokens(" ".join(v["signals"]))) for k,v in CAUSES.items()}
  self.vocab=set(w for c in self.counts.values() for w in c)
 def predict(self,text):
  words=[w for w in tokens(text) if w in self.vocab]
  scores={k:sum(math.log((c[w]+1)/(sum(c.values())+len(self.vocab))) for w in words) for k,c in self.counts.items()}
  peak=max(scores.values()); weights={k:math.exp(v-peak) for k,v in scores.items()}
  return {k:v/sum(weights.values()) for k,v in weights.items()}

MODEL=Classifier()

def descendants(service):
 seen=set(); pending=list(GRAPH.get(service,[]))
 while pending:
  item=pending.pop()
  if item not in seen: seen.add(item); pending.extend(GRAPH.get(item,[]))
 return seen

def investigate(events, excluded=None):
 if not isinstance(events,list) or not events or len(events)>5000: raise ValueError("Supply between 1 and 5000 events.")
 clean=[]
 for i,e in enumerate(events):
  if not isinstance(e,dict) or not isinstance(e.get("message"),str) or len(e["message"])>10000: raise ValueError("Every event needs a message string of at most 10,000 characters.")
  if excluded and e.get("service")==excluded: continue
  clean.append({"id":f"E{i+1:03}","service":str(e.get("service","unknown"))[:80],"time":str(e.get("time","—"))[:80],"message":e["message"],"severity":str(e.get("severity","info"))[:20]})
 if not clean: raise ValueError("The intervention removed all evidence.")
 observed={e["service"] for e in clean if e["severity"] in ("error","critical","warning")}
 hypotheses=[]
 for key,cause in CAUSES.items():
  evidence=[]
  for e in clean:
   probs=MODEL.predict(e["message"]); relevance=probs[key]
   if relevance>.27: evidence.append({**e,"relevance":round(relevance,3)})
  evidence.sort(key=lambda e:e["relevance"],reverse=True)
  # Saturating aggregation prevents duplicate log volume from dominating ranking.
  unique={e["message"]:e["relevance"] for e in evidence}
  text_score=1-math.prod(1-v for v in sorted(unique.values(),reverse=True)[:3])
  reachable=descendants(cause["service"])
  coverage=len(reachable & observed)/max(1,len(observed))
  score=.85*text_score+.15*coverage if evidence else 0
  hypotheses.append({"key":key,"title":cause["title"],"service":cause["service"],"score":round(score,4),"coverage":round(coverage,3),"evidence":evidence[:5],"action":cause["action"],"affected":sorted(reachable & observed)})
 hypotheses.sort(key=lambda h:h["score"],reverse=True)
 return {"hypotheses":hypotheses,"events":clean,"graph":GRAPH,"excluded":excluded,"status":"supported" if hypotheses[0]["score"]>.45 else "insufficient evidence","method":"Smoothed multinomial Naive Bayes + dependency coverage. Scores are ranking signals, not calibrated probabilities. Interventions remove observations; they do not prove causality."}

DEMO=[
 {"time":"14:02:00","service":"api","severity":"info","message":"Deployment v2.8.1 completed"},
 {"time":"14:03:12","service":"database","severity":"error","message":"Connection pool exhausted: 100 active connections; 82 waiting clients"},
 {"time":"14:03:15","service":"database","severity":"error","message":"Connection acquire timeout after 30000ms; too many connections"},
 {"time":"14:03:22","service":"worker","severity":"warning","message":"Job processing latency increased; waiting on database"},
 {"time":"14:03:25","service":"api","severity":"error","message":"Request failed with 503 while waiting for database connection"},
 {"time":"14:03:30","service":"gateway","severity":"error","message":"Elevated 503 responses on checkout route"}]
