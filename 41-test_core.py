import copy,itertools,json,os,pathlib,random,subprocess,sys,tempfile,unittest
from unittest.mock import patch
from stnlab import analyze,verify,validate
ROOT=pathlib.Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/controls.json').read_text())

def fixtures():
    out=[c['input'] for c in CONTROLS]
    for choices in itertools.product([None,-1,0,1],repeat=4):out.append(dict(nodes=2,edges=[[u,v,w] for (u,v),w in zip(itertools.product(range(2),repeat=2),choices) if w is not None]))
    rng=random.Random(93481)
    for _ in range(100):
        n=rng.randint(1,5);out.append(dict(nodes=n,edges=[[rng.randrange(n),rng.randrange(n),rng.randint(-5,6)] for _ in range(rng.randrange(9))]))
    return out

def feasible(edges,t):return all(t[v]-t[u]<=w for u,v,w in edges)

def audit(r):
    n=r['input']['nodes'];edges=r['input']['edges']
    if not r['consistent']:
        ids=r['negative_cycle']['edges'];assert ids and len(set(ids))==len(ids)
        selected=[edges[i] for i in ids];assert all(a[1]==b[0] for a,b in zip(selected,selected[1:]+selected[:1]));assert sum(e[2] for e in selected)==r['negative_cycle']['weight']<0
        assert len({e[0] for e in selected})==len(selected);return
    assert r['schedule'][0]==0 and feasible(edges,r['schedule'])
    for row in r['pairs']:
        u,v,w=row['u'],row['v'],row['bound'];assert r['matrix'][u][v]==w
        if w is None:
            h=row['ray'];assert h[0]==0 and h[v]-h[u]==1;assert all(h[b]-h[a]<=0 for a,b,_ in edges)
            for k in [0,1,1000]:assert feasible(edges,[a+k*b for a,b in zip(r['schedule'],h)])
        else:
            t=row['schedule'];assert t[0]==0 and feasible(edges,t) and t[v]-t[u]==w
            ids=row['path'];at=u;weight=0;seen={u}
            for k in ids:
                a,b,c=edges[k];assert a==at and b not in seen;seen.add(b);at=b;weight+=c
            assert at==v and weight==w
    for row in r['removals']:
        k=row['edge'];remaining=[e for j,e in enumerate(edges) if j!=k];u,v,w=edges[k]
        if row['redundant']:
            ids=row['path'];at=u;weight=0
            for j in ids:assert j!=k;assert edges[j][0]==at;at=edges[j][1];weight+=edges[j][2]
            assert at==v and weight==row['bound_without']<=w
        else:assert feasible(remaining,row['counterexample']) and row['counterexample'][v]-row['counterexample'][u]>=w+1

class CoreTests(unittest.TestCase):
    def test_controls(self):
        for c in CONTROLS:r=analyze(c['input']);self.assertTrue(verify(r));audit(r)
        r=analyze(CONTROLS[0]['input']);self.assertEqual(r['matrix'][0][2],7);self.assertEqual(r['pairs'][2]['path'],[1,2]);self.assertTrue(r['removals'][0]['redundant'])
        r=analyze(CONTROLS[3]['input']);self.assertTrue(all(q['redundant'] for q in r['removals']))
    def test_exhaustive_and_seeded(self):
        for x in fixtures():r=analyze(x);self.assertTrue(verify(r));audit(r)
    def test_integer_enumeration_reference(self):
        # For these bounded two-node inputs, fixing t0=0 and scanning -4..4
        # independently checks feasibility and every finite attainable bound.
        for x in fixtures()[len(CONTROLS):len(CONTROLS)+256]:
            r=analyze(x);solutions=[[0,t] for t in range(-4,5) if feasible(x['edges'],[0,t])]
            self.assertEqual(bool(solutions),r['consistent'])
            if r['consistent']:
                for q in r['pairs']:
                    if q['bound'] is not None:self.assertEqual(max(t[q['v']]-t[q['u']] for t in solutions),q['bound'])
    def test_all_three_node_directed_graphs(self):
        arcs=[(u,v) for u in range(3) for v in range(3) if u!=v]
        for choices in itertools.product([None,-1,0,1],repeat=6):
            x=dict(nodes=3,edges=[[u,v,w] for (u,v),w in zip(arcs,choices) if w is not None]);r=analyze(x);self.assertTrue(verify(r));audit(r)
            solutions=[[0,a,b] for a,b in itertools.product(range(-4,5),repeat=2) if feasible(x['edges'],[0,a,b])]
            self.assertEqual(bool(solutions),r['consistent'])
            if r['consistent']:
                for q in r['pairs']:
                    if q['bound'] is not None:self.assertEqual(max(t[q['v']]-t[q['u']] for t in solutions),q['bound'])
    def test_node_and_edge_relabeling(self):
        x=CONTROLS[0]['input'];r=analyze(x)
        for p in itertools.permutations(range(3)):
            y=dict(nodes=3,edges=[[p[u],p[v],w] for u,v,w in x['edges']]);s=analyze(y);self.assertTrue(verify(s));audit(s)
            for u in range(3):
                for v in range(3):self.assertEqual(r['matrix'][u][v],s['matrix'][p[u]][p[v]])
        for order in itertools.permutations(range(5)):
            s=analyze(dict(nodes=3,edges=[x['edges'][j] for j in order]));self.assertTrue(verify(s));self.assertEqual(r['matrix'],s['matrix']);audit(s)
    def test_independent_checker(self):
        reports=[analyze(c['input']) for c in CONTROLS]
        with patch('stnlab.analyze',side_effect=AssertionError),patch('stnlab.floyd',side_effect=AssertionError),patch('stnlab.potential',side_effect=AssertionError),patch('stnlab.canonical_path',side_effect=AssertionError),patch('stnlab.negative_cycle',side_effect=AssertionError):
            for r in reports:self.assertTrue(verify(r))
    def test_strict_forgeries(self):
        reports=[analyze(c['input']) for c in CONTROLS];bad=[]
        r=reports[0]
        for edit in [lambda q:q.update(extra=0),lambda q:q['matrix'][0].__setitem__(2,8),lambda q:q['schedule'].__setitem__(0,True),lambda q:q['pairs'][2]['path'].reverse(),lambda q:q['pairs'][2]['schedule'].__setitem__(2,99),lambda q:q['removals'][0].update(redundant=1),lambda q:q['removals'][1]['counterexample'].__setitem__(0,8),lambda q:q['pairs'].reverse()]:
            q=copy.deepcopy(r);edit(q);bad.append(q)
        q=copy.deepcopy(reports[1]);q['negative_cycle']['weight']=0;bad.append(q)
        q=copy.deepcopy(reports[2]);next(q for q in q['pairs'] if q['ray'])['ray']=[0]*4;bad.append(q)
        for q in bad:
            with self.assertRaises(ValueError):verify(q)
    def test_invalid(self):
        for x in [None,{},dict(nodes=0,edges=[]),dict(nodes=True,edges=[]),dict(nodes=7,edges=[]),dict(nodes=2,edges=[[0,2,0]]),dict(nodes=2,edges=[[0,1,21]]),dict(nodes=2,edges=[[0,1,0.0]]),dict(nodes=2,edges=[[0,1,False]]),dict(nodes=2,edges=[[0,1,0]]*13),dict(nodes=2,edges=(),other=0)]:
            with self.assertRaises(ValueError):analyze(x)
    def test_cli_strict_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=pathlib.Path(tmp)/'report.json';out.write_text('keep')
            for text in ['{"nodes":2,"nodes":2,"edges":[]}','{"nodes":2,"edges":[[0,1,1e0]]}','{"nodes":NaN,"edges":[]}', '{}','['*2000,' '*65537]:
                p=subprocess.run([sys.executable,'-m','stnlab','-','--output',str(out)],input=text,text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),'keep');self.assertEqual(p.stdout,'')
            text=json.dumps(CONTROLS[0]['input']);p=subprocess.run([sys.executable,'-m','stnlab','-','--output',str(out)],input=text,text=True,capture_output=True);self.assertEqual(p.returncode,0);self.assertTrue(verify(json.loads(out.read_text())))
            p=subprocess.run([sys.executable,'-m','stnlab',str(out),'--verify'],capture_output=True,text=True);self.assertEqual(json.loads(p.stdout),{'valid':True,'schema':'stnlab-v1'})
            self.assertEqual(sorted(p.name for p in pathlib.Path(tmp).iterdir()),['report.json'])
if __name__=='__main__':unittest.main()
