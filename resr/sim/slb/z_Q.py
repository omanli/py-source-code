""" Experiment with priority feature in Queue Component

    Job State: entities in priority queues  (next operation/task)
               remember last/current server (mechanic) (resource)

    Srv State: keep track whether assigned (resource claimed?)

    find circumstances to switch server (mechanic) on a job
                       to make 
    
    handle service time dependent on the server skill/type

"""

import salabim as sim


class SIM:
    env = None
    A   = None  # arrivals
    S   = None  # server
    Q   = None  # queue
    X   = None  # scheduler
    iat = [int(v) for v in " 0 1 3 2 4 2 1".split()]
    pri = [int(v) for v in " 0 3 2 1 3 2 1".split()]
    svt = [int(v) for v in "20 2 4 1 3 1 2".split()]
    fmt_t = "{:4.1f}"


def print_curr_time():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")

def print_event(e, n):
    print_curr_time()
    print(f"{e} {n}")

def print_Q():
    for e in SIM.Q:
        print(f"      {e.name()} {e.prior} {e.t_arr}")


class A(sim.Component):
    def process(self):
        for i,(t,p) in enumerate(zip(SIM.iat, SIM.pri)):
            self.hold(t)
            a = sim.Component(name=f"e{i+1}")
            print_event("Arr", a.name())
            a.t_arr = SIM.env.now()
            a.prior = p
            SIM.Q.add_sorted(component=a, priority=p)
            print_Q()
            print()



class S(sim.Component):
    def process(self):
        for s in SIM.svt:
            self.passivate()
            assert len(SIM.Q) > 0
            j = SIM.Q.pop()
            print_event("Sta", j.name())
            self.hold(s)
            print_event("Dpt", j.name())



class X(sim.Component):
    def process(self):
        msg = {True:"Idle", False:"Busy"}
        while True:
            self.standby()
            print_event("Sch", f"[{msg[SIM.S.ispassive()]}] {len(SIM.Q)}")
            if (len(SIM.Q) > 0) and SIM.S.ispassive():
                SIM.S.activate()


def Run():
    SIM.env = sim.Environment(trace=False)
    SIM.A = A("Arrivals")
    SIM.S = S("Service")
    SIM.X = X("Scheduler")
    SIM.Q = sim.Queue(name="Priority Q")

    print_event("Sim ready to run()", "")
    SIM.env.run()

    return


