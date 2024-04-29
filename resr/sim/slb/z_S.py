""" Experiment with requesting resources on behalf of other Components
    when does control goes to the Component and if it come back

    How salabim works: 
    when a resource is requested 


import <this> as zS
reload(zS); zS.Experiment(ins=0, retry=True,  sleep=1.2)
reload(zS); zS.Experiment(ins=0, retry=True,  sleep=4.0)
reload(zS); zS.Experiment(ins=0, retry=False, sleep=1.2)
"""


import salabim as sim

from .Util import RV


class INS:
    JobArr = None   # list of job arrival times
    JobDur = None   # list of job task durations
    SchAct = None   # list of scheduler activation times
    NumMch = None
    sleep  = None

def Set_Instance(cho):
    if cho == 0:
        INS.JobArr = (1.2, 1.5, 1.7, 1.8, 12.2, 14.4, 15.6)
        INS.JobDur = (4.0, 4.0, 1.0, 3.0,  1.0,  4.0,  2.0)
        INS.SchAct = (2.3, 14.7, 18.2)
        INS.NumMch = 2
    if cho == 1:
        pass
    if cho == 2:
        pass
    if cho == 3:
        pass


class SIM:
    env = None
    prn = True
    S   = None  # scheduler
    J   = None  # list of jobs
    M   = None  # resource w capacity
    Q   = None  # resource request queue
    W   = None  # WIP state queue
    fmt_t = "{:5.1f}"
    fmt_jid = "J{:02d}"


def print_curr_time():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")

def print_event(e):
    if SIM.prn:
        print(SIM.fmt_t.format(SIM.env.now()), e)

def print_state(e):
    if SIM.prn:
        print(SIM.fmt_t.format(SIM.env.now()), end=" ")
        print(f"{SIM.M.available_quantity():3d} {len(SIM.Q):3d} {len(SIM.W):3d}  {e}")



class M(sim.Resource):
    pass


class J(sim.Component):
    def __init__(self, idx, arr, dur, *args, **kwargs):
        super().__init__(name=SIM.fmt_jid.format(idx), *args, **kwargs)
        self.idx = idx
        self.arr = arr
        self.dur = dur

    def process(self):
        self.hold(till=self.arr)
        SIM.Q.add(self)
        print_state(f"{self.name()} arrives & requests")
        # print_state(f"{self.name()} about to Activate Sch")
        # print_state(f"{self.name()} about to Passivate self")
        self.passivate()
        SIM.W.add(self)
        print_state((f"{self.name()} starts task "
                        f"     [{'T' if len(self.claimed_resources())>0 else 'F'}] "
                        f"(Mreq={len(SIM.M.requesters())})"))
        self.hold(self.dur)
        self.release()
        SIM.W.remove(self)
        print_state(f"{self.name()} complt task")


class Sch(sim.Component):
    def __init__(self, ret, act, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ret = ret
        self.act = act
    def process(self):
        self.hold(till=max(self.act, SIM.env.now()))
        print_state(f"Sch activated")
        while len(SIM.Q):
            if not self.ret and (SIM.M.available_quantity() == 0):
                break
            if SIM.M.available_quantity() > 0:
                j = SIM.Q.pop()
                j.request(SIM.M)  # granted request activates the job
                print_state(f"Sch {j.name()} Aft:request (Mreq={len(SIM.M.requesters())})")
            else:
                print_state(f"Sch {j.name()} going to sleep       (Mreq={len(SIM.M.requesters())})")
                self.hold(INS.sleep)
                print_state(f"Sch {j.name()} waking up from sleep (Mreq={len(SIM.M.requesters())})")
        print_state(f"Sch quitting")


def Experiment(ins, retry, sleep):
    SIM.env = sim.Environment(trace=False)
    INS.sleep = sleep
    Set_Instance(ins)

    SIM.M = M("Mechanic", capacity=INS.NumMch)
    SIM.Q = sim.Queue("Requests") # Jobs requesting a resource
    SIM.W = sim.Queue("WIP")      # Jobs in Process (seized a resource)

    assert len(INS.JobArr) == len(INS.JobDur)

    SIM.S = [Sch(name="Sch", ret=retry, act=a)
             for j,a in enumerate(INS.SchAct)
            ]

    SIM.J = [J(idx=j+1, arr=a, dur=d)
             for j,(a,d) in enumerate(zip(INS.JobArr, INS.JobDur))
            ]

    print_event("Avl Req WIP")
    SIM.env.run()
    print_state("Exp ends")

    return

