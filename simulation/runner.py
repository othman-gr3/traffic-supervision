"""Simulation runner: starts SUMO, drives a controller, yields metrics every second."""
import argparse, json, os, sys, tempfile
import xml.etree.ElementTree as ET

def _resolve_sumo_home():
    """Find SUMO_HOME: honour the env-var if already set, then try common install
    locations (Windows Program Files, Linux apt/pip paths), and finally fall back to
    the directory that contains the installed sumolib package so the code works on
    any platform without manual configuration."""
    if "SUMO_HOME" in os.environ:
        return os.environ["SUMO_HOME"]
    # Windows default installer path
    for candidate in [
        r"C:\Program Files (x86)\SUMO",
        r"C:\Program Files\SUMO",
        # Linux system / pip installs
        "/usr/share/sumo",
        "/usr/local/share/sumo",
        "/usr/local/lib/python3.12/dist-packages/sumo",
    ]:
        if os.path.isdir(os.path.join(candidate, "tools")):
            return candidate
    # Last resort: derive from the installed sumolib package location
    try:
        import importlib.util
        spec = importlib.util.find_spec("sumolib")
        if spec and spec.origin:
            # sumolib is at <SUMO_HOME>/tools/sumolib/__init__.py
            return os.path.dirname(os.path.dirname(os.path.dirname(spec.origin)))
    except Exception:
        pass
    raise EnvironmentError(
        "Cannot locate SUMO. Set the SUMO_HOME environment variable to your SUMO "
        "installation directory (the one that contains a 'tools' sub-folder)."
    )

os.environ["SUMO_HOME"] = _resolve_sumo_home()
sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))

import sumolib, traci
import network_info as ni
from controllers import FixedTimeController, SmartController
from metrics import MetricsAggregator

HERE = os.path.dirname(os.path.abspath(__file__))
NET = os.path.join(HERE, "network", "casa.net.xml")
ROUTES = os.path.join(HERE, "network", "routes_casa2.rou.xml")
TLS_ID = "cluster_12698757853_12698757855_2138359128"


def run(controller="fixed", seed=1, duration=1800, gui=False, net=NET, routes=ROUTES,
        tripinfo=None, tls=TLS_ID, green_a=35, green_b=35):
    """Generator: yields one metrics dict per simulated second."""
    tripinfo = tripinfo or os.path.join(tempfile.gettempdir(), f"tripinfo_{controller}_{seed}.xml")
    binary = sumolib.checkBinary("sumo-gui" if gui else "sumo")
    traci.start([binary, "-n", net, "-r", routes, "--seed", str(seed), "--no-step-log", "true",
                 "--no-warnings", "true", "--tripinfo-output", tripinfo,
                 "--device.emissions.probability", "1", "--end", str(duration),
                 "--waiting-time-memory", "1000"], label=f"{controller}_{seed}")
    try:
        sumo_net = ni.load_net(net)
        info = ni.junction_info(sumo_net, tls)
        if controller == "smart":
            ctrl = SmartController(tls, sumo_net, info["axes"])
        else:
            ctrl = FixedTimeController(tls, sumo_net, info["axes"], green_a, green_b)
        agg = MetricsAggregator(info["labels"])
        for t in range(duration):
            traci.simulationStep()
            ctrl.step()
            m = agg.update(t + 1)
            m["light"] = ctrl.info()
            yield m
    finally:
        traci.close()


def trip_summary(path):
    """Overall results from SUMO's tripinfo file (completed trips)."""
    trips = ET.parse(path).getroot().findall("tripinfo")
    n = len(trips)
    if n == 0:
        return {}
    wait = [float(t.get("waitingTime")) for t in trips]
    loss = [float(t.get("timeLoss")) for t in trips]
    co2 = [float(t.find("emissions").get("CO2_abs")) for t in trips if t.find("emissions") is not None]
    return {"completed_trips": n,
            "avg_wait_s": round(sum(wait) / n, 2), "max_wait_s": round(max(wait), 1),
            "avg_time_loss_s": round(sum(loss) / n, 2),
            "avg_co2_g": round(sum(co2) / len(co2) / 1000, 1) if co2 else None}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--controller", choices=["fixed", "smart"], default="fixed")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--duration", type=int, default=1800)
    p.add_argument("--gui", action="store_true")
    p.add_argument("--net", default=NET)
    p.add_argument("--routes", default=ROUTES)
    p.add_argument("--tls", default=TLS_ID, help="junction id")
    p.add_argument("--green-a", type=int, default=35, help="fixed controller: boulevard green (s)")
    p.add_argument("--green-b", type=int, default=35, help="fixed controller: side street green (s)")
    p.add_argument("--stream", action="store_true", help="print one JSON line per second")
    a = p.parse_args()
    info = os.path.join(tempfile.gettempdir(), f"tripinfo_{a.controller}_{a.seed}.xml")
    last = None
    for m in run(a.controller, a.seed, a.duration, a.gui, a.net, a.routes, info, a.tls, a.green_a, a.green_b):
        last = m
        if a.stream:
            print(json.dumps(m))
        elif m["time"] % 300 == 0:
            q = {r["road"]: r["queue"] for r in m["roads"]}
            print(f't={m["time"]:>5}s  queue={q}  light={m["light"]["axis"]}/{m["light"]["stage"]}')
    print("\nFinal per-road stats (vehicles that crossed):")
    for r in last["roads"]:
        print(f'  {r["road"]:<34} crossed={r["crossed"]:>4}  avg_wait={r["avg_wait"]:>6}s  max_wait={r["max_wait"]:>6}s')
    print("Overall:", trip_summary(info))
