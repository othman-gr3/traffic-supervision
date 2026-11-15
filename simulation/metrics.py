"""Metrics aggregation per incoming road (approach).

Waiting time of a vehicle = total time spent stopped (speed < 0.1 m/s) on the
approach edge before crossing the stop line. Stats are computed:
  - live : vehicles currently on the approach (queue, speed, current longest wait)
  - cumulative : vehicles that already crossed the intersection (avg_wait, max_wait)
"""
from collections import defaultdict
import traci

STOP_SPEED = 0.1


class MetricsAggregator:
    def __init__(self, labels):
        self.labels = labels                # edge id -> readable road name
        self.approaches = list(labels)
        self.wait = {}                      # vehicle id -> seconds stopped on current approach
        self.where = {}                     # vehicle id -> approach edge
        self.done = defaultdict(list)       # approach -> waits of vehicles that crossed
        self.crossed = defaultdict(int)

    def update(self, sim_time):
        live = {a: {"speeds": [], "waits": [], "queue": 0} for a in self.approaches}
        present = set()
        for a in self.approaches:
            for v in traci.edge.getLastStepVehicleIDs(a):
                present.add(v)
                speed = traci.vehicle.getSpeed(v)
                if self.where.get(v) != a:
                    self.where[v], self.wait[v] = a, 0.0
                if speed < STOP_SPEED:
                    self.wait[v] += 1.0       # 1 simulation step = 1 s
                    live[a]["queue"] += 1
                live[a]["speeds"].append(speed)
                live[a]["waits"].append(self.wait[v])
        # vehicles that left their approach have crossed the stop line
        for v in list(self.where):
            if v not in present:
                a = self.where.pop(v)
                self.done[a].append(self.wait.pop(v))
                self.crossed[a] += 1

        roads = []
        for a in self.approaches:
            d, w = live[a], self.done[a]
            n = len(d["speeds"])
            roads.append({
                "road": self.labels[a],
                "edge": a,
                "vehicles": n,
                "queue": d["queue"],
                "avg_speed": round(sum(d["speeds"]) / n, 2) if n else 0.0,
                "current_max_wait": max(d["waits"], default=0.0),
                "avg_wait": round(sum(w) / len(w), 2) if w else 0.0,
                "max_wait": max(w, default=0.0),
                "crossed": self.crossed[a],
            })
        return {"time": sim_time, "roads": roads}
