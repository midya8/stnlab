# One-edge insertion: exact closure sensitivity

## Contract

Input is exactly `{base: {nodes, edges}, candidate: [u,v,w]}`. Base validation is unchanged: 1-6 points, at most 12 directed edges, integer weights -20..20. Candidate uses the same endpoint/weight rules and is a separate thirteenth edge when the base is full. Its original index is k=len(base.edges). Parallel edges and self-loops are retained. Times are real-valued; t0=0 removes only shared translation.

Schema `stnlab-insertions-v1`. An inconsistent base returns `base_consistent=false`, its canonical pre-existing negative cycle, classification `base-inconsistent`, no threshold, no spectrum and no post-insertion matrix/schedule/cells. Adding an inequality cannot enlarge an empty feasible set. An isolated anchor does not hide another component's conflict.

For a consistent base, D is its original shortest-bound matrix. Let the proposed edge be a→b of weight w. A new cycle can exist only by traversing the new edge and an old return walk b→a. Its minimum cycle weight is w+D[b,a]. Thus the exact feasible interval is w≥-D[b,a] when the old return bound is finite, and all real weights when it is infinite. The threshold record gives this lower bound (null means no finite lower threshold), its original-index shortest return path, a complete anchored schedule at the finite boundary, and an explicit cycle of weight -1 at boundary-1. Boundary and below-boundary certificate weights are internal and may exceed the public input window. The boundary schedule proves attainability, not merely a necessary cycle condition.

The redundant-at threshold is D[a,b], or null when no finite weight is redundant. Consistent insertion is redundant exactly when w≥D[a,b]. Equality with the lower threshold is feasible, often creating a zero cycle. If lower and redundant-at coincide there may be no tightening region. A zero self-loop uses the empty return path and is redundant; a negative self-loop is inconsistent.

Classification is `inconsistent`, `redundant` or `tightening` for a consistent base. In the inconsistent case, the candidate followed by the selected old shortest return path is the cycle witness, in directed order. It need not be the globally lexicographically first negative cycle, the most-negative cycle or a minimum-cardinality cycle. No post-insertion distance matrix is reported for an empty feasible set.

## Immutable one-edge update

When consistent, for every ordered pair i,j:

`D'[i,j] = min(D[i,j], D[i,a] + w + D[b,j])`.

Every right-hand D is from the immutable old matrix. Missing paths are explicit null infinity, never finite sentinels. Any shortest walk using the new edge more than once contains a nonnegative cycle, which can be removed without increasing its weight. Therefore a shortest representative either avoids the new edge or uses it once, proving the two-term update. A finite via term is accompanied by the two canonical old paths. Their concatenation with the candidate is a directed walk, not necessarily a simple shortest path, especially for unchanged entries. Ties do not count as changed, though witnesses can change.

Each row-major cell record contains u,v,before,via,left_path,right_path,after,changed,path,schedule,ray. It includes both the old via decomposition and a separate canonical post-insertion shortest simple path. Finite post bounds have complete anchored attaining schedules; unbounded post bounds have an anchored ray satisfying all old and candidate edges with nonpositive slope while the selected difference grows by one. A complete common post-insertion base schedule is also returned. Path lexicographic tie rules and schedule normalization follow the original METHOD.md contract. Individual bounds can have different attaining schedules; arbitrary endpoints are not jointly selectable.

The spectrum contains exactly 41 alternatives with fixed endpoints and weights -20..20, in ascending order. Each has weight,classification,changed. Inconsistent alternatives have changed=null, not zero. Alternatives do not accumulate. The real threshold may lie outside this finite integer sample. Changed is the exact number of matrix entries that differ from the original matrix, including newly finite entries. This is not an execution-time, accuracy or causal benchmark.

## Independent implementations

Native generation calls the original Floyd-Warshall once on the base and updates all distances using the stated immutable formula, without full closure recomputation for the candidate or spectrum. It reuses original Bellman-Ford and path/cycle helpers only for evidence construction. A test counts the closure calls. The independent native checker uses the original permutation/edge-product oracle to recompute every alternative network fully, classifying by actual cycle presence and matrix equality, and recomputing every post bound/path/schedule independently. It never calls insertion generation, Floyd, Bellman-Ford or generation witness helpers; tests disable all of those while checking every control. Strict recursive key/type/length/order/value matching rejects forged reports.

The browser reuses the original JavaScript recursive path-enumeration pattern in a separate engine, fully recomputing every alternative. It does not use the native rank-one update to decide post distances or classifications, and it does not fetch native reports. Native/browser full reports are compared. Original core, oracle, engine, contract and original test sources remain unchanged. The original CLI parser and atomic writer are reused by the new module and console entry point. Browser JSON.parse retains its original last-key-wins/numeric-normalization distinction from native strict parsing.

## Reproduce

```bash
python -m stnlab.insertions proposal.json --output report.json
python -m stnlab.insertions report.json --verify
python -m unittest discover -s tests -v
npm test
bash tools/check_wheel.sh
python -m http.server 8000 --directory docs
```

After installation use `stnlab-insertions`. The wheel check runs both original and insertion families outside the checkout, via module and console commands, checking four package origins in site-packages. No runtime dependencies; building requires pip/setuptools. Python 3.10-3.13 and Node 22/actual Chrome in CI.

Eight new native tests, seventeen total. New exhaustive suites cover all 256 two-node bases including loops, every ordered candidate endpoint pair and weights -1/0/1 (3072 proposals), and all 64 three-node acyclic bases at absent/-1/0/1 edges with all endpoint pairs and candidate weights -1/0/1 (1728 proposals). Each report is fully independently recomputed, and every path, cycle, boundary schedule, attaining schedule, via walk and ray is directly audited. Sixty seeded larger networks, six point relabelings and 120 edge permutations, closure-call independence, disabled-generator checking, malformed/forged records and strict atomic CLI rejection are tested.

Three new Node/Chrome tests, six total. 346 new cross-engine reports cover 1008 cell records (118 changed), 7011 spectrum alternatives and 220 inconsistent results. These are summed fixture counts, not performance/accuracy evidence. Real Chrome audits all ten controls at 320/390/1280, including every one of 120 cell proofs (115 finite, five rays), all 369 spectrum alternatives across nine consistent bases, nine thresholds and two cycle cases per width. It checks full JSON, input/return/cycle/via/shortest-path tables, every matrix cell, complete timeline values/slacks, export, stale clearing, invalid input and overflow.

## Scope limits

Only one candidate on a fixed base, not a sequence, deletion engine, persistent branching data structure, IPPC/chordal algorithm, temporal planner, dispatchable network or STNU. The distance update is O(n²), but the explanatory path/cycle enumeration and full checker are deliberately tiny, not an O(n²) end-to-end solver. No benchmark or performance comparison. No causal or action selection, resource capacity, uncertain durations, model API, private records, real calendars, execution or safety guarantee. Classic theory is attributed below, not claimed as a new algorithm. All ten controls are original synthetic networks.

## Source ledger

Sources fetched and relevant sections inspected November 9, 2026. Primary/academic research, academic teaching, official software docs and community exposition are distinguished. No source code, figures, example networks or benchmark results copied.

1. Luke Hunsberger, *Quantitative Temporal Reasoning in Planning Problems*, AAAI-2004 tutorial. https://www.cs.vassar.edu/~hunsberg/__papers__/luke_hunsberger_tutorial.pdf. Governing slides 23,35-37 state the exact insertion consistency condition, redundancy regions and naive all-pairs update formula. Later propagation/canonicalization/real-time and controllability algorithms are not implemented. Academic teaching; high confidence.
2. Andrea Micheli, *An Efficient Incremental Simple Temporal Network Data Structure for Temporal Planning*. https://arxiv.org/html/2212.07226v2. Sections 2-3 motivate incremental constraint addition, branching/persistence and the fact that insertions cannot repair an inconsistent network. Its implicit nonnegative-reference constraints, inverted-graph representation, persistent delta-STN, planning architecture and reported performance are not ours. Primary research; high confidence for this distinction.
3. Rina Dechter, Itay Meiri, Judea Pearl, *Temporal constraint networks*, Artificial Intelligence 49 (1991). https://ftp.cs.ucla.edu/pub/stat_ser/r113-reprint.pdf. The original PDF Section 3 was inspected in the base project; current extracted text corroborates the cycle/minimal-network framework but omits governing portions of Section 3. The direct insertion formula is grounded in source 1, not the incomplete web extraction. Primary paper; bounded source-coverage caveat retained.
4. Piotr Indyk, MIT 6.006 Lecture 17, Spring 2011. https://courses.csail.mit.edu/6.006/spring11/lectures/lec17.pdf. Difference-constraint cycle contradiction and zero-super-source potential feasibility proof support complete schedule evidence. Other robot-planning examples are outside scope. Academic lecture; high confidence.
5. NetworkX official documentation, *negative_edge_cycle*. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.negative_edge_cycle.html. Any-component negative-cycle detection and auxiliary super-source distinction. Not used as a runtime dependency or a benchmark. Official software docs; high confidence.
6. *Floyd-Warshall Algorithm*, Algorithms for Competitive Programming. https://cp-algorithms.com/graph/all-pair-shortest-path-floyd-warshall.html. Shortest-walk decomposition, infinity guards and negative-cycle limits support old closure handling. This is not presented as the direct insertion proof. Community exposition; secondary confidence, cross-checked with academic sources.

Discovery-only item: Planken et al., *Incrementally Solving STNs by Enforcing Partial Path Consistency*, ICAPS 2010, https://ojs.aaai.org/index.php/ICAPS/article/view/13417. Search exposed an abstract and excerpts but direct fetch returned NO_CONTENT_RETURNED. No theorem, source code, algorithm implementation or performance claim relies on this unread page. We do not implement IPPC. This seventh item is not counted as a verified source.
