import copy,itertools,json,os,pathlib,random,subprocess,sys,tempfile,unittest
from unittest.mock import patch
from stnlab.projection import analyze,verify,validate
from stnlab import oracle
ROOT=pathlib.Path(__file__).resolve().parents[1]
class ProjectionTests(unittest.TestCase):
 def audit(self,data):
  r=analyze(data);self.assertTrue(verify(r));n=data['base']['nodes'];es=data['base']['edges'];keep=data['keep']
  if not r['consistent']:
   self.assertLess(r['negative_cycle']['weight'],0);self.assertIsNone(r['matrix']);self.assertEqual(r['pairs'],[]);self.assertFalse(r['query']['accepted']);return r
  def feasible(t,edges=es):self.assertEqual(t[0],0);self.assertTrue(all(t[v]-t[u]<=w for u,v,w in edges))
  feasible(r['schedule']);pos={u:i for i,u in enumerate(keep)}
  # Independent Fourier-Motzkin elimination, before any final all-pairs closure.
  rem=es[:]
  for k in set(range(n))-set(keep):
   incoming=[e for e in rem if e[1]==k and e[0]!=k];outgoing=[e for e in rem if e[0]==k and e[1]!=k]
   rem=[e for e in rem if k not in e[:2]]+[[a,d,w+z] for a,b,w in incoming for c,d,z in outgoing]
  ed,_=oracle.paths(n,rem);self.assertEqual(r['matrix'],[[ed[u][v]for v in keep]for u in keep])
  for q in r['pairs']:
   u,v,w=q['u'],q['v'],q['bound']
   if w is None:
    self.assertEqual(q['ray'][0],0);self.assertEqual(q['ray'][v]-q['ray'][u],1);self.assertTrue(all(q['ray'][b]-q['ray'][a]<=0 for a,b,_ in es))
   else:
    feasible(q['schedule']);self.assertEqual(q['schedule'][v]-q['schedule'][u],w);at=u;total=0
    for k in q['path']:a,b,z=es[k];self.assertEqual(a,at);at=b;total+=z
    self.assertEqual(at,v);self.assertEqual(total,w)
  for q in r['lost']:
   t=dict(zip(keep,q['values']));self.assertTrue(all(t[v]-t[u]<=w for u,v,w in es if u in t and v in t));self.assertGreater(t[q['v']]-t[q['u']],q['bound']);self.assertGreaterEqual(q['actual'],q['bound']+1)
  if r['query']['accepted']:
   t=r['query']['extension'];feasible(t);self.assertEqual([t[i]for i in keep],data['values'])
  else:
   q=r['query']['violation'];self.assertLess(q['cycle_weight'],0);self.assertGreater(q['actual'],q['bound'])
  return r
 def test_controls(self):
  for c in json.loads((ROOT/'docs/projection-controls.json').read_text()):self.audit(c['input'])
 def test_exhaustive_two_points(self):
  for ws in itertools.product([None,-1,0,1],repeat=4):
   es=[[u,v,ws[2*u+v]]for u in range(2)for v in range(2)if ws[2*u+v]is not None]
   for keep in [[0],[0,1]]:
    for vals in ([[0]]if len(keep)==1 else [[0,x]for x in [-2,0,2]]):self.audit(dict(base=dict(nodes=2,edges=es),keep=keep,values=vals))
 def test_three_point_elimination_and_assignments(self):
  for ws in itertools.product([None,-1,0,1],repeat=3):
   es=[[u,v,w]for (u,v),w in zip([(0,1),(1,2),(0,2)],ws)if w is not None]
   for keep in [[0],[0,1],[0,2],[0,1,2]]:
    for tail in itertools.product([-2,0,2],repeat=len(keep)-1):self.audit(dict(base=dict(nodes=3,edges=es),keep=keep,values=[0]+list(tail)))
 def test_seeded_and_permutations(self):
  rng=random.Random(57013)
  for _ in range(70):
   n=rng.randint(1,5);es=[[rng.randrange(n),rng.randrange(n),rng.randint(-4,5)]for _ in range(rng.randint(0,8))];keep=[0]+[i for i in range(1,n)if rng.randrange(2)];self.audit(dict(base=dict(nodes=n,edges=es),keep=keep,values=[0]+[rng.randint(-5,5)for _ in keep[1:]]))
  es=[[0,1,4],[1,2,3],[0,2,12],[2,1,-2],[1,0,-1]]
  for order in itertools.permutations(es):self.audit(dict(base=dict(nodes=3,edges=[list(e)for e in order]),keep=[0,2],values=[0,7]))
 def test_independent_verifier_and_forgeries(self):
  r=self.audit(dict(base=dict(nodes=3,edges=[[0,1,4],[1,2,3]]),keep=[0,2],values=[0,7]))
  with patch('stnlab.projection.analyze',side_effect=AssertionError),patch('stnlab.projection._build',side_effect=AssertionError),patch('stnlab.projection.floyd',side_effect=AssertionError),patch('stnlab.projection.potential',side_effect=AssertionError),patch('stnlab.projection.canonical_path',side_effect=AssertionError):self.assertTrue(verify(r))
  for key,value in [('schema','bad'),('consistent',False),('matrix',[[0,8],[None,0]]),('naive_equivalent',True),('lost',[]),('extra',1)]:
   x=copy.deepcopy(r);x[key]=value
   with self.assertRaises(ValueError):verify(x)
  for route in [('query','extension',1),('pairs',1,'schedule',1),('pairs',1,'path',0),('lost',0,'values',1)]:
   x=copy.deepcopy(r);a=x
   for k in route[:-1]:a=a[k]
   a[route[-1]]+=1
   with self.assertRaises(ValueError):verify(x)
 def test_validation(self):
  x=dict(base=dict(nodes=3,edges=[]),keep=[0,2],values=[0,4])
  for key,val in [('keep',[]),('keep',[2]),('keep',[0,2,1]),('keep',[0,0]),('keep',[False,2]),('keep',[0,3]),('values',[0]),('values',[1,4]),('values',[0,101]),('values',[0,4.0]),('values',[0,True]),('extra',0)]:
   y=copy.deepcopy(x);y[key]=val
   with self.assertRaises(ValueError):validate(y)
 def test_cli(self):
  with tempfile.TemporaryDirectory()as td:
   p=pathlib.Path(td);src=p/'input.json';out=p/'out.json';src.write_text(json.dumps(dict(base=dict(nodes=3,edges=[[0,1,4],[1,2,3]]),keep=[0,2],values=[0,7])))
   cmd=[sys.executable,'-m','stnlab.projection'];subprocess.run(cmd+[str(src),'--output',str(out)],check=True,capture_output=True);subprocess.run(cmd+[str(out),'--verify'],check=True,capture_output=True);original=out.read_bytes();src.write_text('{"base":{},"base":{}}');self.assertNotEqual(subprocess.run(cmd+[str(src),'--output',str(out)],capture_output=True).returncode,0);self.assertEqual(out.read_bytes(),original)
if __name__=='__main__':unittest.main()
