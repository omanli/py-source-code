""" Experiment with warm up period and statistics resetting

import <this> as W
reload(W); W.Test_Warm_Up(1, T=10, W=4)
reload(W); W.Test_Warm_Up(1, T= 9, W=5)
reload(W); W.Test_Warm_Up(2, T= 9, W=5)
reload(W); W.Test_Warm_Up(2, T=10, W=4) 
reload(W); W.Test_Warm_Up(2, T=15, W=6) 
reload(W); W.Test_Warm_Up(3, T=20, W=4)
reload(W); W.Test_Warm_Up(3, T=20, W=7)
"""

from types import SimpleNamespace as SNS
import salabim as sim

inf = float('inf')

class SIM:
    env = None
    Arrivals = None  # arrival process
    Server   = None  # server
    System   = None  # queue
    Entities = None  # list of entities
    iat = [int(v) for v in " 3 1 3 2 4 2 1".split()]
    svt = [int(v) for v in " 2 2 4 1 3 1 2".split()]
    fmt_t = "{:4.1f}"
    print_log = True
    print_ent = False


def print_curr_time():
    if SIM.print_log:
        print(SIM.fmt_t.format(SIM.env.now()), end=": ")

def print_event(e, n):
    if SIM.print_log:
        print_curr_time()
        print(f"{e} {n}")


class A(sim.Component):
    def process(self):
        for i,(t,s) in enumerate(zip(SIM.iat, SIM.svt)):
            self.hold(t)
            a = J(name=f"e{i+1}", svc_time=s)
            SIM.Entities.append(a)


class J(sim.Component):
    def __init__(self, svc_time, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.t_arr = SIM.env.now()
        self.t_svc = svc_time
        self.t_sta = inf
        self.t_dep = inf

    def process(self):
        print_event("Arr", self.name())

        SIM.System.add(component=self)
        self.request(SIM.Server)

        self.t_sta = SIM.env.now()
        self.hold(self.t_svc)
        self.release()

        self.t_dep = SIM.env.now()
        SIM.System.remove(component=self)

        print_event("Dep", self.name())



def Test_Warm_Up(cho, T=None, W=None):
    if cho == 1:
        # no one waits (sparse arrivals)
        SIM.iat = [int(v) for v in "1 4 6 4 5 2".split()]
        SIM.svt = [int(v) for v in "2 3 3 3 1 2".split()]
    elif cho == 2:
        # all wait (dense arrivals)
        SIM.iat = [int(v) for v in "1 2 5 3 6 1".split()]
        SIM.svt = [int(v) for v in "4 6 4 3 1 2".split()]
    elif cho == 3:
        # simple
        SIM.iat = [int(v) for v in "1 3 4 9".split()]
        SIM.svt = [int(v) for v in "5 5 5 3".split()]
    else:
        raise ValueError(f"Invalid cho={cho!r}")
    
    SIM.print_log = False
    SIM.print_ent = True
    Run(T=T, W=0)
    Compare_Metrics(T=T, W=0)
    if W is not None:
        SIM.print_ent = False
        Run(T=T, W=W)
        Compare_Metrics(T=T, W=W)




def Run(T=None, W=None):
    SIM.env = sim.Environment(trace=False, do_reset=True)
    SIM.Arrivals = A("Arrivals")
    SIM.Server   = sim.Resource(name="Server")
    SIM.System   = sim.Queue(name="Queue")
    SIM.Entities = []

    print_event("Sim ready to run()", "")
    if not T:
        SIM.env.run()
        Ts = SIM.env.now()
    elif not W:
        SIM.env.run(till=T)
        Ts = T
    else:
        SIM.env.run(till=W)
        print_event("Sim finished warmup", "")
        [m.reset() for m in SIM.System.all_monitors()]
        [m.reset() for m in SIM.Server.all_monitors()]
        SIM.env.run(till=T)
        Ts = T - W
    print_event("Sim finished run()", "")

    return



def Compare_Metrics(T, W):
    s = Calculate_Metrics_slbm()
    o = Calculate_Metrics_objs(T, W)
    Ts = (T - W) if W is not None else T

    if SIM.print_log:
        print(f"  T = {T:.1f}   Ts = {Ts:.1f}   W = " + (f"{W:.1f}" if W is not None else f"{0:.1f}"))
        print()

    if SIM.print_ent:
        print(f"{'Arr':>5} {'Sta':>5} {'Dep':>5} {'Wait':>5} {'Svc':>5} {'Sys':>5}")
        for e in SIM.Entities:
            print(f"{e.t_arr:5.1f} {e.t_sta:5.1f} {e.t_dep:5.1f} " + \
                 (f"{e.t_sta - e.t_arr:5.1f} " if e.t_sta<inf else f"{'--':>5} ") + \
                  f"{e.t_svc:5.1f} " + \
                  f"{(e.t_dep - e.t_arr) if e.t_dep < inf else (Ts - e.t_arr):5.1f} ")
        print()
    
    print(f"{'':>15} {'Slb':>6}  {'Calc':>6}")
    if SIM.print_log:
        print(f"{'#Arr':>15}: {s.nA:5.1f}   {o.nA:5.1f}")
        print(f"{'#Dep':>15}: {s.nD:5.1f}   {o.nD:5.1f}")
    print(f"{   'Utilization':>15}: {100*s.Utl:5.1f}%  {100*o.Utl:5.1f}%")
    print(f"{'avg   Sys Time':>15}: {s.aST:6.2f}  {o.aST:6.2f}")
    print(f"{'avg  Wait Time':>15}: {s.aWT:6.2f}  {o.aWT:6.2f}")
    print(f"{'avg   Svc Time':>15}: {s.aTT:6.2f}  {o.aTT:6.2f}")
    print(f"{'avg num in Sys':>15}: {s.nS :6.2f}  {o.nS :6.2f}")
    print()




def Calculate_Metrics_slbm():
    s = SNS()

    s.nA  = SIM.System.number_of_arrivals
    s.nD  = SIM.System.number_of_departures
    s.Utl = SIM.Server.occupancy.mean()
    s.aST = SIM.System.length_of_stay.mean()
    s.aWT = SIM.Server.requesters().length_of_stay.mean()
    s.aTT = SIM.Server.claimers().length_of_stay.mean()
    s.nS  = SIM.System.length.mean()

    return s



def Calculate_Metrics_objs(T, W):
    Ts = (T - W) if W is not None else T

    o = SNS()

    o.nA  = len(SIM.Entities)
    o.nD  = sum(1 for e in SIM.Entities if e.t_dep < inf)
    TT = [((e.t_svc - max(0, W - e.t_sta)) if e.t_dep < inf else (T - max(W, e.t_sta))) 
          for e in SIM.Entities 
          if e.t_sta < inf and e.t_dep > (W if W else 0)]
    o.Utl = sum(TT) / Ts
    ST = [(e.t_dep - e.t_arr) for e in SIM.Entities 
          if e.t_dep < inf and e.t_dep > (W if W else 0)]
    TS = [e.t_svc for e in SIM.Entities if (W if W else 0) < e.t_dep < inf]
    WT = [(min(T, e.t_sta) - e.t_arr) 
          for e in SIM.Entities 
          if W < e.t_dep and W < e.t_sta < inf]
    o.aST = sum(ST) / len(ST) if len(ST) else float('nan')
    o.aWT = sum(WT) / len(WT) if len(WT) else float('nan')
    o.aTT = sum(TS) / len(TS) if len(TS) else float('nan')
    o.nS  = sum([(min(T, e.t_dep) - max(W, e.t_arr)) 
                 for e in SIM.Entities 
                 if e.t_dep > (W if W else 0)]) / Ts

    return o
