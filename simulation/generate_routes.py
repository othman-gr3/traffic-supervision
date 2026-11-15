"""Generate traffic demand for ANY junction: heavy on the boulevard (axis A), lighter on the
crossing street (axis B). Arrivals are random (Poisson) but reproducible via SUMO's --seed.

Demand figures are ASSUMPTIONS (no public traffic counts): tune --blvd / --side
until queues look realistic at peak hour.
"""
import argparse
import network_info as ni

SHARE = {"s": 0.80, "r": 0.15, "l": 0.05}     # straight / right / left


def turn_kind(conn):
    d = conn.getDirection()
    return "s" if d == "s" else "r" if d in ("r", "R") else "l"


def upstream_path(edge, min_len=200, max_edges=3):
    """Extend the approach upstream so cars enter far enough from the stop line."""
    path = [edge]
    while sum(e.getLength() for e in path) < min_len and len(path) < max_edges:
        head = path[0]
        if head.getFromNode().getType() == "traffic_light":
            break
        preds = [p for p in head.getIncoming()
                 if p.allows("passenger") and p.getFromNode() != head.getToNode()
                 and head in p.getAllowedOutgoing("passenger") and p not in path]
        if not preds:
            break
        path.insert(0, max(preds, key=lambda p: p.getLaneNumber() * p.getSpeed()))
    return path


def build(net_path, tls_id, blvd_vph, side_vph, duration, out):
    net = ni.load_net(net_path)
    info = ni.junction_info(net, tls_id)
    boulevard = set(info["axes"]["A"])
    lines = ['<routes>',
             '  <vType id="car" accel="2.6" decel="4.5" sigma="0.5" tau="1.2" length="4.5" '
             'minGap="2.5" maxSpeed="13.89" emissionClass="HBEFA4/PC_petrol_Euro-4"/>']
    n = 0
    for e in ni.vehicle_approaches(net, tls_id):
        vph = blvd_vph if e.getID() in boulevard else side_vph
        moves = {}
        for dst in e.getAllowedOutgoing("passenger"):
            if dst.getToNode() == e.getFromNode():
                continue                                  # skip U-turns
            conns = e.getConnections(dst)
            if conns:
                moves.setdefault(turn_kind(conns[0]), []).append(dst)
        total = sum(SHARE[k] for k in moves)
        pre = " ".join(p.getID() for p in upstream_path(e)[:-1])
        for kind, outs in moves.items():
            for dst in outs:
                rate = vph * SHARE[kind] / total / len(outs) / 3600.0
                edges = f"{pre} {e.getID()} {dst.getID()}".strip()
                lines.append(f'  <route id="r{n}" edges="{edges}"/>')
                lines.append(f'  <flow id="f{n}_{kind}" type="car" route="r{n}" begin="0" end="{duration}" '
                             f'period="exp({rate:.5f})" departLane="best" departSpeed="max"/>')
                n += 1
    lines.append('</routes>')
    open(out, "w").write("\n".join(lines))
    return n


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--net", default="network/intersection.net.xml")
    p.add_argument("--tls", default="C", help="junction id (see list_junctions: python network_info.py NET)")
    p.add_argument("--blvd", type=int, default=900, help="veh/h per boulevard approach")
    p.add_argument("--side", type=int, default=250, help="veh/h per side-street approach")
    p.add_argument("--duration", type=int, default=1800)
    p.add_argument("--out", default="network/routes.rou.xml")
    a = p.parse_args()
    print(build(a.net, a.tls, a.blvd, a.side, a.duration, a.out), "flows written to", a.out)
