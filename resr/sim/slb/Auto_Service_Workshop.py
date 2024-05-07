""" Auto Service Workshop
    Jobs from multiple classes arrive with exponential interarrival times
    Resources are Lifts, Sr_Mechanics, and Jr_Mechanics
    Jobs have class dependent sequence of tasks
    Jobs have class dependent priorities in seizing resources
    Tasks have class dependent (distr of) durations

import <this> as ASW
reload(ASW); 
ASW.SIM.prnlog = False
ASW.Set_Instance(1)
?ASW.JOB.priority = dict(A=1, B=1); ASW.Run(rs=4, T=2000)
?ASW.JOB.priority = dict(A=1, B=2); ASW.Run(rs=4, T=2000)

TODO:
  -not a good idea: using .standby() in the Scheduler
   rather than activating the Scheduler from other components
   creates extra calls to the scheduler when the scheduler
   acts on behalf of other components
      https://www.salabim.org/manual/Modelling.html
  -use stores/queues to model requests for servers
      https://www.salabim.org/manual/Modelling.html
      https://www.salabim.org/manual/Store.html
  -or use a Queue to wait for a servers (multiple classes (one of the other) at the same time)
      use stores to maintain instances of classes of servers
  -figure out different service times when assigned to 
  different classes of servers
"""

import salabim as sim

from .Util import RV, TU, SNS, Enum


class SHOP:
    resgroups = {}
    resgroups['Lifts'] = Enum('Lift', 4)
    resgroups['SrMechanics'] = Enum('MechSr', 2)
    resgroups['JrMechanics'] = Enum('MechJr', 4)
    resgroups['Mechanics'] = resgroups['SrMechanics'] + resgroups['JrMechanics']
    resources = resgroups['Lifts'] + resgroups['Mechanics']


class JOB:
    types    = []
    priority = {}
    ia_time  = {}
    tasks    = {}

    types.append('A')
    types.append('B')
    priority ['A'] = 1  # lower value := higher priority
    priority ['B'] = 2
    ia_time  ['A'] = RV('Exponential', 'hours', 123, 1/8)
    ia_time  ['B'] = RV('Exponential', 'hours', 321, 4/8)

    tasks['A'] = [
        SNS(name='Get Lift',
            type='S',   
             res='Lifts',
             dur=None),
        SNS(name='Oil Change',
            type='SDR',
             res='Mechanics',
             dur={'SrMechanics' : RV('Tri', 'minutes', 123, 20, 30, 40),
                  'JrMechanics' : RV('Tri', 'minutes', 231, 25, 35, 50)}),
        SNS(name='Brake Svc',
            type='SDR',
             res='Mechanics', 
             dur={'SrMechanics' : RV('Tri', 'minutes', 222, 20, 25, 30),
                  'JrMechanics' : RV('Tri', 'minutes', 333, 30, 35, 45)}),
        SNS(name='Rls Lift',
            type='R',
             res='Lifts',
             dur=None),
        SNS(name='Test Drive',
            type='SDR', 
             res='SrMechanics', 
             dur={'SrMechanics' : RV('Tri', 'minutes', 444, 25, 30, 35)}),
    ]

    tasks['B'] = [
        SNS(name='Get Lift',
            type='S',   
             res='Lifts',
             dur=None),
        SNS(name='Oil Change',
            type='SDR',
             res='Mechanics',
             dur={'SrMechanics' : RV('Tri', 'minutes', 733, 15, 20, 30),
                  'JrMechanics' : RV('Tri', 'minutes', 622, 20, 25, 35)}),
        SNS(name='Brake Svc',
            type='SDR',
             res='Mechanics', 
             dur={'SrMechanics' : RV('Tri', 'minutes', 421, 25, 35, 40),
                  'JrMechanics' : RV('Tri', 'minutes', 534, 30, 40, 50)}),
        SNS(name='Rls Lift',
            type='R',
             res='Lifts',
             dur=None),
        SNS(name='Test Drive',
            type='SDR', 
             res='SrMechanics', 
             dur={'SrMechanics' : RV('Tri', 'minutes', 355, 15, 25, 30)}),
    ]




class SIM:
    env = None
    time_unit = 'hours'
    trace = False
    prnlog = True
    #
    Arrival_Processes = None  # job creator component
    Scheduler = None   # scheduler component
    Resources = None   # list of all resources
    #
    Requests  = None   # dict of queues: Resource Requests
    #
    n_arrivals = None
    #
    fmt_jid = "J[{:}{:04d}]"
    fmt_t   = "{:.2f}"
    fmt_apn = "J[{:}]"
    fmt_res = "{:}{:02d}"


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


def print_shop_state():
    print("TBD")


class Job(sim.Component):
    def __init__(self, job_type, idx, t_arr, *args, **kwargs):
        super().__init__(name=SIM.fmt_jid.format(job_type, idx), *args, **kwargs)
        self.idx      = idx
        self.job_type = job_type
        self.job_prty = JOB.priority[job_type]
        self.t_arr    = t_arr
        self.t_sta    = None
        self.t_fin    = None

    def process():
        pass
        """ -add self to TBS queue   (state)
            -add self to Lifts queue (request)
        """

class Arrival_Process(sim.Component):
    def __init__(self, job_type, *args, **kwargs):
        super().__init__(name=SIM.fmt_apn.format(job_type), *args, **kwargs)
        self.job_type     = job_type

    def process(self):
        while True:
            self.hold(JOB.ia_time[self.job_type])

            SIM.n_arrivals[self.job_type] += 1
            j = Job(job_type = self.job_type, 
                    idx      = SIM.n_arrivals[self.job_type], 
                    t_arr    = SIM.env.now())
            SIM.TBS.add_sorted(component=j, priority=j.job_prty)
            
            print_arr_event(j)

            SIM.Scheduler.activate()



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
            while (len(SIM.TBS) == 0) or all(not s.ispassive() for s in SIM.Servers.values()):
                self.passivate()

            s = [s for s in SIM.Servers.values() if s.ispassive()][0]

            j = SIM.TBS.pop()
            SIM.WIP.add(j)
            s.current_job = j
            s.activate()



def Run(rs, T=None, N=None):
    """
    SIM.env = sim.Environment(time_unit=SIM.time_unit, trace=SIM.trace)
    SIM.env.random_seed(rs)

    tu  = SIM.time_unit if tu is None else tu

    if rsg is None:
        g = SIM.env.Uniform(1000,9999)
        rsg = [g() for _ in range(1,21)]

    SIM.env.run(till=T*SIM.tu)
    
    print(f"\nNum Ev = {SIM.num_events}")

    

    if (T is None) and (N is None):
        raise ValueError
    SIM.n_max_arrivals = N

    SIM.n_arrivals = {p:0 for p in JOB.types}
    SIM.TBS = sim.Queue(name="Q[TBS]")
    SIM.WIP = sim.Queue(name="Q[WIP]")
    SIM.FIN = sim.Queue(name="Q[FIN]")

    SIM.env = sim.Environment(time_unit=SIM.time_unit, trace=SIM.trace)
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
    """
    
    return


