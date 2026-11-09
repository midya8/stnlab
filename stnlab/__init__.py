"""Exact tiny simple temporal networks. Constraints are t[v]-t[u] <= w."""

def validate(raw):
    if type(raw) is not dict or set(raw)!={'nodes','edges'}:raise ValueError('Expected exactly nodes and edges')
    n=raw['nodes'];edges=raw['edges']
    if type(n) is not int or not 1<=n<=6:raise ValueError('nodes must be an integer from 1 to 6')
    if type(edges) is not list or len(edges)>12:raise ValueError('edges must be a list of at most 12 triples')
    for e in edges:
        if type(e) is not list or len(e)!=3 or any(type(x) is not int for x in e):raise ValueError('Each edge is an integer [u,v,w] triple')
        if not 0<=e[0]<n or not 0<=e[1]<n or not -20<=e[2]<=20:raise ValueError('Endpoint out of range or weight outside -20..20')
    return dict(nodes=n,edges=[e[:] for e in edges])


def floyd(n,edges):
    d=[[0 if u==v else None for v in range(n)] for u in range(n)]
    for u,v,w in edges:
        if d[u][v] is None or w<d[u][v]:d[u][v]=w
    for k in range(n):
        previous=[r[:] for r in d]
        for u in range(n):
            for v in range(n):
                a,b=previous[u][k],previous[k][v]
                if a is not None and b is not None and (d[u][v] is None or a+b<d[u][v]):d[u][v]=a+b
    return d


def potential(n,edges):
    # Synchronous Bellman-Ford from an implicit zero-weight super-source.
    p=[0]*n
    for _ in range(n-1):
        old=p[:]
        for u,v,w in edges:p[v]=min(p[v],old[u]+w)
    if any(p[v]>p[u]+w for u,v,w in edges):raise ValueError('No feasible potential')
    return [x-p[0] for x in p]


def canonical_path(n,edges,u,v,bound):
    if u==v:return []
    def walk(at,seen,ids,total):
        for k,(a,b,w) in enumerate(edges):
            if a!=at or b in seen:continue
            if b==v and total+w==bound:return ids+[k]
            if b!=v:
                result=walk(b,seen|{b},ids+[k],total+w)
                if result is not None:return result
        return None
    result=walk(u,{u},[],0)
    if result is None:raise ValueError('Missing shortest path')
    return result


def negative_cycle(n,edges):
    cycles=set()
    def walk(start,at,seen,ids,total):
        for k,(u,v,w) in enumerate(edges):
            if u!=at:continue
            if v==start and total+w<0:
                row=ids+[k];cycles.add(min(tuple(row[i:]+row[:i]) for i in range(len(row))))
            elif v not in seen:walk(start,v,seen|{v},ids+[k],total+w)
    for start in range(n):walk(start,start,{start},[],0)
    ids=list(min(cycles));return dict(edges=ids,weight=sum(edges[k][2] for k in ids))


def analyze(raw):
    data=validate(raw);n=data['nodes'];edges=data['edges'];d=floyd(n,edges)
    report=dict(schema='stnlab-v1',input=data,consistent=not any(d[i][i]<0 for i in range(n)),schedule=None,matrix=None,pairs=[],removals=[],negative_cycle=None)
    if not report['consistent']:
        report['negative_cycle']=negative_cycle(n,edges);return report
    report['schedule']=potential(n,edges);report['matrix']=d
    for u in range(n):
        for v in range(n):
            w=d[u][v]
            if w is None:
                ray=[int(d[u][j] is None) for j in range(n)];ray=[x-ray[0] for x in ray]
                report['pairs'].append(dict(u=u,v=v,bound=None,path=None,schedule=None,ray=ray))
            else:report['pairs'].append(dict(u=u,v=v,bound=w,path=canonical_path(n,edges,u,v,w),schedule=potential(n,edges+[[v,u,-w]]),ray=None))
    for k,(u,v,w) in enumerate(edges):
        remaining=edges[:k]+edges[k+1:];r=floyd(n,remaining)[u][v];redundant=r is not None and r<=w
        path=canonical_path(n,remaining,u,v,r) if redundant else None
        if path is not None:path=[i if i<k else i+1 for i in path]
        report['removals'].append(dict(edge=k,redundant=redundant,bound_without=r,path=path,counterexample=None if redundant else potential(n,remaining+[[v,u,-w-1]])))
    return report


def verify(report):
    from .oracle import replay
    if type(report) is not dict or 'input' not in report:raise ValueError('Invalid report shape')
    expected=replay(validate(report['input']))
    def equal(a,b):
        if type(a) is not type(b):return False
        if type(a) is dict:return set(a)==set(b) and all(equal(a[k],b[k]) for k in a)
        if type(a) is list:return len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
        return a==b
    if not equal(report,expected):raise ValueError('Report disagrees with independent path/cycle enumeration')
    return True
