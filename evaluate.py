"""Small hand-authored synthetic holdout: a smoke test, not a production benchmark."""
import json
from engine import investigate
CASES=[
 ('connection_pool','database','Clients waiting for connection; pool exhausted'),
 ('connection_pool','database','Too many connections and acquire timeout'),
 ('bad_release','api','Exception spike in new release version'),
 ('bad_release','api','Deployment regression with undefined attribute'),
 ('cache_failure','cache','Redis unavailable with connection refused'),
 ('cache_failure','cache','Cache memory eviction and miss surge'),
 ('resource_pressure','worker','Worker memory pressure and CPU saturation'),
 ('resource_pressure','worker','Out of memory killed with queue backlog'),
 ('upstream_failure','upstream','External provider timeout and circuit breaker'),
 ('upstream_failure','upstream','Third party unavailable with rate limit'),
]
def evaluate():
 results=[]
 for expected,service,message in CASES:
  r=investigate([{'service':service,'message':message,'severity':'error'},{'service':'gateway','message':'Request failed','severity':'error'}])
  results.append({'expected':expected,'predicted':r['hypotheses'][0]['key'],'correct':r['hypotheses'][0]['key']==expected})
 return {'dataset':'10 hand-authored synthetic cases; vocabulary overlaps training phrases','top1_accuracy':sum(r['correct'] for r in results)/len(results),'cases':results}
if __name__=='__main__':print(json.dumps(evaluate(),indent=2))
