import copy,itertools,json,os,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from stnlab import insertions as s,oracle
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/insertion-controls.json').read_text())

class InsertionTests(unittest.TestCase):
    def audit(self,r):
        self.assertTrue(s.verify(r));data=r['input'];n=data['base']['nodes'];base=data['base']['edges'];es=base+[data['candidate']];k=len(base)
        def feasible(t,edges):
            self.assertEqual(t[0],0)
            for u,v,w in edges:self.assertLessEqual(t[v]-t[u],w)
        def path(ids,u,v,weight,edges):
            at=u;total=0
            for j in ids:a,b,w=edges[j];self.assertEqual(a,at);at=b;total+=w
            self.assertEqual((at,total),(v,weight))
        if not r['base_consistent']:self.assertIsNone(r['threshold']);self.assertEqual(r['spectrum'],[])
        else:
            feasible(r['base_schedule'],base);a,b,w=data['candidate'];t=r['threshold']
            if t['lower'] is not None:
                path(t['return_path'],b,a,-t['lower'],base);feasible(t['boundary_schedule'],base+[[a,b,t['lower']]])
                self.assertEqual(t['boundary_schedule'][b]-t['boundary_schedule'][a],t['lower'])
                path(t['below_cycle']['edges'],a,a,-1,base+[[a,b,t['lower']-1]])
            self.assertEqual(len(r['spectrum']),41)
            for x,y in zip(r['spectrum'],r['spectrum'][1:]):
                if x['changed'] is not None and y['changed'] is not None:self.assertGreaterEqual(x['changed'],y['changed'])
        if not r['consistent']:
            c=r['cycle'];start=es[c['edges'][0]][0];path(c['edges'],start,start,c['weight'],es);self.assertLess(c['weight'],0);self.assertEqual(r['cells'],[]);return
        feasible(r['schedule'],es)
        for q in r['cells']:
            if q['after'] is None:
                self.assertEqual(q['ray'][0],0);self.assertEqual(q['ray'][q['v']]-q['ray'][q['u']],1)
                for u,v,w in es:self.assertLessEqual(q['ray'][v]-q['ray'][u],0)
            else:
                path(q['path'],q['u'],q['v'],q['after'],es);feasible(q['schedule'],es);self.assertEqual(q['schedule'][q['v']]-q['schedule'][q['u']],q['after'])
            if q['via'] is not None:path(q['left_path']+[k]+q['right_path'],q['u'],q['v'],q['via'],es)
            if q['changed']:self.assertIn(k,q['path'])

    def test_controls(self):
        for c in CONTROLS:self.audit(s.analyze(c['input']))
        r=s.analyze(CONTROLS[0]['input']);self.assertEqual(r['classification'],'tightening');self.assertEqual(r['matrix'][0][2],6)
        self.assertEqual(s.analyze(CONTROLS[8]['input'])['threshold']['lower'],-100)
        self.assertEqual(s.analyze(CONTROLS[9]['input'])['input']['base']['edges'].__len__(),12)

    def test_exhaustive_two_node_insertion_all_endpoints(self):
        for weights in itertools.product([None,-1,0,1],repeat=4):
            edges=[[u,v,w] for (u,v),w in zip(itertools.product(range(2),repeat=2),weights) if w is not None]
            for a,b in itertools.product(range(2),repeat=2):
                for w in [-1,0,1]:self.audit(s.analyze(dict(base=dict(nodes=2,edges=edges),candidate=[a,b,w])))

    def test_all_three_node_acyclic_bases(self):
        for ws in itertools.product([None,-1,0,1],repeat=3):
            edges=[[u,v,w] for (u,v),w in zip([(0,1),(0,2),(1,2)],ws) if w is not None]
            for a,b in itertools.product(range(3),repeat=2):
                for w in [-1,0,1]:self.audit(s.analyze(dict(base=dict(nodes=3,edges=edges),candidate=[a,b,w])))

    def test_seeded_networks_and_relabelings(self):
        rng=random.Random(782)
        for _ in range(60):
            n=rng.randint(1,5);edges=[[rng.randrange(n),rng.randrange(n),rng.randint(-5,8)] for _ in range(rng.randrange(9))];self.audit(s.analyze(dict(base=dict(nodes=n,edges=edges),candidate=[rng.randrange(n),rng.randrange(n),rng.randint(-8,8)])))
        data=CONTROLS[0]['input'];r=s.analyze(data)
        for perm in itertools.permutations(range(3)):
            raw=dict(base=dict(nodes=3,edges=[[perm[u],perm[v],w] for u,v,w in data['base']['edges']]),candidate=[perm[data['candidate'][0]],perm[data['candidate'][1]],data['candidate'][2]])
            q=s.analyze(raw);self.audit(q)
            for i,j in itertools.product(range(3),repeat=2):self.assertEqual(r['matrix'][i][j],q['matrix'][perm[i]][perm[j]])
        for perm in itertools.permutations(range(len(data['base']['edges']))):
            q=s.analyze(dict(base=dict(nodes=3,edges=[data['base']['edges'][i] for i in perm]),candidate=data['candidate']));self.assertEqual(q['matrix'],r['matrix'])

    def test_generator_updates_from_one_old_matrix(self):
        calls=[];original=s.floyd
        def one(n,edges):calls.append(copy.deepcopy(edges));return original(n,edges)
        with patch.object(s,'floyd',side_effect=one):r=s.analyze(CONTROLS[0]['input'])
        self.assertEqual(calls,[CONTROLS[0]['input']['base']['edges']]);self.assertTrue(s.verify(r))

    def test_checker_disabled_generation(self):
        reports=[s.analyze(c['input']) for c in CONTROLS]
        with patch.object(s,'analyze',side_effect=AssertionError),patch.object(s,'floyd',side_effect=AssertionError),patch.object(s,'potential',side_effect=AssertionError),patch.object(s,'canonical_path',side_effect=AssertionError),patch.object(s,'negative_cycle',side_effect=AssertionError):
            for r in reports:self.assertTrue(s.verify(r))

    def test_forged_fields_and_invalid_inputs(self):
        r=s.analyze(CONTROLS[0]['input'])
        paths=[['classification'],['consistent'],['base_consistent'],['matrix',0,2],['schedule',0],['threshold','lower'],['threshold','below_cycle','weight'],['threshold','boundary_schedule',0],['cells',2,'before'],['cells',2,'via'],['cells',2,'changed'],['cells',2,'path'],['cells',2,'schedule'],['cells',2,'left_path'],['spectrum',20,'classification'],['spectrum',20,'changed']]
        for path in paths:
            q=copy.deepcopy(r);p=q
            for key in path[:-1]:p=p[key]
            p[path[-1]]='forged'
            with self.assertRaises(ValueError):s.verify(q)
        q=copy.deepcopy(r);q['extra']=0
        with self.assertRaises(ValueError):s.verify(q)
        for data in [{},dict(base=CONTROLS[0]['input']['base'],candidate=[True,1,2]),dict(base=CONTROLS[0]['input']['base'],candidate=[0,3,2]),dict(base=CONTROLS[0]['input']['base'],candidate=[0,1,21]),dict(base=CONTROLS[0]['input']['base'],candidate=[0,1,2.0])]:
            with self.assertRaises(ValueError):s.analyze(data)

    def test_cli_strict_atomic_and_verify(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);source=p/'input.json';dest=p/'out.json';source.write_text(json.dumps(CONTROLS[0]['input']));env=dict(os.environ,PYTHONPATH=str(ROOT))
            def run(*args):return subprocess.run([sys.executable,'-m','stnlab.insertions',*map(str,args)],env=env,cwd=d,capture_output=True,text=True)
            self.assertEqual(run(source,'--output',dest).returncode,0);self.assertEqual(run(dest,'--verify').returncode,0);original=dest.read_bytes()
            for text in ['{"base":{},"base":{},"candidate":[0,1,2]}','{"base":{"nodes":2,"edges":[]},"candidate":[0,1,2.0]}','{"base":{"nodes":2,"edges":[]},"candidate":[0,1,1e0]}','NaN',' '*65537]:
                source.write_text(text);self.assertEqual(run(source,'--output',dest).returncode,2);self.assertEqual(dest.read_bytes(),original)
