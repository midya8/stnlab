# STNLab

STNLab checks exact simple temporal networks for small supplied plans. Each input edge `[u,v,w]` means `t[v] - t[u] <= w`. Inspect a strongest implied upper bound, a complete schedule attaining it, an unbounded translation ray, or a negative cycle proving no schedule exists.

[Interactive temporal inspector](https://midya8.github.io/stnlab/) · [Exact method and seven-source ledger](METHOD.md)

The default network directly allows `t2-t0 <= 12`, but a two-edge chain proves `<= 7`. A full feasible assignment reaches 7, so the bound is tight. A second network has three individually feasible edges summing to `0 <= -1`. An isolated anchor does not hide a conflict in another component. Missing directed paths are unbounded, not inconsistent.

## Run and audit

```bash
python -m stnlab input.json --output report.json
python -m stnlab report.json --verify
python -m unittest discover -s tests -v
npm test                       # Node 22 + actual Chrome
bash tools/check_wheel.sh       # installed outside checkout, both entry points
python -m http.server 8000 --directory docs
```

Or `pip install .`, then `stnlab input.json`. Python 3.10+, no runtime dependencies; building requires pip/setuptools. The browser runs independent recursive JavaScript path search, not a native report or an API.

```python
from stnlab import analyze, verify
report = analyze({'nodes': 3, 'edges': [[0, 2, 12], [0, 1, 4], [1, 2, 3]]})
assert report['matrix'][0][2] == 7
assert report['pairs'][2]['path'] == [1, 2]
assert verify(report)
```

The full current suite has 31 Python and 12 Node/actual-Chrome tests across all four inspectors. The original release counts below describe the base inspector.

## Choose a question

- **Original inspector:** is the network feasible, and what is the tightest bound on each time difference?
- **Insertion:** what changes when one proposed constraint is added to a fixed base?
- **Projection:** what constraints remain after existentially hiding selected time points?
- **Conflicts and repairs:** which edge sets are minimally inconsistent, and which removals restore consistency?

These operate on supplied constraint networks, not calendars. Projection is not
edge deletion, and a minimal repair need not have minimum cardinality.

## Bounds and witnesses

- All ordered time differences: exact finite bound, original-index path and complete attaining schedule; or an anchored ray proving unboundedness.
- Full directed bound matrix and complete base schedule. Times can be negative; `t0=0` removes only a common translation.
- Each original edge removed separately: an alternate implication path, or a schedule satisfying every other edge and violating the removed one.
- Negative-cycle inconsistency witness with every original inequality and the impossible summed inequality.
- Eleven original synthetic controls: tighter chains, three-edge conflict, disconnected freedom/conflict, duplicate redundancy, zero cycles, negative self-loop, single anchor, six free points, 12-edge network and a length-five bound of 100.

The original nine native tests include all 256 two-node graphs with loops and all 4096 three-node directed graphs at absent/-1/0/1 edges, 100 seeded larger networks, independent bounded-integer checks, node/edge relabeling, strict forgeries and CLI errors. The original three Node/Chrome tests include 367 complete cross-engine reports. Actual Chrome inspects every bound/ray/removal/cycle at 320/390/1280, exports, stale clearing and overflow. Installed-wheel controls reproduce outside checkout.

## Scope and limits

At most six time points, 12 directed edges, integer input weights -20..20. Times are real-valued; integer certificates suffice for these integer constraints. Native Floyd-Warshall closure and synchronous Bellman-Ford schedules; independent permutation/edge-product verifier and recursive browser search. Enumeration is deliberately tiny, not a production scaling claim. No uncertain durations, resource capacity, disjunctions, dispatchability, objective optimization, real calendar actions, learned model, paid API or new algorithm. Individually attainable bounds do not make every combination of their endpoints feasible. Individually redundant duplicates cannot safely be deleted together. MIT license.


## Single-edge insertion

[Insertion inspector](https://midya8.github.io/stnlab/insertions.html) · [Insertion contract and source ledger](INSERTIONS.md)

Add one proposed [u,v,w] constraint to a fixed base. Its exact feasible threshold is -D[v,u], or no finite lower threshold when the return path is absent. The boundary has a full feasible schedule; one below it has a negative-cycle certificate. A redundant proposal changes no matrix entry. Otherwise inspect every old/new bound, old left and right routes through the candidate, canonical post-insertion path, attaining schedule or unbounded ray. A 41-weight integer sweep shows the consistency/tightening/redundancy regions and exact changed-cell counts.

Native generation computes closure once and updates each distance from the immutable old matrix. Independent full permutation/edge-product recomputation checks every sampled weight and witness; the browser independently recomputes with recursive paths. Ten original controls include a -100 threshold outside the input window, an inconsistent base and thirteen total edges. The original core, independent oracle, browser engine and original test sources remain unchanged.

```bash
python -m stnlab.insertions proposal.json --output insertion-report.json
python -m stnlab.insertions insertion-report.json --verify
# After installation: stnlab-insertions proposal.json
```

One candidate at a time, not accumulated insertions or a fully dynamic planner. The distance update is O(n²), not the exhaustive certificate generation/checker. See INSERTIONS.md for exact source distinctions and independently counted test evidence.

## Existential projection

[Projection inspector](https://midya8.github.io/stnlab/projection.html) · [Exact contract and six-source ledger](PROJECTION.md)

Hide time points without losing constraints implied through them. Compare exact closure restriction with naive edge deletion, test a retained assignment, and inspect a full original-network extension or an original path proving it impossible. Every finite projected difference has a complete attaining schedule; missing paths have anchored unbounded rays. Naive-deletion counterexamples show the lost consequences explicitly. An inconsistent hidden component still makes projection empty.

```sh
python -m stnlab.projection input.json --output projection.json
python -m stnlab.projection projection.json --verify
# or, after installation: stnlab-projection input.json
```

Twelve synthetic controls, independent permutation/edge-product replay, a separate Fourier-Motzkin elimination audit and recursive browser recomputation. Retained IDs are preserved, including t0=0; negative real times are allowed. Projected edges/witnesses can exceed the bounded public input windows. This is classical existential projection, not point deletion, task execution or a new algorithm. The original and insertion inspectors remain intact.


## Complete conflicts and repairs

[All-conflict inspector](https://midya8.github.io/stnlab/conflicts.html) | [Contract and source ledger](CONFLICTS.md)

Inspect every inclusion-minimal inconsistent edge set and every inclusion-minimal correction set. Full conflict-deletion schedules prove minimality; restoration cycles prove every proposed removal is needed. Complete subset feasibility, minimum-cardinality ties and both directions of hitting-set duality are independently audited. Ten original controls include unequal-size minimal repairs, disconnected conflicts, duplicate edges, zero cycles and a 12-edge complete directed network. Classical bounded temporal diagnosis, not a new algorithm or real execution.
