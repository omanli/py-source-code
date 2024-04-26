""" Job Routing Experiment
    Jobs from multiple classes arrive with exponential interarrival times
    Resources are Lifts, Sr_Mechanics, and Jr_Mechanics
    Jobs have class dependent sequence of tasks
    Jobs have class dependent priorities in seizing resources
    Tasks have class dependent (distr of) durations

import <this> as J
reload(J); 
J.SIM.prnlog = False
?J.Set_Instance(1)
?J.JOB.priority = dict(A=1, B=1); J.Run(rs=4, T=2000)
?J.JOB.priority = dict(A=1, B=2); J.Run(rs=4, T=2000)

TODO:
  -use stores/queues to model requests for servers
      https://www.salabim.org/manual/Modelling.html
      https://www.salabim.org/manual/Store.html
  -or use a Queue to wait for a servers (multiple classes (one of the other) at the same time)
      use stores to maintain instances of classes of servers
  -figure out different service times when assigned to 
  different classes of servers
"""

import salabim as sim

class SIM:
    time_unit = 'hours'
    trace = False
    env = sim.Environment(time_unit=time_unit, trace=trace)

from .Util import RV, TU, SNS, Enum

SIM.tu = TU(SIM.env)
SIM.prnlog = True
#
SIM.Arrivals  = None   # job creator components
SIM.Scheduler = None   # scheduler component
SIM.Resource  = None   # list of all resources
#
SIM.ActJobs   = None   # queue to keep all active jobs
#
SIM.Requests  = None   # dict of queues: Task ResRequests
SIM.State_TBS = None   # queue: on_hold
SIM.State_WIP = None   # queue: in_progress
SIM.State_FIN = None   # queue: completed
#
SIM.n_arrivals = None
#
SIM.fmt_jid = "J[{:}{:04d}]"
SIM.fmt_t   = "{:6.2f}"
SIM.fmt_apn = "J[{:}]"
SIM.fmt_res = "{:}{:02d}"



class SHOP:
    resources = '1 2 3 4 5'.split()


class JOB:
    types    = []
    priority = {}
    ia_time  = {}
    tasks    = {}

    types = 'A B'.split()
    priority ['A'] = 1
    priority ['B'] = 2
    # ia_time  ['A'] = RV(SIM.env, 'Exponential', 'hours', 123, 1.1)
    # ia_time  ['B'] = RV(SIM.env, 'Exponential', 'hours', 321, 1.5)
    ia_time  ['A'] = RV(SIM.env, 'ExpRt', 'hours', 123, 1.2)
    ia_time  ['B'] = RV(SIM.env, 'ExpRt', 'hours', 321, 0.8)

    tasks['A'] = [
        SNS(res='1', dur=RV(SIM.env, 'Tri', 'minutes', 333, 20, 30, 40)),
        SNS(res='3', dur=RV(SIM.env, 'Tri', 'minutes', 222, 10, 20, 30)),
        SNS(res='4', dur=RV(SIM.env, 'Tri', 'minutes', 444, 25, 35, 45)),
    ]

    tasks['B'] = [
        SNS(res='2', dur=RV(SIM.env, 'Tri', 'minutes', 300, 20, 30, 40)),
        SNS(res='3', dur=RV(SIM.env, 'Tri', 'minutes', 200, 20, 40, 50)),
        SNS(res='5', dur=RV(SIM.env, 'Tri', 'minutes', 400, 15, 30, 40)),
    ]


def print_time_now():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")


def print_event(e):
    print(SIM.fmt_t.format(SIM.env.now()) + f': {e}')


def print_sys_state(s):
    if SIM.prnlog:
        print_time_now()
        # print(s + " ".join(f"Q[{r}]={len(Q)}" for r,Q in SIM.Requests.items()))
        print(s + " ".join(f"{len(Q):2}" for Q in SIM.Requests.values()))
        print_time_now()
        # print(" "*len(s) + " ".join(f"R[{r}]={len(R.claimers())}" for r,R in SIM.Resource.items()))
        print(" "*len(s) + " ".join(f"{len(R.claimers()):2}" for R in SIM.Resource.values()))

def print_active_jobs(s):
    if SIM.prnlog:
        print_time_now()
        print(s + " ".join(f"{j.name()}" for j in SIM.ActJobs))

def print_arr_event(j):
    if SIM.prnlog:
        print_time_now()
        print(f"Arrival  {j.name()}")


def print_shop_state():
    print("TBD")


class Arrival_Process(sim.Component):
    def __init__(self, job_type, *args, **kwargs):
        super().__init__(name=SIM.fmt_apn.format(job_type), *args, **kwargs)
        self.job_type = job_type

    def process(self):
        while True:
            self.hold(JOB.ia_time[self.job_type])

            SIM.n_arrivals[self.job_type] += 1
            j = Job(job_type = self.job_type, 
                    idx      = SIM.n_arrivals[self.job_type], 
                    t_arr    = SIM.env.now())
            
            # j is automatically activated, no need to explicitly call j.activate()
            # let the new arriving job awake the scheduler SIM.Scheduler.activate()
            SIM.ActJobs.add(j)



class Job(sim.Component):
    def __init__(self, job_type, idx, t_arr, *args, **kwargs):
        super().__init__(name=SIM.fmt_jid.format(job_type, idx), *args, **kwargs)
        self.idx      = idx
        self.job_type = job_type
        self.job_prty = JOB.priority[job_type]
        self.t_arr    = t_arr
        self.t_sta    = None
        self.t_fin    = None

    def process(self):
        print_event(f'{self.name()} arrives')
        for T in JOB.tasks[self.job_type]:
            print_event(f'{self.name()} requests res:{T.res}')
            SIM.Requests[T.res].add(self)
            SIM.Scheduler.activate()
            self.passivate()
            # print(f"{self.name()} dur={t:4.2f}")
            self.request((SIM.Resource[T.res], 1))
            # print(f"{self.name()} dur={t:4.2f}")
            self.hold(T.dur)
            self.release()
        SIM.ActJobs.remove(self)
        print_event(f'{self.name()} departs')




class Scheduler(sim.Component):
    def process(self):
        while True:
            """ -check if at least one Server is available
                -select Server
                -select Job
                -handle Queue
                -assign Job to Server
                -activate Server
            """
            print_sys_state("Sch before scan ")

            # scan Queues & Resources
            for r,Q in SIM.Requests.items():
                if (len(Q) > 0) and len(SIM.Resource[r].claimers()) < SIM.Resource[r].capacity():
                    j = SIM.Requests[r].pop()
                    j.activate()                    
                    # print_event(f"Sch Job[{j.name()}] req {r1:5.3f} {r2:5.3f}")
                    # self.release(SIM.M)

            # self.hold(0.3)
            print_sys_state("Sch after  scan ")
            self.passivate()
            # print_event("Sch[ ] after  passivate")
            """
            while (len(SIM.TBS) == 0) or all(not s.ispassive() for s in SIM.Servers.values()):
                self.passivate()

            s = [s for s in SIM.Servers.values() if s.ispassive()][0]

            j = SIM.TBS.pop()
            SIM.WIP.add(j)
            s.current_job = j
            s.activate()
            """



def Run(rs, T=None, time_unit=None):
    SIM.env = sim.Environment(time_unit=SIM.time_unit, trace=SIM.trace, do_reset=True)
    SIM.env.random_seed(rs)
    time_unit  = SIM.time_unit if time_unit is None else time_unit

    U = sim.Uniform(1000,9999)
    for typ in JOB.types:
        JOB.ia_time[typ].randomstream = sim.random.Random(int(U()))

    SIM.n_arrivals = { 
        j : 0  for j in JOB.types 
    }
    SIM.Arrivals = {
        j : Arrival_Process(job_type=j) for j in JOB.types
    }
    SIM.Resource = {
        r : sim.Resource(name=r, capacity=1) for r in SHOP.resources
    }
    SIM.Requests = {
        r : sim.Queue(name=r) for r in SHOP.resources
    }
    SIM.ActJobs = sim.Queue(name='ActiveJobs')
    SIM.Scheduler = Scheduler()

    # print_sys_state('Run ')
    SIM.env.run(till = T * SIM.tu[time_unit] / SIM.tu[SIM.time_unit])

    print()
    print(f"{'Type':>4s} {'#Arr':>5s} {'#Cmp':>5s} {'AvgST':>6s} {'AvgWT':>6s}")
    for typ in JOB.types:
        nc, AST, AWT = -1, -1, -1
        na = SIM.n_arrivals[typ]
        print(f"{typ:>4s} {na:5d} {nc:5d} {AST:6.2f} {AWT:6.2f}")

    """    
    print(f"\nNum Ev = {SIM.num_events}")
    """

    """
    if (T is None) and (N is None):
        raise ValueError
    SIM.n_max_arrivals = N

    SIM.n_arrivals = {p:0 for p in JOB.types}
    SIM.TBS = sim.Queue(name="Q[TBS]")
    SIM.WIP = sim.Queue(name="Q[WIP]")
    SIM.FIN = sim.Queue(name="Q[FIN]")


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
    """
    
    return

