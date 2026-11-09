# STNLab

**One more deadline. Still a possible plan?** Exact simple temporal networks for small AI plans. Each input edge `[u,v,w]` means `t[v] - t[u] <= w`. Inspect a strongest implied upper bound, a complete schedule attaining it, an unbounded translation ray, or a negative cycle proving no schedule exists.

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

## Every consequence has evidence

- All ordered time differences: exact finite bound, original-index path and complete attaining schedule; or an anchored ray proving unboundedness.
- Full directed bound matrix and complete base schedule. Times can be negative; `t0=0` removes only a common translation.
- Each original edge removed separately: an alternate implication path, or a schedule satisfying every other edge and violating the removed one.
- Negative-cycle inconsistency witness with every original inequality and the impossible summed inequality.
- Eleven original synthetic controls: tighter chains, three-edge conflict, disconnected freedom/conflict, duplicate redundancy, zero cycles, negative self-loop, single anchor, six free points, 12-edge network and a length-five bound of 100.

Nine native tests include all 256 two-node graphs with loops and all 4096 three-node directed graphs at absent/-1/0/1 edges, 100 seeded larger networks, independent bounded-integer checks, node/edge relabeling, strict forgeries and CLI errors. Three Node/Chrome tests include 367 complete cross-engine reports. Actual Chrome inspects every bound/ray/removal/cycle at 320/390/1280, exports, stale clearing and overflow. Installed-wheel controls reproduce outside checkout.

## Boundaries before interpretation

At most six time points, 12 directed edges, integer input weights -20..20. Times are real-valued; integer certificates suffice for these integer constraints. Native Floyd-Warshall closure and synchronous Bellman-Ford schedules; independent permutation/edge-product verifier and recursive browser search. Enumeration is deliberately tiny, not a production scaling claim. No uncertain durations, resource capacity, disjunctions, dispatchability, objective optimization, real calendar actions, learned model, paid API or new algorithm. Individually attainable bounds do not make every combination of their endpoints feasible. Individually redundant duplicates cannot safely be deleted together. MIT license.
