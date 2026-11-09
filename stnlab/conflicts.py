"""All inclusion-minimal temporal conflicts and correction sets, bounded exhaustive search."""
from . import validate,floyd,potential,negative_cycle

def analyze(raw):
    data=validate(raw);n=data['nodes'];es=data['edges'];m=len(es);full=(1<<m)-1
    ids=lambda mask:[i for i in range(m) if mask>>i&1]
    subset=lambda mask:[es[i] for i in ids(mask)]
    feasible=[]
    for mask in range(full+1):
        d=floyd(n,subset(mask));feasible.append(not any(d[i][i]<0 for i in range(n)))
    def cycle(mask):
        ix=ids(mask);c=negative_cycle(n,subset(mask));return dict(edges=[ix[i] for i in c['edges']],weight=c['weight'])
    mus=[x for x in range(full+1) if not feasible[x] and all(feasible[x^(1<<i)] for i in ids(x))]
    repairs=[x for x in range(full+1) if feasible[full^x] and all(not feasible[(full^x)|(1<<i)] for i in ids(x))]
    conflicts=[dict(edges=ids(x),cycle=cycle(x),deletions=[dict(edge=i,schedule=potential(n,subset(x^(1<<i)))) for i in ids(x)]) for x in mus]
    corrected=[dict(removed=ids(x),kept=ids(full^x),schedule=potential(n,subset(full^x)),restorations=[dict(edge=i,cycle=cycle((full^x)|(1<<i))) for i in ids(x)]) for x in repairs]
    minimum=min(map(int.bit_count,repairs))
    return dict(schema='stnlab-conflicts-v1',input=data,consistent=feasible[full],feasible=feasible,conflicts=conflicts,repairs=corrected,minimum_removals=minimum,minimum_repairs=[ids(x) for x in repairs if x.bit_count()==minimum],unavoidable=[i for i in range(m) if all(x>>i&1 for x in repairs)],hits=[[min(set(ids(x))&set(ids(y))) for y in mus] for x in repairs])

def verify(report):
    from . import oracle
    if type(report) is not dict or 'input' not in report:raise ValueError('Invalid conflict report')
    data=validate(report['input']);n=data['nodes'];es=data['edges'];m=len(es);full=(1<<m)-1
    # Enumerate complete original simple cycles once. A subset is inconsistent iff it contains one.
    bad=oracle.cycles(n,es);masks=[sum(1<<i for i in row) for row in bad]
    ids=lambda x:[i for i in range(m) if x>>i&1]
    edges=lambda x:[es[i] for i in ids(x)]
    sat=[not any(x&b==b for b in masks) for x in range(full+1)]
    # Independent minimal hitting-set construction for all corrections, not generator subset tests.
    cores=[x for x in range(full+1) if not sat[x] and not any(not sat[y] for y in range(x) if y&x==y)]
    hitting=[all(x&y for y in cores) for x in range(full+1)]
    repairs=[x for x in range(full+1) if hitting[x] and not any(hitting[y] for y in range(x) if y&x==y)]
    if any(hitting[x]!=sat[full^x] for x in range(full+1)):raise ValueError('Duality mismatch')
    def cyc(x):
        row=next(row for row,mask in zip(bad,masks) if mask&x==mask)
        return dict(edges=list(row),weight=sum(es[i][2] for i in row))
    expected=dict(schema='stnlab-conflicts-v1',input=data,consistent=sat[full],feasible=sat,conflicts=[dict(edges=ids(x),cycle=cyc(x),deletions=[dict(edge=i,schedule=oracle.schedule(n,edges(x^(1<<i)))) for i in ids(x)])for x in cores],repairs=[dict(removed=ids(x),kept=ids(full^x),schedule=oracle.schedule(n,edges(full^x)),restorations=[dict(edge=i,cycle=cyc((full^x)|(1<<i)))for i in ids(x)])for x in repairs],minimum_removals=min(len(ids(x))for x in repairs),minimum_repairs=[],unavoidable=[i for i in range(m)if all(x>>i&1 for x in repairs)],hits=[[min(set(ids(x))&set(ids(y)))for y in cores]for x in repairs])
    expected['minimum_repairs']=[ids(x)for x in repairs if len(ids(x))==expected['minimum_removals']]
    # Dual direction: all conflicts are minimal hitting sets of all repairs, including empty-family conventions.
    dual=[x for x in range(full+1)if all(x&y for y in repairs)]
    if cores!=[x for x in dual if not any(y!=x and y&x==y for y in dual)]:raise ValueError('Reverse duality mismatch')
    def equal(a,b):
        if type(a)is not type(b):return False
        if type(a)is dict:return set(a)==set(b)and all(equal(a[k],b[k])for k in a)
        if type(a)is list:return len(a)==len(b)and all(equal(x,y)for x,y in zip(a,b))
        return a==b
    if not equal(report,expected):raise ValueError('Conflict report disagrees with independent cycle/hitting-set replay')
    return True

def main():
    from .__main__ import main as cli
    return cli(analyze,verify,'stnlab-conflicts-v1')
if __name__=='__main__':raise SystemExit(main())
