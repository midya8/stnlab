"""Exact existential STN projection, not induced-subgraph deletion."""
from . import validate as validate_base, floyd, potential, canonical_path, negative_cycle

def validate(raw):
    if type(raw) is not dict or set(raw)!={'base','keep','values'}:raise ValueError('Expected exactly base, keep and values')
    base=validate_base(raw['base']);keep=raw['keep'];values=raw['values']
    if type(keep) is not list or not keep or any(type(i) is not int for i in keep) or keep!=sorted(set(keep)) or keep[0]!=0 or keep[-1]>=base['nodes']:raise ValueError('keep must be sorted unique valid nodes including anchor 0')
    if type(values) is not list or len(values)!=len(keep) or any(type(x) is not int or not -100<=x<=100 for x in values) or values[0]!=0:raise ValueError('values must match keep, integers -100..100, anchor value 0')
    return dict(base=base,keep=keep[:],values=values[:])

def _build(data,closure,solve,path,cycle):
    base=data['base'];n=base['nodes'];es=base['edges'];keep=data['keep'];values=data['values'];d=closure(n,es);bad=cycle(n,es)
    r=dict(schema='stnlab-projection-v1',input=data,consistent=bad is None,negative_cycle=bad,matrix=None,projected_edges=[],schedule=None,pairs=[],naive_matrix=None,naive_equivalent=False,lost=[],query=dict(accepted=False,violation=None,extension=None))
    if bad is not None:return r
    r['matrix']=[[d[u][v] for v in keep] for u in keep];r['schedule']=solve(n,es)
    r['projected_edges']=[[u,v,d[u][v]] for u in keep for v in keep if u!=v and d[u][v] is not None]
    induced=[e for e in es if e[0] in keep and e[1] in keep];naive=closure(n,induced);r['naive_matrix']=[[naive[u][v] for v in keep] for u in keep]
    for u in keep:
        for v in keep:
            w=d[u][v];p=None if w is None else path(n,es,u,v,w)
            r['pairs'].append(dict(u=u,v=v,bound=w,path=p,schedule=None if w is None else solve(n,es+[[v,u,-w]]),ray=None if w is not None else [int(d[u][j] is None)-int(d[u][0] is None) for j in range(n)]))
            if w is not None and (naive[u][v] is None or w<naive[u][v]):
                t=solve(n,induced+[[v,u,-w-1]])
                r['lost'].append(dict(u=u,v=v,bound=w,naive_bound=naive[u][v],path=p,values=[t[i] for i in keep],actual=t[v]-t[u]))
    r['naive_equivalent']=not r['lost'];fixed=dict(zip(keep,values))
    violated=next((p for p in r['pairs'] if p['bound'] is not None and fixed[p['v']]-fixed[p['u']]>p['bound']),None)
    if violated:
        u,v,w=violated['u'],violated['v'],violated['bound'];r['query']['violation']=dict(u=u,v=v,bound=w,path=violated['path'],actual=fixed[v]-fixed[u],cycle_weight=w+fixed[u]-fixed[v])
    else:
        pins=[[a,b,w] for i,x in zip(keep,values) for a,b,w in [(0,i,x),(i,0,-x)]]
        r['query']=dict(accepted=True,violation=None,extension=solve(n,es+pins))
    return r

def analyze(raw):
    data=validate(raw)
    def cycle(n,es):
        d=floyd(n,es)
        return negative_cycle(n,es) if any(d[i][i]<0 for i in range(n)) else None
    return _build(data,floyd,potential,canonical_path,cycle)

def verify(report):
    # Separate oracle reconstructs closure, paths, cycles and potentials by permutations.
    from . import oracle
    if type(report) is not dict or 'input' not in report:raise ValueError('Invalid projection report')
    data=validate(report['input']);es=data['base']['edges'];n=data['base']['nodes'];keep=data['keep'];vals=data['values'];bad=oracle.cycles(n,es)
    r=dict(schema='stnlab-projection-v1',input=data,consistent=not bad,negative_cycle=None,matrix=None,projected_edges=[],schedule=None,pairs=[],naive_matrix=None,naive_equivalent=False,lost=[],query=dict(accepted=False,violation=None,extension=None))
    if bad:r['negative_cycle']=dict(edges=list(bad[0]),weight=sum(es[i][2] for i in bad[0]))
    else:
        d,p=oracle.paths(n,es);induced=[e for e in es if e[0] in keep and e[1] in keep];nd,_=oracle.paths(n,induced)
        r['matrix']=[[d[u][v] for v in keep] for u in keep];r['naive_matrix']=[[nd[u][v] for v in keep] for u in keep];r['schedule']=oracle.schedule(n,es)
        r['projected_edges']=[[u,v,d[u][v]] for u in keep for v in keep if u!=v and d[u][v] is not None]
        for u in keep:
            for v in keep:
                w=d[u][v];r['pairs'].append(dict(u=u,v=v,bound=w,path=p[u][v],schedule=None if w is None else oracle.schedule(n,es+[[v,u,-w]]),ray=None if w is not None else [int(d[u][j] is None)-int(d[u][0] is None) for j in range(n)]))
                if w is not None and nd[u][v]!=w:
                    t=oracle.schedule(n,induced+[[v,u,-w-1]]);r['lost'].append(dict(u=u,v=v,bound=w,naive_bound=nd[u][v],path=p[u][v],values=[t[i] for i in keep],actual=t[v]-t[u]))
        r['naive_equivalent']=not r['lost'];fixed=dict(zip(keep,vals))
        failures=[q for q in r['pairs'] if q['bound'] is not None and fixed[q['v']]-fixed[q['u']]>q['bound']]
        pins=sum(([[0,i,x],[i,0,-x]] for i,x in zip(keep,vals)),[])
        actual_bad=oracle.cycles(n,es+pins)
        if bool(actual_bad)!=bool(failures):raise ValueError('Projection and pinned feasibility disagree')
        if failures:
            q=failures[0];u,v,w=q['u'],q['v'],q['bound'];r['query']['violation']=dict(u=u,v=v,bound=w,path=p[u][v],actual=fixed[v]-fixed[u],cycle_weight=sum(es[i][2] for i in p[u][v])+fixed[u]-fixed[v])
        else:r['query']=dict(accepted=True,violation=None,extension=oracle.schedule(n,es+pins))
    def equal(a,b):
        if type(a) is not type(b):return False
        if type(a) is dict:return set(a)==set(b) and all(equal(a[k],b[k]) for k in a)
        if type(a) is list:return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
        return a==b
    if not equal(report,r):raise ValueError('Projection disagrees with independent permutation replay')
    return True

def main():
    from .__main__ import main as cli
    return cli(analyze,verify,'stnlab-projection-v1')
if __name__=='__main__':raise SystemExit(main())
