import copy,itertools,json,pathlib,random,subprocess,sys,tempfile,unittest
from unittest.mock import patch
from stnlab.conflicts import analyze,verify
from stnlab import oracle
ROOT=pathlib.Path(__file__).resolve().parents[1]
class ConflictTests(unittest.TestCase):
 def audit(self,data):
  r=analyze(data);self.assertTrue(verify(r));es=data['edges'];n=data['nodes'];m=len(es);full=(1<<m)-1
  def schedule(t,ids):self.assertEqual(t[0],0);self.assertEqual(len(t),n);self.assertTrue(all(t[es[i][1]]-t[es[i][0]]<=es[i][2]for i in ids))
  def cycle(c,ids):
   ix=c['edges'];self.assertTrue(set(ix)<=set(ids));self.assertEqual(len(ix),len(set(ix)));self.assertTrue(all(es[a][1]==es[b][0]for a,b in zip(ix,ix[1:]+ix[:1])));self.assertEqual(c['weight'],sum(es[i][2]for i in ix));self.assertLess(c['weight'],0)
  for c in r['conflicts']:
   cycle(c['cycle'],c['edges']);self.assertEqual(set(c['cycle']['edges']),set(c['edges']))
   for d in c['deletions']:schedule(d['schedule'],set(c['edges'])-{d['edge']})
  for c in r['repairs']:
   schedule(c['schedule'],c['kept']);self.assertEqual(set(c['kept']),set(range(m))-set(c['removed']))
   # Every removed edge must actually be violated by every remaining-system solution.
   self.assertTrue(all(c['schedule'][es[i][1]]-c['schedule'][es[i][0]]>es[i][2]for i in c['removed']))
   for d in c['restorations']:cycle(d['cycle'],set(c['kept'])|{d['edge']})
  for mask,ok in enumerate(r['feasible']):
   ix={i for i in range(m)if mask>>i&1};self.assertEqual(not ok,any(set(c['edges'])<=ix for c in r['conflicts']));removed=set(range(m))-ix;self.assertEqual(ok,any(set(c['removed'])<=removed for c in r['repairs']))
  return r
 def test_controls_and_minimal_not_minimum(self):
  for c in json.load(open(ROOT/'docs/conflict-controls.json')):self.audit(c['input'])
  r=analyze(json.load(open(ROOT/'docs/conflict-controls.json'))[0]['input']);self.assertEqual(r['minimum_repairs'],[[0]]);self.assertEqual([x['removed']for x in r['repairs']],[[0],[1,2],[1,3]])
 def test_all_two_point_networks_against_integer_grid(self):
  for states in itertools.product([None,-1,0,1],repeat=4):
   es=[[u,v,w]for (u,v),w in zip(itertools.product(range(2),repeat=2),states)if w is not None];r=self.audit(dict(nodes=2,edges=es))
   for mask,ok in enumerate(r['feasible']):self.assertEqual(ok,any(all(t[v]-t[u]<=w for i,(u,v,w)in enumerate(es)if mask>>i&1)for t in ([0,x]for x in range(-2,3))))
 def test_seeded_and_edge_permutations(self):
  rng=random.Random(904)
  for _ in range(50):
   n=rng.randint(1,6);self.audit(dict(nodes=n,edges=[[rng.randrange(n),rng.randrange(n),rng.randint(-3,3)]for _ in range(rng.randint(0,8))]))
  data=json.load(open(ROOT/'docs/conflict-controls.json'))[0]['input']
  for perm in itertools.permutations(data['edges']):self.audit(dict(nodes=3,edges=list(perm)))
 def test_every_subset_cycle_reference(self):
  data=dict(nodes=3,edges=[[0,1,-1],[1,2,0],[2,0,0],[1,0,0],[0,2,2],[2,2,0]]);r=self.audit(data)
  for mask,ok in enumerate(r['feasible']):self.assertEqual(ok,not oracle.cycles(3,[e for i,e in enumerate(data['edges'])if mask>>i&1]))
 def test_forgeries_and_exact_types(self):
  data=json.load(open(ROOT/'docs/conflict-controls.json'))[0]['input'];r=analyze(data)
  for mutate in [lambda x:x.update(extra=0),lambda x:x.update(minimum_removals=True),lambda x:x['conflicts'].pop(),lambda x:x['repairs'].pop(),lambda x:x['feasible'].__setitem__(0,False),lambda x:x['hits'][0].__setitem__(0,99),lambda x:x['conflicts'][0]['cycle'].update(weight=0),lambda x:x['repairs'][0]['schedule'].__setitem__(0,1),lambda x:x['repairs'][0]['restorations'][0]['cycle']['edges'].pop()]:
   q=copy.deepcopy(r);mutate(q)
   with self.assertRaises(ValueError):verify(q)
 def test_verifier_independent(self):
  r=analyze(dict(nodes=3,edges=[[0,1,-1],[1,0,0]]))
  with patch('stnlab.conflicts.analyze',side_effect=RuntimeError),patch('stnlab.conflicts.floyd',side_effect=RuntimeError),patch('stnlab.conflicts.potential',side_effect=RuntimeError),patch('stnlab.conflicts.negative_cycle',side_effect=RuntimeError):self.assertTrue(verify(r))
 def test_cli_atomic_and_rejection(self):
  with tempfile.TemporaryDirectory()as t:
   p=pathlib.Path(t);(p/'in.json').write_text('{"nodes":2,"edges":[[0,1,-1],[1,0,0]]}');cmd=[sys.executable,'-m','stnlab.conflicts'];subprocess.run(cmd+[str(p/'in.json'),'--output',str(p/'out.json')],check=True);self.assertTrue(verify(json.load(open(p/'out.json'))));subprocess.run(cmd+[str(p/'out.json'),'--verify'],check=True,capture_output=True);before=(p/'out.json').read_bytes();(p/'in.json').write_text('{"nodes":true,"edges":[]}');q=subprocess.run(cmd+[str(p/'in.json'),'--output',str(p/'out.json')],capture_output=True);self.assertNotEqual(q.returncode,0);self.assertEqual((p/'out.json').read_bytes(),before)
if __name__=='__main__':unittest.main()
