""" Priority Queue

    
    import <this> as PQ
    reload(PQ); 
    PQ.Run(rs=42, T=None, N=50)
"""

import salabim as sim

slb_Environment = sim.Environment
slb_Component = sim.Component
slb_Queue = sim.Queue
Gamma = sim.random.gammavariate
Uniform = sim.random.uniform
Exponential = sim.random.expovariate



class SIM:
    env = None
    Arrival_Processes = None
    Scheduler = None
    Servers = None
    trace = False
    prnlog = True
    #
    TBS = None  # on_hold
    WIP = None  # in_progress
    FIN = None  # completed
    #
    p_job_types = None
    p_job_priority = None
    p_arr_rate = None
    #
    n_arrivals = None
    n_max_arrivals = None
    #
    fmt_jid = "J{:}{:04d}"
    fmt_t   = "{:.2f}"
    fmt_apn = "AP[{:}]"


def print_time_now():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")


def print_sch_state(s, j):
    if SIM.prnlog:
        print_time_now()
        print((f"Sch[{s}] "
               f"{j.name()}  "
               f"TBS={len(SIM.TBS)}  "
               f"WIP={len(SIM.WIP)}  "
               f"FIN={len(SIM.FIN)}  "))


def print_arr_event(j):
    if SIM.prnlog:
        print_time_now()
        print((f"Arrival  {j.name()}  "
               f"TBS={len(SIM.TBS)}  "
               f"WIP={len(SIM.WIP)}  "
               f"FIN={len(SIM.FIN)}  "))



class Job(slb_Component):
    def __init__(self, job_type, idx, t_arr, *args, **kwargs):
        super().__init__(name=SIM.fmt_jid.format(job_type, idx), *args, **kwargs)
        self.idx      = idx
        self.job_type = job_type
        self.t_arr    = t_arr
        self.t_sta    = None
        self.t_fin    = None



class Arrival_Process(slb_Component):
    def __init__(self, job_type, arrival_rate, *args, **kwargs):
        super().__init__(name=SIM.fmt_apn.format(job_type), *args, **kwargs)
        self.job_type     = job_type
        self.arrival_rate = arrival_rate

    def process(self):
        while True:
            t = Exponential(self.arrival_rate)
            self.hold(t)

            if SIM.n_max_arrivals:
                if sum(SIM.n_arrivals.values()) >= SIM.n_max_arrivals:
                    break

            SIM.n_arrivals[self.job_type] += 1
            j = Job(job_type = self.job_type, 
                    idx      = SIM.n_arrivals[self.job_type], 
                    t_arr    = SIM.env.now())
            SIM.TBS.add(j)

            print_arr_event(j)

            if SIM.Scheduler.ispassive():
                SIM.Scheduler.activate()



class Server(slb_Component):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.current_job = None

    def process(self):
        while True:
            while self.current_job is None:
                self.passivate()

            j = self.current_job
            svc_time = Exponential(1 / SIM.p_svc_time[j.job_type])

            j = SIM.TBS.pop()
            j.t_sta = SIM.env.now()
            SIM.WIP.add(j)
            self.hold(svc_time)
            SIM.WIP.remove(j)
            j.t_fin = SIM.env.now()
            SIM.FIN.add(j)

            self.current_job = None

            if SIM.Scheduler.ispassive():
                SIM.Scheduler.activate()



class Scheduler(slb_Component):
    def process(self):
        while True:
            while (len(SIM.TBS) == 0) or all(not s.ispassive() for s in SIM.Servers.values()):
                self.passivate()

            s = [s for s in SIM.Servers.values() if s.ispassive()][0]
            s.current_job = SIM.TBS[0]
            s.activate()


            """
            -check if at least Server available
            -select Server
            -select Job
            -handle Queue
            -assign Job to Server
            -activate Server
            """

            """
            j = SIM.TBS.pop()
            j.t_sta = SIM.env.now()
            SIM.WIP.add(j)

            if SIM.prnlog:
                print_sch_state("sta", j)

            self.hold(3)

            SIM.WIP.remove(j)
            j.t_fin = SIM.env.now()
            SIM.FIN.add(j)

            if SIM.prnlog:
                print_sch_state("fin", j)
            """



def Run(rs, T=None, N=None):
    if (T is None) and (N is None):
        raise ValueError
    SIM.n_max_arrivals = N

    SIM.p_job_types = ['A', 'B']
    SIM.p_job_priority = dict(A=2, B=1)
    SIM.p_arr_rate = dict(A=0.2, B=0.5)
    SIM.p_svc_time = dict(A=2.0, B=1.0)

    SIM.n_arrivals = {p:0 for p in SIM.p_job_types}
    SIM.TBS = slb_Queue(name="Q[TBS]")
    SIM.WIP = slb_Queue(name="Q[WIP]")
    SIM.FIN = slb_Queue(name="Q[FIN]")

    SIM.env = slb_Environment(trace=SIM.trace)
    SIM.env.random_seed(rs)

    SIM.Scheduler = Scheduler()
    SIM.Arrival_Processes = {
        j : Arrival_Process(
              job_type     = j, 
              arrival_rate = SIM.p_arr_rate[j]
            )
        for j in SIM.p_job_types
    }
    SIM.Servers = {
        s : Server(name = s)
        for s in ['S01']
    }

    if T is not None:
        SIM.env.run(till=T)
    else:
        SIM.env.run()

    print("\n", "Num Arrivals:", sep="")
    for p,n in SIM.n_arrivals.items():
        print(f"  {p}={n}")

    if SIM.prnlog:
        for Q in "TBS WIP FIN".split():
            print("\n", f"{Q}:", sep="")
            for j in getattr(SIM, Q):
                print((f"  {j.name()} "
                       f"{SIM.fmt_t.format(j.t_arr)} "
                       f"{SIM.fmt_t.format(j.t_sta if j.t_sta else 0)} "
                       f"{SIM.fmt_t.format(j.t_fin if j.t_fin else 0)} "))

    return

