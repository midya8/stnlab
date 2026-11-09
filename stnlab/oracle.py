"""Independent permutation/edge-product references. Never calls generator routines."""
from itertools import permutations,product

def paths(n,edges):
    d=[[None]*n for _ in range(n)];best=[[None]*n for _ in range(n)]
    for start in range(n):
        d[start][start]=0;best[start][start]=[]
        other=[i for i in range(n) if i!=start]
        for length in range(1,n):
            for tail in permutations(other,length):
                vertices=(start,)+tail;options=[[k for k,e in enumerate(edges) if e[:2]==[a,b]] for a,b in zip(vertices,vertices[1:])]
                for ids in product(*options):
                    weight=sum(edges[k][2] for k in ids);v=tail[-1];ids=list(ids)
                    if d[start][v] is None or (weight,ids)<(d[start][v],best[start][v]):d[start][v]=weight;best[start][v]=ids
    return d,best

def cycles(n,edges):
    out=set()
    for size in range(1,n+1):
        for nodes in permutations(range(n),size):
            if nodes[0]!=min(nodes):continue
            options=[[k for k,e in enumerate(edges) if e[:2]==[a,b]] for a,b in zip(nodes,nodes[1:]+nodes[:1])]
            for ids in product(*options):
                if sum(edges[k][2] for k in ids)<0:out.add(min(ids[i:]+ids[:i] for i in range(size)))
    return sorted(out)

def schedule(n,edges):
    d,_=paths(n,edges);p=[min([0]+[d[u][v] for u in range(n) if d[u][v] is not None]) for v in range(n)]
    return [x-p[0] for x in p]

def replay(data):
    n=data['nodes'];edges=data['edges'];bad=cycles(n,edges)
    r=dict(schema='stnlab-v1',input=data,consistent=not bad,schedule=None,matrix=None,pairs=[],removals=[],negative_cycle=None)
    if bad:r['negative_cycle']=dict(edges=list(bad[0]),weight=sum(edges[k][2] for k in bad[0]));return r
    d,p=paths(n,edges);r['schedule']=schedule(n,edges);r['matrix']=d
    for u in range(n):
        for v in range(n):
            w=d[u][v];ray=None
            if w is None:
                ray=[int(d[u][j] is None)-int(d[u][0] is None) for j in range(n)]
            r['pairs'].append(dict(u=u,v=v,bound=w,path=p[u][v],schedule=schedule(n,edges+[[v,u,-w]]) if w is not None else None,ray=ray))
    for k,(u,v,w) in enumerate(edges):
        remaining=[e for j,e in enumerate(edges) if j!=k];q,b=paths(n,remaining);bound=q[u][v];red=bound is not None and bound<=w
        r['removals'].append(dict(edge=k,redundant=red,bound_without=bound,path=[j if j<k else j+1 for j in b[u][v]] if red else None,counterexample=None if red else schedule(n,remaining+[[v,u,-w-1]])))
    return r
