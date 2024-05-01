""" Auto Service Workshop
    Jobs from multiple classes arrive with exponential interarrival times
    Resources are Lifts, Sr_Mechanics, and Jr_Mechanics
    Jobs have class dependent sequence of tasks
    Jobs have class dependent priorities in seizing resources
    Tasks have class dependent (distr of) durations

import <this> as ASW
reload(ASW); 
ASW.SIM.prnlog = True
ASW.Run(123, 3)
ASW.Run(None, 3)
ASW.SIM.Requests["Lifts"].print_info()


TODO:
  - Task Dur should depend on ResGr of claimed resource
  - If type resources are available to a Request decide
    which one to allocate


  - not a good idea: using .standby() in the Scheduler
    rather than activating the Scheduler from other components
    creates extra calls to the scheduler when the scheduler
    acts on behalf of other components
       https://www.salabim.org/manual/Modelling.html
  - use stores/queues to model requests for servers/resources
       Requests as sim.Queue()
       https://www.salabim.org/manual/Modelling.html
       https://www.salabim.org/manual/Store.html
  - or use a Queue to wait for a servers (multiple classes (one of the other) at the same time)
       use stores to maintain instances of classes of servers
       or make model servers as sim.Resource()
  - figure out different service times when assigned to 
    different classes of servers
"""

import salabim as sim

class SIM:
    time_unit = 'hours'
    trace = False
    env = sim.Environment(time_unit=time_unit, trace=trace)

from .Util import RV, TU, SNS, Enum

SIM.prnlog = True
#
SIM.Arrival_Processes = None  # job creator component
SIM.Scheduler = None   # scheduler component
SIM.Resource  = None   # dict of all resources
SIM.Requests  = None   # queue of all Resource Requests
#
SIM.Arrivals = None    # list of all jobs arrived
SIM.n_arrivals = None
#
SIM.fmt_jid = "J[{:}{:04d}]"
SIM.fmt_t   = "{:.2f}"
SIM.fmt_apn = "J[{:}]"
SIM.fmt_res = "{:}{:02d}"


class SHOP:
    restype = {}
    restype['Lift']   = Enum('Lift',   4)
    restype['SrMech'] = Enum('SrMech', 3)
    restype['JrMech'] = Enum('JrMech', 4)

    rtyp = { r:t for t,R in restype.items() for r in R }

    resgroup = {}
    resgroup['Lifts']       = restype['Lift']
    resgroup['SrMechanics'] = restype['SrMech']
    resgroup['JrMechanics'] = restype['JrMech']
    resgroup['Mechanics']   = restype['SrMech'] + restype['JrMech']

    resources = resgroup['Lifts'] + resgroup['SrMechanics'] + resgroup['JrMechanics']



class JOB:
    types    = []
    priority = {}
    ia_time  = {}
    tasks    = {}

    types.append('A')
    types.append('B')
    priority ['A'] = 'A'  # lower value := higher priority
    priority ['B'] = 'B'
    ia_time  ['A'] = RV(SIM.env, 'ExpRt', 'hours', 123, 1.2)
    ia_time  ['B'] = RV(SIM.env, 'ExpRt', 'hours', 123, 2.2)

    tasks['A'] = [
        SNS(name='Get Lift',
            type='S',   
            rsgr='Lifts',
             dur=None),
        SNS(name='Oil Change',
            type='SDR',
            rsgr='Mechanics',
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 123, 20, 30, 40),
                  'JrMech' : RV(SIM.env, 'Tri', 'minutes', 231, 25, 35, 50)}),
        SNS(name='Brake Svc',
            type='SDR',
            rsgr='Mechanics', 
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 222, 20, 25, 30),
                  'JrMech' : RV(SIM.env, 'Tri', 'minutes', 333, 30, 35, 45)}),
        SNS(name='Rls Lift',
            type='R',
            rsgr='Lifts',
             dur=None),
        SNS(name='Test Drive',
            type='SDR', 
            rsgr='SrMechanics', 
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 444, 25, 30, 35)}),
    ]

    tasks['B'] = [
        SNS(name='Get Lift',
            type='S',   
            rsgr='Lifts',
             dur=None),
        SNS(name='Oil Change',
            type='SDR',
            rsgr='Mechanics',
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 733, 15, 20, 30),
                  'JrMech' : RV(SIM.env, 'Tri', 'minutes', 622, 20, 25, 35)}),
        SNS(name='Brake Svc',
            type='SDR',
            rsgr='Mechanics', 
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 421, 25, 35, 40),
                  'JrMech' : RV(SIM.env, 'Tri', 'minutes', 534, 30, 40, 50)}),
        SNS(name='Rls Lift',
            type='R',
            rsgr='Lifts',
             dur=None),
        SNS(name='Test Drive',
            type='SDR', 
            rsgr='SrMechanics', 
             dur={'SrMech' : RV(SIM.env, 'Tri', 'minutes', 355, 15, 25, 30)}),
    ]


def print_time_now():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")


def print_job_state(j, m):
    if SIM.prnlog:
        print_time_now()
        print(f"{j.name()} {m}")


def print_srv_state(s, m, j):
    if SIM.prnlog:
        print_time_now()
        print(f"{s} {m}  {j.name()}  ")


def print_sch_state(s, j):
    if SIM.prnlog:
        print_time_now()
        print(f"Sch[{s}] {j.name()}  ")


def print_arr_event(j):
    if SIM.prnlog:
        print_time_now()
        print(f"{j.name()} Arrives")


def print_shop_state():
    print("TBD")



class Arrival_Process(sim.Component):
    def __init__(self, job_type, *args, **kwargs):
        super().__init__(name=SIM.fmt_apn.format(job_type), *args, **kwargs)
        self.job_type     = job_type

    def process(self):
        while True:
            self.hold(JOB.ia_time[self.job_type])

            SIM.n_arrivals[self.job_type] += 1

            j = Job(job_type = self.job_type, 
                    idx      = SIM.n_arrivals[self.job_type])
            
            print_arr_event(j)



class Job(sim.Component):
    def __init__(self, job_type, idx, *args, **kwargs):
        super().__init__(name=SIM.fmt_jid.format(job_type, idx), *args, **kwargs)
        self.idx      = idx
        self.job_type = job_type
        self.job_prty = JOB.priority[job_type]
        self.t_arr    = SIM.env.now()
        self.t_fin    = None
        self.rsgr_req = None

    def process(self):
        SIM.Arrivals.append(self)

        for T in JOB.tasks[self.job_type]:
            assert self not in SIM.Requests
            assert self.rsgr_req is None

            print_job_state(self, f"{T.name:12} [{T.rsgr}]")

            # Seize 
            if 'S' in T.type:
                self.rsgr_req = T.rsgr
                SIM.Requests.add_sorted(component=self, priority=self.job_prty)
                SIM.Scheduler.activate()
                self.passivate()
                self.rsgr_req = None
                print_job_state(self, "acquired resources: [" + " ".join(r.name() for r in self.claimed_resources()) + "]")

            # Delay 
            if 'D' in T.type:
                self.hold(T.dur[list(T.dur.keys())[0]])

            # Release
            if 'R' in T.type:
                for r in self.claimed_resources():
                    # print("------  ", r.name(), " ".join(r for r in SHOP.resgroup[T.rsgr]))
                    if r.name() in SHOP.resgroup[T.rsgr]:
                        print_job_state(self, f"releasing resource: [{r.name()}]")
                        self.release(r)
                        SIM.Scheduler.activate()

        self.t_fin = SIM.env.now()



class Scheduler(sim.Component):
    def process(self):
        while True:
            """ -iterate over requests
                -try to assign resources to high priority 
            """
            print_time_now()
            print()
            for j in SIM.Requests:
                print(f"    {j.name()} " + (j.rsgr_req if j.rsgr_req is not None else "--"))
                for r in SHOP.resgroup[j.rsgr_req]:
                    if SIM.Resource[r].available_quantity() > 0:
                        SIM.Requests.remove(j)
                        j.request(SIM.Resource[r])
                        break
            self.passivate()
            """
            if (len(Reqs) > 0) and ():
                print(f"{rg:>13} Req:" + " ".join(f"{sum(1 for j in Reqs if j.job_type == jt):2}" for jt in JOB.types), end=" ")
                print(" Avl:" + " ".join(f"{SIM.Resource[Res].available_quantity():2}" for Res in SHOP.resgroup[rg]))
                print(SIM.Resource)
            while (len(SIM.TBS) == 0) or all(not s.ispassive() for s in SIM.Servers.values()):
                self.passivate()
            s = [s for s in SIM.Servers.values() if s.ispassive()][0]
            j = Req.pop()
            """



def Run(rs, T):

    SIM.env = sim.Environment(time_unit=SIM.time_unit, trace=SIM.trace, do_reset=True)

    if rs is not None:
        SIM.env.random_seed(rs)
        for rv in JOB.ia_time.values():
            r = SIM.env.random.randint(1000,9999)
            rv.randomstream = SIM.env.random.Random(r)

    SIM.Scheduler = Scheduler()

    SIM.Arrival_Processes = {
        j : Arrival_Process(job_type=j)
        for j in JOB.types
    }

    SIM.Resource = {
        r : sim.Resource(name=f"{r}", capacity=1)
        for r in SHOP.resources
    }

    SIM.Requests = sim.Queue(name=f"Requests")
    """
    SIM.Requests = {
        r : sim.Queue(name=f"Req{r}")
        for r in SHOP.resgroup
    }
    """

    SIM.Arrivals = []
    SIM.n_arrivals = { p:0 for p in JOB.types }

    SIM.env.run(till=T)

    print()
    print(f"{'Type':>4s} {'#Arr':>5s}") 
    # "{'#Cmp':>5s} {'AvgST':>6s} {'AvgWT':>6s}")
    for typ in JOB.types:
        # nc, AST, AWT = -1, -1, -1
        # "{nc:5d} {AST:6.2f} {AWT:6.2f}"
        na = SIM.n_arrivals[typ]
        print(f"{typ:>4s} {na:5d}") 

    """
    [f"{j.name()} {j.claimed_resources()} for j in ASW.SIM.Arrivals]
    [ for j in ASW.SIM.Arrivals]
    [j.t_fin for j in ASW.SIM.Arrivals]
    """


    """
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
