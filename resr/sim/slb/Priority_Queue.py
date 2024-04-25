""" Priority Queue
    Job classes arrive with Exp. interarrival times
    Multiple servers with Exp. service times

import <this> as PQ
reload(PQ); 
PQ.Run(rs=42, T=None, N=50)

reload(PQ); 
PQ.SIM.prnlog = False
PQ.Set_Instance(1)
PQ.JOB.priority = dict(A=1, B=1); PQ.Run(rs=4, T=2000)
PQ.JOB.priority = dict(A=1, B=2); PQ.Run(rs=4, T=2000)

TODO:
  -random seed for each Arr.Process     (each Job Type)
  -random seed for each Svc.Time distr. (each Job Type)
  -better Instance setting function     
      num_servers
      num_job_types
      priorities
      partial WL values
      frequencies (granularity)
      target Utilization value
"""

import salabim as sim

slb_Environment = sim.Environment
slb_Component = sim.Component
slb_Queue = sim.Queue
Gamma = sim.random.gammavariate
Uniform = sim.random.uniform
Exponential = sim.random.expovariate


class JOB:
    types = ['A', 'B']
    priority = dict(A=1, B=2)
    arr_rate = dict(A=0.2, B=0.5)
    svc_time = dict(A=2.0, B=1.0)


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
    n_servers = 1
    n_arrivals = None
    n_max_arrivals = None
    #
    fmt_jid = "J{:}{:04d}"
    fmt_t   = "{:.2f}"
    fmt_apn = "AP[{:}]"
    fmt_svn = "S{:02d}"


def print_time_now():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")


def print_srv_state(s, m, j):
    if SIM.prnlog:
        print_time_now()
        print((f"{s} {m}  "
               f"{j.name()}  "
               f"TBS={len(SIM.TBS)}  "
               f"WIP={len(SIM.WIP)}  "
               f"FIN={len(SIM.FIN)}  "))


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
        self.job_prty = JOB.priority[job_type]
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
            SIM.TBS.add_sorted(component=j, priority=j.job_prty)
            
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
            svc_time = Exponential(1 / JOB.svc_time[j.job_type])
            j.t_sta = SIM.env.now()
            print_srv_state(self.name(), "sta", j)

            self.hold(svc_time)

            SIM.WIP.remove(j)
            SIM.FIN.add(j)
            j.t_fin = SIM.env.now()
            print_srv_state(self.name(), "fin", j)

            self.current_job = None

            if SIM.Scheduler.ispassive():
                SIM.Scheduler.activate()



class Scheduler(slb_Component):
    def process(self):
        while True:
            """ -check if at least one Server is available
                -select Server
                -select Job
                -handle Queue
                -assign Job to Server
                -activate Server
            """
            while (len(SIM.TBS) == 0) or all(not s.ispassive() for s in SIM.Servers.values()):
                self.passivate()

            s = [s for s in SIM.Servers.values() if s.ispassive()][0]

            j = SIM.TBS.pop()
            SIM.WIP.add(j)
            s.current_job = j
            s.activate()



def Analyze_Instance(cho):
    Set_Instance(cho)
    if (set(JOB.types) ^ set(JOB.priority.keys())) or \
       (set(JOB.types) ^ set(JOB.arr_rate.keys())) or \
       (set(JOB.types) ^ set(JOB.svc_time.keys())):
        raise ValueError("Job classes not consistent with Priorities, Arr.Rt, or Svc.Rt.")
    WL = sum(JOB.arr_rate[t]*JOB.svc_time[t] for t in JOB.types)
    U = WL / SIM.n_servers
    print(f"   WorkLoad = {WL:.3f}")
    print(f"          s = {SIM.n_servers}")
    print(f"Utilization = {U:.3f}")
    return



def Set_Instance(cho):
    if cho == 1:
        SIM.n_servers = 1
        JOB.types = ['A', 'B']
        JOB.priority = dict(A=1, B=2)
        JOB.arr_rate = dict(A=0.2, B=0.5)
        JOB.svc_time = dict(A=2.0, B=1.0)
        return
    if cho == 2:
        SIM.n_servers = 2
        JOB.types = ['A', 'B']
        JOB.priority = dict(A=1, B=2)
        JOB.arr_rate = dict(A=0.5, B=1.0)
        JOB.svc_time = dict(A=1.8, B=0.8)
        return
    if cho == 3:
        SIM.n_servers = 3
        JOB.types = ['A', 'B']
        JOB.priority = dict(A=1, B=2)
        JOB.arr_rate = dict(A=0.2, B=0.6)
        JOB.svc_time = dict(A=4.0, B=3.0)
        return
    raise ValueError(f"Invalid choice cho={cho}")
    


def Run(rs, T=None, N=None):
    if (T is None) and (N is None):
        raise ValueError
    SIM.n_max_arrivals = N

    SIM.n_arrivals = {p:0 for p in JOB.types}
    SIM.TBS = slb_Queue(name="Q[TBS]")
    SIM.WIP = slb_Queue(name="Q[WIP]")
    SIM.FIN = slb_Queue(name="Q[FIN]")

    SIM.env = slb_Environment(trace=SIM.trace)
    SIM.env.random_seed(rs)

    SIM.Scheduler = Scheduler()
    SIM.Arrival_Processes = {
        j : Arrival_Process(
              job_type     = j, 
              arrival_rate = JOB.arr_rate[j]
            )
        for j in JOB.types
    }
    servers = (SIM.fmt_svn.format(i) for i in range(1,SIM.n_servers+1))
    SIM.Servers = {
        s : Server(name = s)
        for s in servers
    }

    if T is not None:
        SIM.env.run(till=T)
    else:
        SIM.env.run()

    if SIM.prnlog:
        for Q in "TBS WIP FIN".split():
            print("\n", f"{Q}:", sep="")
            for j in getattr(SIM, Q):
                print((f"  {j.name()} "
                       f"{SIM.fmt_t.format(j.t_arr)} "
                       f"{SIM.fmt_t.format(j.t_sta if j.t_sta else 0)} "
                       f"{SIM.fmt_t.format(j.t_fin if j.t_fin else 0)} "))

    print()
    print(f"{'Type':>4s} {'#Arr':>5s} {'#Cmp':>5s} {'AvgST':>6s} {'AvgWT':>6s}")
    for typ in JOB.types:
        ST = [(j.t_fin - j.t_sta) for j in SIM.FIN if j.job_type == typ]
        WT = [(j.t_sta - j.t_arr) for j in SIM.FIN if j.job_type == typ]
        na = SIM.n_arrivals[typ]
        nc = len(ST)
        AST = sum(ST) / nc
        AWT = sum(WT) / nc
        print(f"{typ:>4s} {na:5d} {nc:5d} {AST:6.2f} {AWT:6.2f}")

    return

