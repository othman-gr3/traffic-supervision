"""Automatic analysis of a junction in ANY SUMO network (synthetic or from OpenStreetMap).

- finds the incoming roads (approaches) of a traffic-light junction
- groups them in two axes by angle: "A" = the boulevard (more capacity), "B" = the crossing street
- gives each approach a readable label (street name + direction it comes from)
"""
import math, sys, os


def _resolve_sumo_home():
    if "SUMO_HOME" in os.environ:
        return os.environ["SUMO_HOME"]
    for candidate in [
        r"C:\Program Files (x86)\SUMO",
        r"C:\Program Files\SUMO",
        "/usr/share/sumo",
        "/usr/local/share/sumo",
        "/usr/local/lib/python3.12/dist-packages/sumo",
    ]:
        if os.path.isdir(os.path.join(candidate, "tools")):
            return candidate
    try:
        import importlib.util
        spec = importlib.util.find_spec("sumolib")
        if spec and spec.origin:
            return os.path.dirname(os.path.dirname(os.path.dirname(spec.origin)))
    except Exception:
        pass
    raise EnvironmentError(
        "Cannot locate SUMO. Set the SUMO_HOME environment variable."
    )


os.environ["SUMO_HOME"] = _resolve_sumo_home()
sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import sumolib

COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def load_net(path):
    return sumolib.net.readNet(path, withPrograms=False)


def bearing(edge):
    """Travel direction at the end of the edge (0 = north, clockwise)."""
    (x1, y1), (x2, y2) = edge.getShape()[-2], edge.getShape()[-1]
    return math.degrees(math.atan2(x2 - x1, y2 - y1)) % 360


def comes_from(edge):
    return COMPASS[int(((bearing(edge) + 180) % 360 + 22.5) // 45) % 8]


def vehicle_approaches(net, tls_id):
    try:
        node = net.getNode(tls_id)
    except KeyError:
        ids = [n.getID() for n in net.getNodes() if n.getType() == "traffic_light"]
        raise SystemExit(f"Junction '{tls_id}' not found. Traffic-light junctions: {ids}")
    return [e for e in node.getIncoming()
            if e.allows("passenger") and not e.getFunction()]


def junction_info(net, tls_id):
    edges = vehicle_approaches(net, tls_id)
    if len(edges) < 2:
        raise SystemExit(f"Junction {tls_id} has fewer than 2 usable incoming roads")
    # cluster by axis angle (direction modulo 180)
    seed = bearing(edges[0]) % 180
    def close(e):
        d = abs(bearing(e) % 180 - seed)
        return min(d, 180 - d) < 45
    g1 = [e for e in edges if close(e)]
    g2 = [e for e in edges if not close(e)]
    cap = lambda g: sum(e.getLaneNumber() * e.getSpeed() for e in g)
    if g2 and cap(g2) > cap(g1):
        g1, g2 = g2, g1
    axes = {"A": [e.getID() for e in g1]}
    if g2:
        axes["B"] = [e.getID() for e in g2]
    labels, used = {}, set()
    for e in edges:
        name = e.getName() or e.getID()
        label = f"{name} (from {comes_from(e)})"
        while label in used:
            label += "'"
        used.add(label)
        labels[e.getID()] = label
    return {"axes": axes, "labels": labels}


def list_junctions(net_path):
    net = load_net(net_path)
    print(f"{'junction id':<28}{'incoming roads'}")
    for n in net.getNodes():
        if n.getType() == "traffic_light":
            inc = vehicle_approaches(net, n.getID())
            desc = ", ".join(f"{e.getName() or e.getID()}[{e.getLaneNumber()} lanes, from {comes_from(e)}]"
                             for e in inc)
            print(n.getID())
            print("    " + desc)


if __name__ == "__main__":
    list_junctions(sys.argv[1])
