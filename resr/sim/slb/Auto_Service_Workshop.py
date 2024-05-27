""" Auto Service Workshop
    Jobs from multiple classes arrive with exponential interarrival times
    Resources are Lifts, Sr_Mechanics, and Jr_Mechanics
    Jobs have class dependent sequence of tasks
    Jobs have class dependent priorities in seizing resources
    Tasks have class dependent (distr of) durations

import <this> as ASW
reload(ASW); 
ASW.SIM.print_log = True
ASW.Run(123, 3)
ASW.Run(None, 3)
ASW.SIM.Requests["Lifts"].print_info()

cd Documents/py/sim/slb/
D = ASW.Read_Instance('Model_v1.yaml')


TODO:
-- Sim Output write to File
-- Implement Replications
-- Implement Warm Up Period
[] Report Utilization Stats
[] Report WIP Stats
[] Report Waiting Time Stats

TODO:
  - If more than one type of resource is available to a Request 
       decide which one to allocate
  - Among multiple Requests that can be honored select which ones 
       to respond to

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
from Util import RV, TU, SNS, Enum, dirm
import yaml

SIM  = SNS()
SHOP = SNS()
JOB  = SNS()


SIM.time_unit = 'hours'
SIM.trace = False
SIM.env = sim.Environment(time_unit=SIM.time_unit, trace=SIM.trace)

SIM.print_log = False
#
SIM.Arrival_Processes = None  # job creator component
SIM.Scheduler = None   # scheduler component
SIM.Resource  = None   # dict of all resources
SIM.Requests  = None   # queue of all Resource Requests
SIM.System    = None   # queue of all jobs currently in the Shop
#
SIM.Arrivals = None    # list of all jobs arrived
SIM.n_arrivals = None
#
SIM.fmt_jid = "J[{:}{:04d}]"
SIM.fmt_t   = "{:.2f}"
SIM.fmt_apn = "J[{:}]"
SIM.fmt_res = "{:}{:02d}"






def print_time_now():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")


def print_job_state(j, m):
    if SIM.print_log:
        print_time_now()
        print(f"{j.name()} {m}")


def print_srv_state(s, m, j):
    if SIM.print_log:
        print_time_now()
        print(f"{s} {m}  {j.name()}  ")


def print_sch_state(s, j):
    if SIM.print_log:
        print_time_now()
        print(f"Sch[{s}] {j.name()}  ")


def print_arr_event(j):
    if SIM.print_log:
        print_time_now()
        print(f"{j.name()} Arrives")


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
        self.WT       = []
        self.rsgr_req = None
        self.resr_asg = None
        self.resr_acq = [None]*len(JOB.tasks[job_type])
        self.wip      = None
        self.task     = []

    def process(self):
        SIM.Arrivals.append(self)
        SIM.System.add(self)
        self.wip = False

        for T in JOB.tasks[self.job_type]:
            assert self not in SIM.Requests
            assert self.rsgr_req is None
            assert self.resr_asg is None
            self.task.append(SNS())
            self.task[-1].job_type = T.type
            self.task[-1].res_grp  = T.rsgr
            self.WT.append(0)
            
            print_job_state(self, f"{T.name:19} [{T.rsgr}]")

            # Seize 
            if 'S' in T.type:
                self.rsgr_req = T.rsgr
                self.task[-1].t_s_req = SIM.env.now()
                SIM.Requests.add_sorted(component=self, priority=self.job_prty)
                t_req = SIM.env.now()
                SIM.Scheduler.activate()
                self.passivate()
                self.WT[-1] = SIM.env.now() - t_req 
                self.task[-1].t_s_acq = SIM.env.now()
                self.rsgr_req = None
                assert self.resr_asg is not None
                self.resr_acq[T.ridx] = self.resr_asg
                self.resr_asg = None
                print_job_state(self, 
                    "Acquired Resources: [" + \
                    " ".join(r.name() for r in self.claimed_resources()) + "]")

            # Delay 
            if 'D' in T.type:
                self.wip = True
                self.task[-1].t_d_sta = SIM.env.now()
                print_job_state(self, 
                    (f"Delay on Resource:  "
                     f"[{self.resr_acq[T.ridx].name()}"
                     f" {SHOP.rtyp[self.resr_acq[T.ridx].name()]}]"))
                self.hold(T.dur[SHOP.rtyp[self.resr_acq[T.ridx].name()]])
                self.wip = False
                self.task[-1].t_d_fin = SIM.env.now()

            # Release
            if 'R' in T.type:
                print_job_state(self, 
                    f"Releasing Resource: [{self.resr_acq[T.ridx].name()}]")
                self.task[-1].t_r = SIM.env.now()
                self.release(self.resr_acq[T.ridx])
                assert self.resr_asg is None
                SIM.Scheduler.activate()

        self.t_fin = SIM.env.now()
        SIM.System.remove(self)



class Scheduler(sim.Component):
    def process(self):
        while True:
            """ -iterate over requests
                -try to assign resources to high priority 
            """
            if SIM.print_log:
                print_time_now()
                print(" [Schdl] Activates")
            for j in SIM.Requests:
                # print(f"    {j.name()} " + (j.rsgr_req if j.rsgr_req is not None else "--"))
                for r in SHOP.ResourceGroups[j.rsgr_req]:
                    if SIM.Resource[r].available_quantity() > 0:
                        SIM.Requests.remove(j)
                        assert j.resr_asg is None
                        j.resr_asg = SIM.Resource[r]
                        j.request(SIM.Resource[r])
                        break
            self.passivate()
            """
            if (len(Reqs) > 0) and ():
                print(f"{rg:>13} Req:" + \
                  " ".join(f"{sum(1 for j in Reqs 
                             if j.job_type == jt):2}" 
                             for jt in JOB.types), end=" ")
                print(" Avl:" + \
                  " ".join(f"{SIM.Resource[Res].available_quantity():2}" 
                           for Res in SHOP.ResourceGroups[rg]))
                print(SIM.Resource)
            while (len(SIM.TBS) == 0) or all(not s.ispassive() for s in SIM.Servers.values()):
                self.passivate()
            s = [s for s in SIM.Servers.values() if s.ispassive()][0]
            j = Req.pop()
            """



def Read_Instance(fn):
    global SHOP, JOB, SIM

    with open(fn, 'r') as yf:
        D = yaml.safe_load(yf.read())

    sim_fields = """
        time_unit 
        sim_length 
        random_seed
        trace
    """.split()

    for fld in sim_fields:
        setattr(SIM, fld, D['RUN'][fld])

    SHOP = SNS(**D['SHOP'])
    JOB  = SNS(**D['JOB'])

    IAT = {}
    for typ,par in JOB.ia_time.items():
        p = par.split()
        IAT[typ] = RV(SIM.env, p[0], p[1], int(p[2]), *(float(x) for x in p[3:]))
    # JOB.ia_time = SNS(**IAT)
    # JOB.priority = SNS(**JOB.priority)
    JOB.ia_time = IAT
    JOB.priority = JOB.priority
    for T,L in JOB.tasks.items():
        JOB.tasks[T] = [SNS(**V) for V in L]
        for X in JOB.tasks[T]:
            if isinstance(X.dur, dict):
                for r,par in X.dur.items():
                    p = par.split()
                    X.dur[r] = RV(SIM.env, p[0], p[1], int(p[2]), *(float(x) for x in p[3:]))
            if X.dur == "None":
                X.dur = None

    for T in SHOP.ResourceTypes.keys():
        SHOP.ResourceTypes[T] = SHOP.ResourceTypes[T].split()
    for T in SHOP.ResourceGroups.keys():
        SHOP.ResourceGroups[T] = SHOP.ResourceGroups[T].split()

    SHOP.Resources = [R for T in SHOP.ResourceTypes.values() for R in T]

    SHOP.rtyp = {r:t for t,R in SHOP.ResourceTypes.items() for r in R}

    return



def Run_Instance():
    if SIM.time_unit not in "hours minutes days seconds years".split():
        raise ValueError(f"Invalid SIM.time_unit={SIM.time_unit!r}")

    # convert sim_length to env default time unit
    T = getattr(SIM.env, SIM.time_unit)(SIM.sim_length)

    Run(SIM.random_seed, T)



def Run(rs, T):
    if rs is None:
        rs = SIM.random_seed

    SIM.env = sim.Environment(time_unit=SIM.time_unit, trace=SIM.trace, do_reset=True)

    if rs is not None:
        SIM.env.random_seed(rs)
        for rv in JOB.ia_time.values():
            r = SIM.env.random.randint(1000,9999)
            rv.randomstream = SIM.env.random.Random(r)
        for JT in JOB.tasks.values():
            for TT in JT:
                if TT.dur is not None:
                    for dd in TT.dur.values():
                        r = SIM.env.random.randint(1000,9999)
                        dd.randomstream = SIM.env.random.Random(r)

    SIM.Scheduler = Scheduler()

    SIM.Arrival_Processes = {
        j : Arrival_Process(job_type=j)
        for j in JOB.types
    }

    SIM.Resource = {
        r : sim.Resource(name=f"{r}", capacity=1)
        for r in SHOP.Resources
    }

    SIM.System   = sim.Queue(name=f"System")
    SIM.Requests = sim.Queue(name=f"Requests")

    SIM.Arrivals = []
    SIM.n_arrivals = { p:0 for p in JOB.types }

    SIM.env.run(till=T)



    print()
    print((f"{'Type':>12s} {'#Arr':>6s} {'#Cmp':>6s} {'#WIP':>6s} "
           f"{'AST':>6} {'AWT':>6} {'ATT':>6} {'NiS':>6}"))
    AWR = { typ:{r:0 for r in SHOP.ResourceGroups.keys()} for typ in JOB.types}
    for typ in JOB.types:
        na = SIM.n_arrivals[typ]
        nc = sum(1 for j in SIM.Arrivals if (j.job_type == typ) and (j.t_fin is not None))

        n = 0
        AST, AWT, ATT, NiS = 0, 0, 0, 0
        for j in SIM.Arrivals:
            if (j.job_type == typ):
                NiS += (j.t_fin - j.t_arr) if j.t_fin else (T - j.t_arr)
            if (j.job_type == typ) and (j.t_fin is not None):
                n += 1
                AST += j.t_fin - j.t_arr
                for tt in j.task:
                    if "S" in tt.job_type:
                        AWT += tt.t_s_acq - tt.t_s_req
                        AWR[typ][tt.res_grp] += tt.t_s_acq - tt.t_s_req
                for tt in j.task:
                    if "D" in tt.job_type:
                        ATT += tt.t_d_fin - tt.t_d_sta
        n = 1 if n == 0 else n
        AST = AST / n
        AWT = AWT / n
        ATT = ATT / n
        for rg in SHOP.ResourceGroups.keys():
            AWR[typ][rg] /= n
        NiS = NiS / T

        print((f"{typ:>12s} {na:6d} {nc:6d} {na-nc:6d} " 
               f"{AST:6.2f} {AWT:6.2f} {ATT:6.2f} {NiS:6.2f}"))
    print()

    print(f"{' ':>12s} " + " ".join(f"{rg[:6]:>6s}" for rg in SHOP.ResourceGroups.keys()))
    for typ in JOB.types:
        print(f"{typ:>12}", end=" ")
        for rg in SHOP.ResourceGroups.keys():
            print(f"{AWR[typ][rg]:6.2f}", end=" ")
        print()
    print()

    print(f"{' ':>12s} {'Util':>6s}")
    for Typ,RL in SHOP.ResourceTypes.items():
        Utl = sum(SIM.Resource[R].occupancy.mean() for R in RL) / len(RL)
        print(f"{Typ:>12} {100*Utl:5.1f}%")
    print()

    print(f"{'System':>12s}")
    print(f"{'Len of Stay':>12} {SIM.System.length_of_stay.mean():6.2f}")
    print(f"{'Num in Sys':>12} {SIM.System.length.mean():6.2f}")

    return
