"""Traffic light controllers.

TrafficLightController (abstract)
 |- FixedTimeController : classic fixed cycle, ignores traffic
 |- SmartController     : gives green to the axis with the most waiting vehicles

Both use the SAME phases and safety rules (yellow + all-red), so the comparison is fair.
"""
from abc import ABC, abstractmethod
import traci

YELLOW = 3
ALL_RED = 2
DETECTION_RANGE = 100.0   # metres before the stop line observed by the smart controller


class Phase:
    def __init__(self, name, state, duration=None):
        self.name, self.state, self.duration = name, state, duration


def build_phases(tls_id, net, axes):
    """Build green / yellow / all-red state strings for each axis from the SUMO network."""
    links = traci.trafficlight.getControlledLinks(tls_id)
    n = len(links)
    phases = {}
    for axis, edges in axes.items():
        green, yellow = ["r"] * n, ["r"] * n
        for i, group in enumerate(links):
            if not group:
                continue
            in_lane = group[0][0]
            edge_id = in_lane.rsplit("_", 1)[0]
            if edge_id in edges:
                out_edge = group[0][1].rsplit("_", 1)[0]
                is_left = net.getEdge(edge_id).getConnections(net.getEdge(out_edge))
                left = any(c.getDirection() in ("l", "L", "t") for c in is_left)
                green[i] = "g" if left else "G"     # left turns yield to oncoming traffic
                yellow[i] = "y"
        phases[axis] = (Phase(axis + "_green", "".join(green)),
                        Phase(axis + "_yellow", "".join(yellow), YELLOW))
    phases["ALL_RED"] = Phase("all_red", "r" * n, ALL_RED)
    return phases


class TrafficLightController(ABC):
    name = "abstract"

    def __init__(self, tls_id, net, axes):
        self.tls_id = tls_id
        self.axes = axes
        self.phases = build_phases(tls_id, net, axes)
        self.keys = list(axes)
        self.current_axis = self.keys[0]
        self.stage = "green"            # green -> yellow -> all_red -> green (other axis)
        self.stage_time = 0
        self._apply()

    # ---- helpers -------------------------------------------------------
    def _apply(self):
        if self.stage == "green":
            state = self.phases[self.current_axis][0].state
        elif self.stage == "yellow":
            state = self.phases[self.current_axis][1].state
        else:
            state = self.phases["ALL_RED"].state
        traci.trafficlight.setRedYellowGreenState(self.tls_id, state)

    def other(self):
        return self.keys[1] if len(self.keys) > 1 and self.current_axis == self.keys[0] else self.keys[0]

    def _advance_transition(self):
        """Handle yellow and all-red stages (identical for every controller)."""
        if self.stage == "yellow" and self.stage_time >= YELLOW:
            self.stage, self.stage_time = "all_red", 0
            self._apply()
        elif self.stage == "all_red" and self.stage_time >= ALL_RED:
            self.current_axis = self.other()
            self.stage, self.stage_time = "green", 0
            self._apply()

    def _start_yellow(self):
        self.stage, self.stage_time = "yellow", 0
        self._apply()

    def step(self):
        self.stage_time += 1
        if self.stage == "green":
            if self.should_switch():
                self._start_yellow()
        else:
            self._advance_transition()

    @abstractmethod
    def should_switch(self) -> bool:
        ...

    def info(self):
        return {"controller": self.name, "axis": self.current_axis,
                "stage": self.stage, "stage_time": self.stage_time}


class FixedTimeController(TrafficLightController):
    name = "fixed"

    def __init__(self, tls_id, net, axes, green_a=35, green_b=35):
        self.green = {"A": green_a, "B": green_b}
        super().__init__(tls_id, net, axes)

    def should_switch(self):
        return self.stage_time >= self.green[self.current_axis]


class SmartController(TrafficLightController):
    """Adaptive: switch to the axis with more waiting vehicles.

    Safeguards: minimum green (no flicker), maximum green (no starvation),
    and the same yellow / all-red phases as the fixed controller.
    """
    name = "smart"

    def __init__(self, tls_id, net, axes, min_green=10, max_green=45, margin=1):
        self.min_green, self.max_green, self.margin = min_green, max_green, margin
        super().__init__(tls_id, net, axes)

    def demand(self, axis):
        """Vehicles waiting (stopped or slowly approaching) near the stop line on an axis."""
        count = 0
        for edge in self.axes[axis]:
            for lane_idx in range(traci.edge.getLaneNumber(edge)):
                lane = f"{edge}_{lane_idx}"
                length = traci.lane.getLength(lane)
                for v in traci.lane.getLastStepVehicleIDs(lane):
                    if traci.vehicle.getLanePosition(v) >= length - DETECTION_RANGE:
                        count += 1
        return count

    def should_switch(self):
        if self.stage_time < self.min_green:
            return False
        mine, theirs = self.demand(self.current_axis), self.demand(self.other())
        if theirs == 0:
            return False                       # nobody waiting on the other road: keep green
        if self.stage_time >= self.max_green:
            return True                        # avoid starvation
        if mine == 0:
            return True                        # current road empty, other road waiting
        return theirs > mine + self.margin     # other road clearly busier
