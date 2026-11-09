"""One-edge STN closure update, with full independent recomputation verification."""
from . import validate as validate_base, floyd, potential, canonical_path, negative_cycle

def validate(raw):
    if type(raw) is not dict or set(raw)!={'base','candidate'}:raise ValueError('Expected exactly base and candidate')
    base=validate_base(raw['base']);candidate=raw['candidate']
    validate_base(dict(nodes=base['nodes'],edges=[candidate]))
    return dict(base=base,candidate=candidate[:])

def analyze(raw):
    data=validate(raw);base=data['base'];n=base['nodes'];edges=base['edges'];a,b,w=data['candidate'];k=len(edges);d=floyd(n,edges)
    r=dict(schema='stnlab-insertions-v1',input=data,base_consistent=not any(d[i][i]<0 for i in range(n)),base_matrix=None,base_schedule=None,base_cycle=None,threshold=None,classification='base-inconsistent',consistent=False,matrix=None,schedule=None,cycle=None,cells=[],spectrum=[])
    if not r['base_consistent']:r['base_cycle']=negative_cycle(n,edges);r['cycle']=r['base_cycle'];return r
    r['base_matrix']=d;r['base_schedule']=potential(n,edges);back=d[b][a];lower=None if back is None else -back;upper=d[a][b]
    path=None if back is None else canonical_path(n,edges,b,a,back)
    r['threshold']=dict(lower=lower,redundant_at=upper,return_path=path,boundary_schedule=None if lower is None else potential(n,edges+[[a,b,lower]]),below_cycle=None if lower is None else dict(candidate_weight=lower-1,edges=[k]+path,weight=-1))
    for x in range(-20,21):
        cls='inconsistent' if lower is not None and x<lower else 'redundant' if upper is not None and x>=upper else 'tightening'
        changed=None if cls=='inconsistent' else sum(d[i][a] is not None and d[b][j] is not None and (d[i][j] is None or d[i][a]+x+d[b][j]<d[i][j]) for i in range(n) for j in range(n))
        r['spectrum'].append(dict(weight=x,classification=cls,changed=changed))
    r['classification']=r['spectrum'][w+20]['classification'];r['consistent']=r['classification']!='inconsistent';aug=edges+[[a,b,w]]
    if not r['consistent']:r['cycle']=dict(edges=[k]+path,weight=w+back);return r
    updated=[[d[i][j] for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            via=None if d[i][a] is None or d[b][j] is None else d[i][a]+w+d[b][j]
            if via is not None and (updated[i][j] is None or via<updated[i][j]):updated[i][j]=via
    r['matrix']=updated;r['schedule']=potential(n,aug)
    for i in range(n):
        for j in range(n):
            v=updated[i][j];via=None if d[i][a] is None or d[b][j] is None else d[i][a]+w+d[b][j]
            ray=None if v is not None else [int(updated[i][z] is None)-int(updated[i][0] is None) for z in range(n)]
            r['cells'].append(dict(u=i,v=j,before=d[i][j],via=via,left_path=None if d[i][a] is None else canonical_path(n,edges,i,a,d[i][a]),right_path=None if d[b][j] is None else canonical_path(n,edges,b,j,d[b][j]),after=v,changed=v!=d[i][j],path=None if v is None else canonical_path(n,aug,i,j,v),schedule=None if v is None else potential(n,aug+[[j,i,-v]]),ray=ray))
    return r

def verify(report):
    from . import oracle
    if type(report) is not dict or 'input' not in report:raise ValueError('Invalid insertion report')
    data=validate(report['input']);base=data['base'];n=base['nodes'];edges=base['edges'];a,b,w=data['candidate'];k=len(edges);bad=oracle.cycles(n,edges)
    r=dict(schema='stnlab-insertions-v1',input=data,base_consistent=not bad,base_matrix=None,base_schedule=None,base_cycle=None,threshold=None,classification='base-inconsistent',consistent=False,matrix=None,schedule=None,cycle=None,cells=[],spectrum=[])
    if bad:r['base_cycle']=dict(edges=list(bad[0]),weight=sum(edges[i][2] for i in bad[0]));r['cycle']=r['base_cycle']
    else:
        d,p=oracle.paths(n,edges);r['base_matrix']=d;r['base_schedule']=oracle.schedule(n,edges);back=d[b][a];lower=None if back is None else -back;upper=d[a][b]
        r['threshold']=dict(lower=lower,redundant_at=upper,return_path=p[b][a],boundary_schedule=None if lower is None else oracle.schedule(n,edges+[[a,b,lower]]),below_cycle=None if lower is None else dict(candidate_weight=lower-1,edges=[k]+p[b][a],weight=-1))
        for x in range(-20,21):
            es=edges+[[a,b,x]];bad_new=oracle.cycles(n,es);q,_=oracle.paths(n,es) if not bad_new else (None,None)
            cls='inconsistent' if bad_new else 'redundant' if q==d else 'tightening'
            r['spectrum'].append(dict(weight=x,classification=cls,changed=None if q is None else sum(q[i][j]!=d[i][j] for i in range(n) for j in range(n))))
        r['classification']=r['spectrum'][w+20]['classification'];r['consistent']=r['classification']!='inconsistent';aug=edges+[[a,b,w]]
        if not r['consistent']:r['cycle']=dict(edges=[k]+p[b][a],weight=w+back)
        else:
            q,paths=oracle.paths(n,aug);r['matrix']=q;r['schedule']=oracle.schedule(n,aug)
            for i in range(n):
                for j in range(n):
                    v=q[i][j];left=p[i][a];right=p[b][j];via=None if left is None or right is None else sum(edges[z][2] for z in left+right)+w
                    ray=None if v is not None else [int(q[i][z] is None)-int(q[i][0] is None) for z in range(n)]
                    r['cells'].append(dict(u=i,v=j,before=d[i][j],via=via,left_path=left,right_path=right,after=v,changed=v!=d[i][j],path=paths[i][j],schedule=None if v is None else oracle.schedule(n,aug+[[j,i,-v]]),ray=ray))
    def equal(x,y):
        if type(x) is not type(y):return False
        if type(x) is dict:return set(x)==set(y) and all(equal(x[z],y[z]) for z in x)
        if type(x) is list:return len(x)==len(y) and all(equal(a,b) for a,b in zip(x,y))
        return x==y
    if not equal(report,r):raise ValueError('Insertion report disagrees with independent full recomputation')
    return True

def main():
    from .__main__ import main as cli
    return cli(analyze,verify,'stnlab-insertions-v1')

if __name__=='__main__':raise SystemExit(main())
