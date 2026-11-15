"""Compare fixed vs smart controller on identical traffic (same seeds), several runs."""
import argparse, csv, os, statistics as st, tempfile
import runner


def one(controller, seed, duration, **kw):
    info = os.path.join(tempfile.gettempdir(), f"cmp_{controller}_{seed}.xml")
    last = None
    for last in runner.run(controller, seed, duration, tripinfo=info, **kw):
        pass
    s = runner.trip_summary(info)
    s.update(controller=controller, seed=seed)
    for r in last["roads"]:                      # per-road cumulative stats
        s[f'avg_wait_{r["road"]}'] = r["avg_wait"]
        s[f'max_wait_{r["road"]}'] = r["max_wait"]
    return s


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--duration", type=int, default=1800)
    p.add_argument("--out", default="results.csv")
    p.add_argument("--net", default=runner.NET)
    p.add_argument("--routes", default=runner.ROUTES)
    p.add_argument("--tls", default=runner.TLS_ID)
    p.add_argument("--green-a", type=int, default=35)
    p.add_argument("--green-b", type=int, default=35)
    a = p.parse_args()
    kw = dict(net=a.net, routes=a.routes, tls=a.tls, green_a=a.green_a, green_b=a.green_b)
    rows = [one(c, s, a.duration, **kw) for s in range(1, a.seeds + 1) for c in ("fixed", "smart")]
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
        w.writeheader(); w.writerows(rows)
    metrics = ["avg_wait_s", "max_wait_s", "avg_time_loss_s", "avg_co2_g", "completed_trips"] + \
              sorted(k for k in rows[0] if k.startswith("avg_wait_") and k != "avg_wait_s")
    print(f"\nMean over {a.seeds} seeds ({a.duration}s each)")
    print(f'{"metric":<44}{"fixed":>9}{"smart":>9}{"change":>9}')
    for m in metrics:
        f_ = st.mean(r[m] for r in rows if r["controller"] == "fixed")
        s_ = st.mean(r[m] for r in rows if r["controller"] == "smart")
        print(f"{m:<44}{f_:>9.1f}{s_:>9.1f}{(s_ - f_) / f_ * 100 if f_ else 0:>8.0f}%")
