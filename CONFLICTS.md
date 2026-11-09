# Complete temporal conflicts and repairs

This inspector applies classical MUS/MCS duality to the existing bounded simple temporal network. It is not a new diagnosis algorithm. Each original edge is one independently removable inequality, including equal duplicate triples. Removing an interval represented by two directed edges is not an atomic interval operation here.

## Semantics

Input is exactly `{nodes,edges}`, using the original strict validator: 1..6 nodes, at most 12 integer `[u,v,w]` triples, valid endpoints, weights -20..20. An edge means `t[v]-t[u] <= w`. Mathematical time is real-valued and may be negative. Anchor `t0=0` only fixes common translation. Generated integer witnesses are feasible real schedules, not a discreteness assumption.

A conflict is an inclusion-minimal infeasible edge set. A repair is an inclusion-minimal removal set whose complement is feasible. Minimal means no proper subset works; minimum means smallest cardinality among all repairs. All edges are soft/removable. There are no protected observations, weighted priorities or fault models. Repairs are suggestions in a mathematical model, never account actions or permissions.

## Exact report contract

Schema `stnlab-conflicts-v1` has exactly these keys: `schema`, `input`, `consistent`, `feasible`, `conflicts`, `repairs`, `minimum_removals`, `minimum_repairs`, `unavoidable`, `hits`.

- `feasible[mask]` covers every mask 0..2^m-1. Bit i selects original edge Ci. No edge renumbering. Empty subset is feasible, including a one-node or empty-edge input.
- `conflicts` are ordered by increasing integer edge mask, not by cardinality. Each has sorted original `edges`, a `cycle:{edges,weight}` and `deletions:[{edge,schedule}]` in increasing original edge order. Every immediate deletion has a full n-node feasible schedule for only the remaining conflict edges. It need not satisfy unrelated original edges. The original negative-cycle indices follow traversal order, with lexicographically smallest cyclic rotation and then lexicographically smallest negative simple cycle selected. Every edge in a minimal conflict lies in that cycle.
- `repairs` are ordered by increasing removed mask. Each has `removed`, `kept`, a full n-node `schedule`, and `restorations:[{edge,cycle}]`. Every kept edge holds. Restoring any removed edge makes the kept network infeasible; its cycle is the same canonical original-index convention. The returned schedule necessarily violates each removed edge, since no feasible kept-system solution could satisfy one without contradicting repair minimality.
- `minimum_removals` is the smallest repair cardinality; `minimum_repairs` contains all tied sorted removal lists in repair order, not only the first. `unavoidable` is the sorted intersection of all repairs, not a claim about causal responsibility.
- `hits[repair][conflict]` is the smallest original index shared by that removal set and conflict. Every entry exists. The native verifier independently checks the complete hitting-set families in both directions, not only these witness intersections.

A consistent original network has no conflicts and exactly one repair: empty removal, all edges kept. `minimum_removals=0`, `minimum_repairs=[[]]`, `unavoidable=[]`, `hits=[[]]`. The only minimal hitting set of an empty conflict family is empty; no set hits the family containing the empty repair. These conventions make reverse duality agree without inventing an empty conflict.

## Algorithms and limits

Native generation runs full Floyd-Warshall separately for every subset, then tests immediate deletions/restorations. Monotonicity makes immediate neighbors sufficient for inclusion minimality. Bellman-Ford potentials give schedules; recursive simple-cycle enumeration gives canonical contradictions. Worst-case subset count is 4096. There is no scalability, performance superiority, causal diagnosis, execution or uncertainty claim.

The native verifier does not call generation, Floyd-Warshall, native potential construction or native cycle search. It independently enumerates original cycles by vertex permutations and parallel-edge products, derives all subset feasibility by cycle containment, enumerates all minimal hitting sets, verifies both dual directions, reconstructs potentials from independent simple paths, and strictly compares every report field and type. This is complete replay for tiny inputs, not an efficient local-certificate checker. Separate JavaScript recursively enumerates cycles and simple paths and agrees with native reports. No SAT/SMT/NetworkX dependency is used.

Seven new native tests cover all 256 two-point networks against direct anchored integer-grid feasibility (sufficient for this {-1,0,1} fixture domain), 50 seeded networks, 24 edge permutations, all ten controls, direct cycle/schedule/slack checks, all-subset completeness, independent per-subset cycle references, strict forgeries, disabled-generator replay and CLI atomic rejection. Two Node tests compare 316 reports and strict validation. Actual Chrome tests visit every conflict/deletion and repair/restoration, masks, slacks, hitting rows, schedule labels, export and stale clearing at 320, 390 and 1280 pixels. Original tests remain unchanged; test-file serialization prevents concurrent Chrome-startup contention. Installed reproduction covers all four inspector families outside checkout.

## Source ledger

1. F. Bacchus and G. Katsirelos, *Using Minimal Correction Sets to more Efficiently Compute Minimal Unsatisfiable Sets*, CAV 2015. https://gkatsi.github.io/papers/bkcav15.pdf . Primary research. Section 2 definitions of MUS/MSS/MCS and theory-parameterized duality. Its new algorithms and performance results are not implemented or claimed here.
2. A. Ignatiev, A. Previti, M. Liffiton and J. Marques-Silva, *Smallest MUS Extraction with Minimal Hitting Set Dualization*, CP 2015. https://alexeyignatiev.github.io/assets/pdf/iplms-cp15-preprint.pdf . Primary research. Preliminaries/Proposition 1 and Definition 5 distinguish subset-minimal and minimum-size hitting sets. No implicit-hitting-set solver is implemented here.
3. J. Marques-Silva, F. Heras, M. Janota, A. Previti and A. Belov, *On Computing Minimal Correction Subsets*, IJCAI 2013. https://ijcai.org/proceedings/2013/0098.pdf . Primary research. MCS/MSS definitions and correction-set context. Its CLD and relaxation-search algorithms are not used.
4. N. Roos and C. Witteveen, *Diagnosis of Simple Temporal Networks*, ECAI 2008. https://dke.maastrichtuniversity.nl/nico.roos/wp-content/uploads/2015/04/RW08ECAI.pdf . Primary temporal-diagnosis research. Preliminaries and qualifications explain feasibility, negative cycles and constraint removal. Context only: this inspector does not implement their observations, abnormality/fault modes, temporal assumptions or maximum-confirmation diagnosis. Unlike that planning model, negative times are allowed here.
5. P. Indyk, MIT 6.006 Lecture 17, *Solving a system of difference constraints*, 2011. https://courses.csail.mit.edu/6.006/spring11/lectures/lec17.pdf . University teaching source. Negative cycles telescope to contradictions; super-source shortest paths supply feasible potentials.
6. NetworkX official `negative_edge_cycle` documentation. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.negative_edge_cycle.html . Official implementation documentation. Negative cycles anywhere in disconnected graphs, using a super-source. Not a dependency or independent endorsement of this implementation.

All six sources fetched and governing portions inspected. Original synthetic controls, interface, implementation and tests. Diagnoselab covers the Boolean CNF counterpart elsewhere in this portfolio; this feature adds integrated temporal witnesses, not another copy of that project. No private records, paid APIs or real calendar changes.
