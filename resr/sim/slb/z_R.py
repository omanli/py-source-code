""" Experiment with requesting resources on behalf of other Components

    Job State: entities in priority queues  (next operation/task)
                  add self to request queue
                  rather than requesting the resource directly
               remember last/current server (mechanic) (resource)

    Srv State: keep track whether assigned (resource claimed?)

    find circumstances to switch server (mechanic) on a job
                       to make 
    
    handle service time dependent on the server skill/type

    use Scheduler.activate() rather than 
        Scheduler.process():self.standby()
"""


""" old scheduler logic:
r1 = sim.random.random() #{r1:5.3f} {r2:5.3f}
r2 = sim.random.random()

if (r1 > 0.4) and (SIM.M.available_quantity() > 0):
    print_event(f"Sch before Job req")
    SIM.J.request(SIM.M)
    print_event(f"Sch after  Job req")
    continue

if (r2 > 0.6) and (SIM.M in SIM.J.claimed_resources()):
    print_event(f"Sch before Job rel")
    SIM.J.release(SIM.M)
    print_event(f"Sch after  Job rel")
    continue

print_event(f"Sch no action")



[zR.Experiment(rs, 10000, ins=1, prn=False) for rs in range(11,14)]
[zR.Experiment(rs, 10000, ins=2, prn=False) for rs in range(11,14)]
[zR.Experiment(rs, 10000, ins=3, prn=False) for rs in range(11,14)]

"""


import salabim as sim


class INS:
    B = (1, 2, 4, 8)
    I = (2, 5, 6, 2)


def Set_Instance(cho):
    if cho == 0:
        INS.B = (1, 2, 4, 8)
        INS.I = (2, 5, 6, 2)
    if cho == 1:
        INS.B = (1, 2, 4, 8)
        INS.I = (1, 1, 1, 1)
    if cho == 2:
        INS.B = (1, 2, 4, 8)
        INS.I = (2, 4, 6, 4)
    if cho == 3:
        INS.B = ( 1,  2,  4,  8)
        INS.I = (11, 11, 11, 21)


class SIM:
    env = None
    prn = True
    Y   = None  # scheduler
    J   = None  # list of jobs
    M   = None  # resource w capacity
    Q   = None  # resource request queue
    W   = None  # WIP queue
    I   = None  # Idle queue
    fmt_t = "{:5.2f}"
    fmt_jid = "J{:01d}"


def print_curr_time():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")

def print_event(e):
    if SIM.prn:
        print(SIM.fmt_t.format(SIM.env.now()), end=" ")
        print(f"(Avl Req WIP Idl)=({SIM.M.available_quantity()} {len(SIM.Q)} {len(SIM.W)} {len(SIM.I)}) {e}")



class M(sim.Resource):
    pass


class J(sim.Component):
    def __init__(self, idx, busy, idle, *args, **kwargs):
        super().__init__(name=SIM.fmt_jid.format(idx), *args, **kwargs)
        self.idx = idx
        self.busy = busy
        self.idle = idle
        self.n_c = 0

    def process(self):
        B = sim.Exponential(mean=self.busy)
        I = sim.Exponential(mean=self.idle)
        # lambda : sim.random.choice((1, 2, 2, 2, 4, 4))
        SIM.I.add(self)
        while True:
            self.hold(I)
            # print_event(f"{self.name()} about to Request")
            SIM.I.remove(self)
            SIM.Q.add(self)
            # print_event(f"{self.name()} about to Activate Sch")
            SIM.Y.activate()
            # print_event(f"{self.name()} about to Passivate self")
            self.passivate()
            SIM.W.add(self)
            print_event((f"{self.name()} starts task "
                         f"     [{'T' if len(self.claimed_resources())>0 else 'F'}] "
                         f"(Mreq={len(SIM.M.requesters())})"))
            self.hold(B)
            self.n_c += 1
            SIM.W.remove(self)
            SIM.I.add(self)
            self.release()
            print_event(f"{self.name()} complt task")
            SIM.Y.activate()



class Y(sim.Component):
    def process(self):
        msg = {True:"Idle", False:"Busy"}
        while True:
            # print_event(f"Sch activated")
            L1 = len(SIM.Q)
            while len(SIM.Q) and (SIM.M.available_quantity() > 0):
                j = SIM.Q[0]
                print_event(f"Sch {j.name()} Bfr:request (Mreq={len(SIM.M.requesters())})")
                j = SIM.Q.pop()
                # print(f"{j.name()}:{j.status()}")
                j.request(SIM.M)  # granted request activates the job
                # print(f"{j.name()}:{j.status()}")
                print_event(f"Sch {j.name()} Aft:request (Mreq={len(SIM.M.requesters())})")
            L2 = len(SIM.Q)
            # print_event(f"Sch Q:{L1}>{L2}")
            # print_event(f"Sch about to passivate")
            self.passivate()
            

def Experiment(rs, T, ins=0, prn=True):
    SIM.env = sim.Environment(trace=False)
    SIM.env.random_seed(rs)
    SIM.prn = prn
    Set_Instance(ins)

    SIM.M = M("Mechanic", capacity=2)
    SIM.Q = sim.Queue("Requests") # Jobs requesting a resource
    SIM.W = sim.Queue("WIP")      # Jobs in Process (seized a resource)
    SIM.I = sim.Queue("Idle")     # Jobs in idle state
    SIM.Y = Y("Scheduler")
    SIM.J = []
    for j in range(len(INS.B)):
        SIM.J.append(J(idx=j+1, busy=INS.B[j], idle=INS.I[j]))

    print_event("Exp starts")
    SIM.env.run(till=T)
    print_event("Exp ends\n")

    for j in SIM.J:
        j.e_c  = T / (j.busy + j.idle)
        j.e_cc = T / (j.busy + j.idle + SIM.Q.length_of_stay.mean())

    wn = max(SIM.env.math.ceil(SIM.env.math.log10(j.n_c)) for j in SIM.J)
    we = max(SIM.env.math.ceil(SIM.env.math.log10(j.e_c)) for j in SIM.J)
    fn = f"{{:{wn}d}}"
    fe = f"{{:{we+2}.0f}}"

    for j in SIM.J:
        print(f"    {j.name()}:  " + \
              fn.format(j.n_c) + " " + \
              fe.format(j.e_cc) + " " + \
              fe.format(j.e_c))

    print(f"\n   AQT: {SIM.Q.length_of_stay.mean():.3f}")
    

    # SIM.M.available_quantity.print_statistics()
    # SIM.M.claimed_quantity.print_statistics()

    return

