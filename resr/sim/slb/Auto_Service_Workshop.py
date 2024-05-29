""" Auto Service Workshop
    Jobs from multiple classes arrive with exp. i-arrival times
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
[] Implement Warm Up Period
[] Report Utilization Stats
[] Report WIP Stats
[] Report Waiting Time Stats

TODO:
  - If more than one type of resource is available to a Request 
       decide which one to allocate
  - Among multiple Requests that can be honored select which one(s) 
       to respond to
"""

import salabim as sim
from .Util import RV, TU, SNS, Enum, dirm
import yaml

inf = float('inf')


SIM  = SNS()
SHOP = SNS()
JOB  = SNS()


SIM.time_unit = 'hours'
SIM.trace = False
SIM.env = sim.Environment(time_unit=SIM.time_unit, 
                          trace=SIM.trace)

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
        super().__init__(name=SIM.fmt_apn.format(job_type), 
                         *args, **kwargs)
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
        super().__init__(name=SIM.fmt_jid.format(job_type, idx), 
                         *args, **kwargs)
        self.idx      = idx
        self.job_type = job_type
        self.job_prty = JOB.priority[job_type]
        self.t_arr    = SIM.env.now()
        self.t_dep    = inf
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
            self.WT.append(inf)
            
            print_job_state(self, f"{T.name:19} [{T.rsgr}]")

            # Seize 
            if 'S' in T.type:
                self.rsgr_req = T.rsgr
                self.task[-1].t_s_req = SIM.env.now()
                SIM.Requests.add_sorted(component=self, 
                                        priority=self.job_prty)
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

        self.t_dep = SIM.env.now()
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
                for r in SHOP.ResourceGroups[j.rsgr_req]:
                    if SIM.Resource[r].available_quantity() > 0:
                        SIM.Requests.remove(j)
                        assert j.resr_asg is None
                        j.resr_asg = SIM.Resource[r]
                        j.request(SIM.Resource[r])
                        break
            self.passivate()



def Read_Instance(fn):
    global SHOP, JOB, SIM

    with open(fn, 'r') as yf:
        D = yaml.safe_load(yf.read())

    sim_fields = """
        time_unit
        sim_length
        wup_length
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
        IAT[typ] = RV(SIM.env, p[0], p[1], int(p[2]), 
                      *(float(x) for x in p[3:]))
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
                    X.dur[r] = RV(SIM.env, p[0], p[1], int(p[2]), 
                                  *(float(x) for x in p[3:]))
            if X.dur == "None":
                X.dur = None

    for T in SHOP.ResourceTypes.keys():
        SHOP.ResourceTypes[T] = SHOP.ResourceTypes[T].split()
    for T in SHOP.ResourceGroups.keys():
        SHOP.ResourceGroups[T] = SHOP.ResourceGroups[T].split()

    SHOP.Resources = [R for T in SHOP.ResourceTypes.values() 
                        for R in T]

    SHOP.rtyp = {r:t for t,R in SHOP.ResourceTypes.items() 
                     for r in R}

    return



def Run_Instance():
    if SIM.time_unit not in "hours minutes days seconds years".split():
        raise ValueError(f"Invalid SIM.time_unit={SIM.time_unit!r}")

    # convert sim_length to env default time unit
    T = getattr(SIM.env, SIM.time_unit)(SIM.sim_length)
    W = getattr(SIM.env, SIM.time_unit)(SIM.wup_length)

    Run(rs=SIM.random_seed, T=T, W=W)
    m = Calculate_Metrics(T=T, W=W)
    Print_Metrics(m)



def Run(rs, T, W=0):
    if rs is None:
        rs = SIM.random_seed

    SIM.env = sim.Environment(time_unit=SIM.time_unit, 
                              trace=SIM.trace, 
                              do_reset=True)

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

    if W > 0:
        SIM.env.run(till=W)
        [m.reset() for R in SIM.Resource.values() for m in R.all_monitors()]
        [m.reset() for m in SIM.System.all_monitors()]
        [m.reset() for m in SIM.Requests.all_monitors()]

    SIM.env.run(till=T)

    return


def Print_Metrics(m):
    print(("\n" f"{'Type':>12s} {'#Arr':>6s} {'#Cmp':>6s} {'#WIP':>6s} "
           f"{'AST':>6} {'AWT':>6} {'ATT':>6} {'NiS':>6}"))
    for t in JOB.types:
        print((f"{t:>12s} " 
               f"{m.n_arr[t]:6d} {m.n_dep[t]:6d} {m.n_arr[t]-m.n_dep[t]:6d} " 
               f"{m.Avg_Sys_Time[t]:6.2f} "
               f"{m.Avg_Wait_Time[t]:6.2f} "
               f"{m.Avg_Task_Time[t]:6.2f} "
               f"{m.Avg_Num_in_Sys[t]:6.2f}"))

    print(("\n" f"{' ':>12s} {'Util':>6s}"))
    for rt in SHOP.ResourceTypes.keys():
        print((f"{rt:>12} "
               f"{100*m.Utilization[rt]:5.1f}%"))

    print(("\n" f"{' ':>12s} ") + \
          " ".join(f"{rg[:6]:>6s}" for rg in SHOP.ResourceGroups.keys()))
    for t in JOB.types:
        print(f"{t:>12}", end=" ")
        for rg in SHOP.ResourceGroups.keys():
            print(f"{m.Avg_Wait_Res[t][rg]:6.2f}", end=" ")
        print()
    print()



def Calculate_Metrics(T, W=0):
    o = SNS()
    o.n_arr          = {typ:0 for typ in JOB.types}
    o.n_dep          = {typ:0 for typ in JOB.types}
    o.n_sys          = {typ:0 for typ in JOB.types}
    o.Utilization    = {}
    o.Avg_Sys_Time   = {typ:0 for typ in JOB.types}
    o.Avg_Wait_Time  = {typ:0 for typ in JOB.types}
    o.Avg_Task_Time  = {typ:0 for typ in JOB.types}
    o.Avg_Num_in_Sys = {typ:0 for typ in JOB.types}
    o.Avg_Wait_Res   = {typ:{r:0 for r in SHOP.ResourceGroups.keys()} for typ in JOB.types}


    for typ, Res in SHOP.ResourceTypes.items():
        o.Utilization[typ] = sum(SIM.Resource[R].occupancy.mean() 
                                 for R in Res) / len(Res)
    
    for j in SIM.Arrivals:
        o.n_arr[j.job_type] += 1

        if j.t_dep < inf:
            o.n_dep[j.job_type] += 1

        if W < j.t_dep:
            o.Avg_Num_in_Sys[j.job_type] += min(T, j.t_dep) - max(W, j.t_arr)

        if W < j.t_dep < inf:
            o.Avg_Sys_Time[j.job_type] += j.t_dep - j.t_arr
            o.n_sys[j.job_type] += 1

        if W < j.t_dep < inf:
            for tt in j.task:
                if 'S' in tt.job_type and tt.t_s_acq:
                    o.Avg_Wait_Time[j.job_type] += tt.t_s_acq - tt.t_s_req
                    o.Avg_Wait_Res[j.job_type][tt.res_grp] += tt.t_s_acq - tt.t_s_req
                if 'D' in tt.job_type:
                    o.Avg_Task_Time[j.job_type] += tt.t_d_fin - tt.t_d_sta

    non_zero = lambda x : x if x > 0 else 1

    for typ in JOB.types:
        o.Avg_Num_in_Sys[typ] /= T - W
        o.Avg_Sys_Time[typ]   /= non_zero(o.n_sys[typ])
        o.Avg_Wait_Time[typ]  /= non_zero(o.n_sys[typ])
        o.Avg_Task_Time[typ]  /= non_zero(o.n_sys[typ])

    for typ in JOB.types:
        for rtyp, Res in SHOP.ResourceGroups.items():
            o.Avg_Wait_Res[typ][rtyp] /= non_zero(o.n_sys[typ])

    return o

