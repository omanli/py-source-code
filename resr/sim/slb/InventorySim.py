"""
MTO Inventory Simulation
  Inventory - Raw Materials procurement and consumption is simulated
  Production of Semi Finished Goods and Finished Goods is omitted
  (single level BOM, final product requires a list of materials)
  (assembly process of final product is ignored)

Order of Events: (rewrite) 
  Event at time t (state value effective right continous)
  Inventory of Material 
  Demand Order Arrivals
  Production Order Release consumes Inventory 
  Purchase Quantity arrives after Lead Time
  Purchase Order Arrival replenishes Inventory

terminology:
  Demand Arrival
  Purchase Order
  Production Order
"""

# A General Production/Inventory Simulation:
"""
 -Production Policy (handling Production Orders e.g. top down vs bottom up)
 -Queueing Policy (handling parts to be processed at queues of machines or workstations)
 -Inventory Policy (Purchase Policy + Production Order Release)
 -Fulfillment Policy (partial shipping vs full order)
"""


# Implement 
"""
PurchaseOrder InterArrival Time Distributions  
  E=Exponential
  U=Uniform
  C=Constant (?)
  B=Beta (?)
  G=Gamma (?)
  W=Weibull (?)
  L=Lognormal (?)
  T=Triangular (?)
    Truncated Normal (?)
SimInstance better __repr__

PeriodicReview Events can be made Class Based
  tPR = [  5       5      10        20    ]
  cPR = [  A       B       C         D    ]
  mPR = [[0..1]  [2..5]  [6..10]  [11..15]]
invoke Inventory Review for the whole class
handle order/skip decisions for all members (products/parts) of the class


"""


# salabim logic
'''
salabim:
  end simulation depending on state, number of occurances of a certain type of event, or total sim time
    env.main().activate()

  process: Arrival of Demand  (1 object per Product instance used throughout the whole simulation)
     loop: schedule next arrival + apply arrival

  process: Review of Inventory      (1 object instance per SKU class used throughout the whole simulation)
     loop: review & create purchase orders when necessary

  process: Purchase Order           (multiple instances, 1 per purchase, allow overlapping and variable lead time)
     loop: issue+arrival  

  trigger: everytime a new Sales Order arrives 
       do: check for possible Production Order release while updating the inventory

  trigger: everytime a Purchase Order Arrives or simulation starts initially
       do: check for all possible Production Order releases
           keep on checking&releasing until not possible due to lack of inventory while updating the inventory

'''


# sample code / how to run
''' 
import InventorySim as S
reload(S);
O = S.RunPy(S.Ins,T=200,rs=123); S.PltOut(O)
O = S.RunPy(S.Ins,T=30,rs=123); S.PltOut(O)
S.PrnEvv(S.Out.Evv);

reload(S); S.RunSlb(Ins, N=11,  rs=2); S.PltOut(Sim.Out)
reload(S); S.RunSlb(Ins, T=200, rs=1); S.PltOut(S.Sim.Out)
S.Stats(S.Sim.Out)   

reload(S); S.Test1(); S.Analyze(S.Ins[2], S.Out[2])

reload(S); S.Out = S.RunSlb(Ins, T=300, rs=3); S.PltInv(S.Out)
[S.Out[3].Inv[2].v[i:i+6] for i in range(4,80,6)]
[S.Out[3].Inv[3].v[i:i+6] for i in range(4,80,6)]
[S.Out[3].Inv[6].v[i:i+9] for i in range(84,180,9)]
[S.Out[3].Inv[7].v[i:i+6] for i in range(14,100,6)]
S.SnapOut(S.Out[-1],300)  


I = S.BuildInstance(S.InstanceCase("01x01"))
reload(S); 
S.RunSlb(I, T=200, rs=1)
S.PltOut(S.Sim.Out)
S.Stats(S.Sim.Out)

'''






import numpy as np
import numpy.random as rnd
import matplotlib.pyplot as plt
import salabim as sim


class Trajectory:
    """
    t : time epochs of the trajectory
    v : value of the trajectory at time epoch (right continous)
    """
    def __init__(self, N, rsz=None):
        self.t = np.zeros(N, dtype=float)
        self.v = np.zeros(N, dtype=int)
        self.c = 0
        if rsz is None:
            rsz = N
        self.rsz = rsz
    def add(self, t, v):
        self.t[self.c] = t
        self.v[self.c] = v
        self.c += 1
        if self.c == self.t.size:
            self.t.resize(self.c+self.rsz)
            self.v.resize(self.c+self.rsz)
    def ext(self, t):
        if self.t[self.c-1] < t:
            self.t[self.c] = t
            self.v[self.c] = self.v[self.c-1]
            self.c += 1
    def trunc(self):
        self.t.resize(self.c)
        self.v.resize(self.c)


class SimOutput:
    def __init__(self, N, nProd, nMtrl):
        self.Blg = [Trajectory(N) for i in range(nProd)]
        self.Inv = [Trajectory(N) for i in range(nMtrl)]
        self.EvB = [Trajectory(N) for i in range(nProd)]
        self.Evv = []


class SimInstance:
    """
    default time unit = day
         default rate = per day
    """
    def __init__(self):
        self.nProd    = None   # number of products                          (int)
        self.nMtrl    = None   # number of materials                         (int)
        self.LProd    = None   # labels of products                          (list of str)
        self.LMtrl    = None   # labels of materials                         (list of str)
        self.BOM      = None   # BOM recipe quantities                       (dict of lists, keys={Prd}+{range()})
        self.MTBO     = None   # Mean Time b/w Orders [days/Order]           (list of int/float)
        self.InitBlg  = None   # Initial Backlog (Demand Orders)             (list of int)
        self.InitInv  = None   # Initial Inventory Level of Materials [SKU]  (list of int)
        self.Price    = None   # Purchase Price of Materials                 (list of int)
        self.LeadTime = None   # Purchase Lead Time of Materials  [days]     (list of int)
        self.StckClss = None   # Material Inventory Control Class [.]        (list of .)
        self.RvwPrd   = None   # Review Period of Stock Classes   [days]     (list of int)
        self.OrdUpTo  = None   # Order Up to Level of Inventory   [SKU]      (list of int)
        """
        self.LClss    = None   # Inventory Control Class Labels
        self.ClssRP   = None   # Inventory Control Class Review Periods
        self.ICClss   = None   # Inventory Control Class of Materials
        """

    def __str__(self):
        # called by print
        s = []
        s.append(f"nP = {self.nProd}")
        s.append(f"nM = {self.nMtrl}")
        s.extend(["BOM   " + "".join([f"{m:>4}" for m in self.LMtrl])])
        s.extend([(f"   {p:>3}" + "".join([f" {v:3}" if v>0 else "   -" for v in self.BOM[p]])) for p in self.LProd])
        # return str(self.__class__) + ".str()"
        return "\n".join(s)

    def __repr__(self):
        # called by object dump
        return str(self.__class__) + ".repr()"


def InstanceCase(cho="05x16"):
    S = lambda T : [s.strip() for s in T if len(s.split()) > 0]
    I = dict(BOM=None, par=None)

    if cho == "05x16":
        BOMstr = """\
                  BOM M01 M02 M03 M04 M05 M06 M07 M08 M09 M10 M11 M12 M13 M14 M15 M16
                  P01  3   -   4   -   -   -   2   -   -   -   -   1   -   -   -   -
                  P02  2   -   -   1   -   -   2   1   -   -   -   -   2   -   -   -
                  P03  2   -   -   2   -   -   -   1   2   -   -   -   -   2   -   -
                  P04  -   4   -   -   2   -   -   -   -   3   -   -   -   -   1   -
                  P05  -   2   -   -   -   3   -   -   -   -   2   -   -   -   -   1
        """.splitlines()
        parstr = """\
          prodparam    P01 P02 P03 P04 P05 
          MTbwOrders     4   6  12  15  20
          InitBacklog    1   2   3   0   0
          #
          mtrlparam    M01 M02 M03 M04 M05 M06 M07 M08 M09 M10 M11 M12 M13 M14 M15 M16
          InitInv        9  12   6   6   6  12   6   3   6   6  12  20  30  15  10  10
          PrchPrice     20  16  10   8   6   6   4   3   3   2   2   1   1   1   1   1
          LeadTime       3   3   2   2   2   2   4   2   4   3   2   6   6   6   6   6
          StockClass     A   A   B   B   B   C   C   C   C   C   D   D   D   D   D   D
          InvRvwPrd      5   5   5   5   5   5  10  10  10  10  10  20  20  20  20  20
          InvOrdUpTo    60  30  60  20  10  15  60  20  15  25  15  40  50  25  15  10
        """.splitlines()
        I["BOM"] = S(BOMstr)
        I["par"] = S(parstr)
    elif cho == "01x01":
        BOMstr = """\
                  BOM M01
                  P01  1 
        """.splitlines()
        parstr = """\
          prodparam    P01
          MTbwOrders     4
          InitBacklog    0
          #
          mtrlparam    M01
          InitInv       20
          PrchPrice      1
          LeadTime      30
          StockClass     A
          InvRvwPrd     70
          InvOrdUpTo    40
        """.splitlines()
        I["BOM"] = S(BOMstr)
        I["par"] = S(parstr)
    else:
        raise ValueError(f"Invalid cho={cho}")

    return I


def BuildInstance(InsTxt):
    def isi(s):
        try: 
            int(s)
            return True
        except ValueError:
            return False

    SI = SimInstance()

    SI.LMtrl = InsTxt["BOM"][0].split()[1:]
    SI.LProd = [s.split()[0] for s in InsTxt["BOM"][1:]]
    SI.nProd, SI.nMtrl = len(SI.LProd), len(SI.LMtrl)

    SI.BOM = dict()
    for s in InsTxt["BOM"][1:]:
        r = s.split()
        assert len(r) == SI.nMtrl+1, "BOM matrix string number of columns inconsistent"
        SI.BOM[r[0]] = [0 if x=="-" else int(x) for x in r[1:]]
    for i,p in enumerate(SI.LProd):
        SI.BOM[i] = SI.BOM[p]

    for p in InsTxt["par"]:
        h = p.split()[0]
        d = [x for x in p.split()[1:]]
        v = [int(x) if isi(x) else None for x in p.split()[1:]]
        if h == "MTbwOrders":  SI.MTBO = v
        if h == "InitBacklog": SI.InitBlg = v
        if h == "InitInv":     SI.InitInv = v
        if h == "PrchPrice":   SI.Price = v
        if h == "StockClass":  SI.StckClss = d
        if h == "LeadTime":    SI.LeadTime = v
        if h == "InvRvwPrd":   SI.RvwPrd = v
        if h == "InvOrdUpTo":  SI.OrdUpTo = v

    assert len(SI.MTBO)     == SI.nProd, "Mean Time b/w Orders dimension inconsistent"
    assert len(SI.InitBlg)  == SI.nProd, "Initial Backlog dimension inconsistent"
    assert len(SI.InitInv)  == SI.nMtrl, "Initial Inventory dimension inconsistent"
    assert len(SI.Price)    == SI.nMtrl, "Purchase Price dimension inconsistent"
    assert len(SI.StckClss) == SI.nMtrl, "Stock Class dimension inconsistent"
    assert len(SI.LeadTime) == SI.nMtrl, "Lead Time dimension inconsistent"
    assert len(SI.RvwPrd)   == SI.nMtrl, "Inventory Review Period dimension inconsistent"
    assert len(SI.OrdUpTo)  == SI.nMtrl, "Inventory Order Up To Level dimension inconsistent"

    return SI



def RunPy(Ins, N, rs=1):
    """
    Parameters
       N : stopping criteria (cum.num.of all events or only demand arrivals?)
       M : number of materials
       P : number of products

    Simulation State
       t : current simulation time
     Inv : Inventory Levels
     Blg : Order Backlogs
     tAr : Demand Arrival Times
     tRv : Next Periodic Review Time
     tPD : List of Purchase Delivery Times
     iPD : List of Purchase Delivery Inventory Indices
     qPD : List of Purchase Delivery Quantities

    Sim Vars
     m,p : loop vars
     evt : imminent event type
     ett : imminent event time
     qIR : Inventory Check (Inv/Req)
           Production Order Available (mtrl release to start new Prod.Order possible)

    Bookkeeping
    narr : total number of Arrival events 
       O : simulation state output
    """

    # parameters
    P,M = Ins.nProd,Ins.nMtrl
    rP,rM = range(P),range(M)

    # sim state initialization
    rnd.seed(rs)
    t = 0.0
    Inv = Ins.InitInv.copy()
    Blg = Ins.InitBlg.copy()
    tDA = np.array([rnd.exponential(a) for a in Ins.MTBO])
    tPR = Ins.RvwPrd.copy()
    # make tPD, qPD (add iPD) variable length queues to handle:
    # -periodic review with LT > RvwPrd
    # -continuous review with multiple In Transit Orders of same material type
    tPD = [np.Inf for m in rM]
    qPD = [None for m in rM]

    # book keeping
    narr = 0
    O = SimOutput(2*N+1,P,M)
    [O.Blg[p].add(t,Blg[p]) for p in rP]
    [O.Inv[m].add(t,Inv[m]) for m in rM]
    
    # crude event log
    E = []

    while narr < N:
        # 
        # check for available production orders
        while True:
            qIR = [min([int(np.floor(Inv[m]/Ins.BOM[p][m])) 
                        for m in rM if Ins.BOM[p][m] > 0]) 
                   for p in rP]
            # select max Backlog with enough Inventory to release at least one kit
            sc = sorted([(b,i) for i,b in enumerate(Blg) if qIR[i]>0 and Blg[i]>0], 
                        key=lambda x:(x[0],-x[1]), 
                        reverse=True)
            if not sc:
                break
            p = sc[0][1]
            if False:
                print("Inv :", Inv)
                print("Blg :", Blg)
                print("qIR :", qIR)
                print("      (Blg,qIR) :", [(b,i) for i,b in enumerate(Blg) if qIR[i]>0 and Blg[i]>0])
                print("sorted(Blg,qIR) :", sc)
                print("p :", p)
            # release Inv of selected Product
            Inv = [Inv[m]-Ins.BOM[p][m] for m in rM]
            Blg[p] -= 1
            [O.Inv[m].add(t,Inv[m]) for m,v in enumerate(Ins.BOM[p]) if v>0]
            O.Blg[p].add(t,Blg[p])
            O.EvB[p].add(t,-1)

        # 
        # find the imminent event and event time
        # tPD does not handle continuous review if multiple InTransit Orders of the same material are possible
        svt = [min(tDA), min(tPR), min(tPD)]
        s = np.argmin(svt)
        evt, ett = ["DA","PR","PD"][s], svt[s]

        # bookkeep:
        #   DA : arriving order prod type
        #   PR : purchase orders & mtrl type
        #   PD : purchase delivery qty & mtrl type

        # (Demand Arrival) Product Order Arrival 
        if evt == "DA":
            # handle Blg
            t = ett
            narr += 1
            p = np.argmin(tDA)
            Blg[p] += 1
            tDA[p] = ett + rnd.exponential(Ins.MTBO[p])
            O.Blg[p].add(ett,Blg[p])
            O.EvB[p].add(ett,+1)
            E.append([ett, "DemArr", [p]])

        # (Periodic Review) Inventory Periodic Review
        if evt == "PR":
            # handle tPD, iPD, qPD
            t = ett
            sm = [m for m in rM if tPR[m]<=ett]
            assert np.all([tPD[m] == np.Inf for m in sm]), "Inv Review on In Transit material (tPD)"
            assert np.all([qPD[m] is None for m in sm]),  "Inv Review on In Transit material (qPD)"
            tPR = [(ett+Ins.RvwPrd[m]) if m in sm else tPR[m] for m in rM]
            if False:
                print("PRvw :", sm)
                print(" tPR : [" + ", ".join(["{:2.0f}".format(x) for x in tPR]) + "]")
            so = [m for m in rM if (m in sm) and (Ins.OrdUpTo[m]-Inv[m])>0]
            tPD = [(ett+Ins.LeadTime[m])   if m in so else tPD[m] for m in rM]
            qPD = [(Ins.OrdUpTo[m]-Inv[m]) if m in so else qPD[m] for m in rM]
            E.append([ett, "InvRvw", sm])
            E.append([ett, "PrcOrd", so])

        # (Procurement/Purchase Arrival) Purchased Material Delivery
        if evt == "PD":
            # handle tPD, iPD, qPD
            t = ett
            sm = [m for m in rM if tPD[m]<=ett]
            so = [m for m in sm if qPD[m]>0]
            assert len([m for m in rM if tPD[m]<=ett and qPD[m]<=0]) == 0, "Prc Qty zero (tPD)"
            if False:
                print("  PD :", sm)
            # print(" tPR : [" + ", ".join(["{:2.0f}".format(x) for x in tPR]) + "]")
            tPD = [np.Inf if m in sm else tPD[m] for m in rM]
            Inv = [Inv[m]+(qPD[m] if m in sm else 0) for m in rM]
            qPD = [None   if m in sm else qPD[m] for m in rM]
            [O.Inv[m].add(ett,Inv[m]) for m in rM if m in sm]
            E.append([ett, "PrcArr", sm])


    # extend all trajectories to t terminal simulation time
    [O.Blg[p].ext(t) for p in rP]
    [O.Inv[m].ext(t) for m in rM]
    # truncate all trajectories 
    [O.Blg[p].trunc() for p in rP]
    [O.EvB[p].trunc() for p in rP]
    [O.Inv[m].trunc() for m in rM]

    # add Events log to Output
    O.Evv = E

    return O





def ReleasePO(loginv=False):
    # check for available production orders
    while True:
        # calculate maximum Prod.Orders that can be released for each P
        mxPO = [min([int(np.floor(Sim.Inv[m]/Sim.Ins.BOM[p][m])) 
                     for m in Sim.rM if Sim.Ins.BOM[p][m] > 0]) 
                for p in Sim.rP]
        # select max Backlog with enough Inventory to release at least one kit
        sc = sorted([(b,i) for i,b in enumerate(Sim.Blg) if mxPO[i]>0 and Sim.Blg[i]>0], 
                    key=lambda x:(x[0],-x[1]), 
                    reverse=True)
        # indices of Stock Out product types
        so = [(b,i) for i,b in enumerate(Sim.Blg) if mxPO[i]==0 and Sim.Blg[i]>0]
        if not sc:
            # no available Prod.Orders
            break
        else:
            # release the product with max backlog
            p = sc[0][1]
        # release one Prod.Order: decrease Backlog by one, decrease Inv by BOM
        for m in Sim.rM:
            if Sim.Ins.BOM[p][m] > 0:
                Sim.Inv[m] -= Sim.Ins.BOM[p][m]
                Sim.Out.Inv[m].add(Sim.env.now(),Sim.Inv[m])
        Sim.Blg[p] -= 1
        if loginv:
            Sim.Out.Blg[p].add(Sim.env.now(),Sim.Blg[p])
        Sim.Out.EvB[p].add(Sim.env.now(),-1)
        Sim.Out.Evv.append([Sim.env.now(), "PrdOrd", [p]])


class DemandArrival(sim.Component):
    def setup(self, part_type, mean_time):
        self.iar_time_dist = sim.Exponential(mean=mean_time)
        self.prod_type = part_type
    def process(self):
        while True:
            yield self.hold(self.iar_time_dist.sample())
            Sim.Blg[self.prod_type] += 1
            Sim.nAr[self.prod_type] += 1
            Sim.Out.EvB[self.prod_type].add(Sim.env.now(),+1)
            Sim.Out.Evv.append([Sim.env.now(), "DemArr", [self.prod_type]])
            if sum(Sim.nAr) >= Sim.N:
                Sim.env.main().activate()
            ReleasePO(False)
            Sim.Out.Blg[self.prod_type].add(Sim.env.now(),Sim.Blg[self.prod_type])


class InventoryReview(sim.Component):
    def setup(self, m, p):
        self.period = p
        self.materials = m
    def process(self):
        while True:
            yield self.hold(self.period)
            Sim.Out.Evv.append([Sim.env.now(), "InvRvw", self.materials])
            for m in self.materials:
                oq = Sim.Ins.OrdUpTo[m] - Sim.Inv[m] - sum([po.ordr_qnty for po in Sim.PurOrd if po.mtrl_type == m]) 
                if oq > 0:
                    Sim.PurOrd.append(PurchaseOrder(mtrl=m, ordr_qnty=oq, lead_time=Sim.Ins.LeadTime[m]))


class PurchaseOrder(sim.Component):
    def setup(self, mtrl, ordr_qnty, lead_time):
        self.mtrl_type = mtrl
        self.ordr_qnty = ordr_qnty
        self.lead_time = lead_time
    def process(self):
        Sim.Out.Evv.append([Sim.env.now(), "PrcOrd", [self.mtrl_type]])
        yield self.hold(self.lead_time)
        Sim.Inv[self.mtrl_type] += self.ordr_qnty
        Sim.PurOrd.remove(self)
        Sim.Out.Inv[self.mtrl_type].add(Sim.env.now(),Sim.Inv[self.mtrl_type])
        Sim.Out.Evv.append([Sim.env.now(), "PrcArr", [self.mtrl_type]])
        ReleasePO(True)


class Sim():
    """
    This class is a data class (namespace) for the Simulation State, Objects, and Bookkeeping
 
    Instance & Parameters
      Ins : model instance
        M : number of materials
        P : number of products
       rM : range object to iterate Materials
       rP : range object to iterate Products
  
    System State
      Inv : Inventory Levels
      Blg : Order Backlogs
  
    Simulation Vars
      m,p : loop vars
      qIR : Inventory Check (Inv/Req)
            Production Order Available (mtrl release to start new Prod.Order possible)
  
    Bookkeeping
        N : stopping criteria (cum.num. of demand arrivals)
      nAr : number of demand arrivals
      Out : simulation state output
      Evv : crude event log

    Simulation Objects
      env    : simulation environment object
      Demand : static list of Demand Arrival Process objects
      InvRvw : static list of Inventory Review Process objects
      PurOrd : dynamic list of Purchase Order objects
    """

    Ins = None
    M, P, rM, rP = None, None, None, None
    Inv = None
    Blg = None
    N   = None    
    nAr = None    
    Out = None
    Evv = None

    env = None
    Demand = None  # static list of Demand Arrival Process objects
    InvRvw = None  # static list of Inventory Review Process objects
    PurOrd = None  # dynamic list of Purchase Order objects


def RunSlb(Ins, N=None, T=None, rs=1, trace=False):
    """
    Simulation 
    -Set up
    -Run
    -Output
    """
    if N is None and T is None:
        raise ValueError(f"Both N={N} and T={T} cannot be defaulted")
    if T is None:
        T = sim.inf

    # instance & parameters
    Sim.Ins = Ins
    Sim.P, Sim.M = Ins.nProd, Ins.nMtrl
    Sim.rP, Sim.rM = range(Sim.P),range(Sim.M)

    # state
    Sim.Inv = Ins.InitInv.copy()
    Sim.Blg = Ins.InitBlg.copy()

    # book keeping
    Sim.N = sim.inf if N is None else N 
    Sim.T = T
    Sim.nAr = [0] * Sim.P
    os = 2*sum([1+T//m for m in Sim.Ins.MTBO]) if N is None else N
    Sim.Out = SimOutput(os,Sim.P,Sim.M)
    [Sim.Out.Blg[p].add(0,Sim.Blg[p]) for p in Sim.rP]
    [Sim.Out.Inv[m].add(0,Sim.Inv[m]) for m in Sim.rM]
    Sim.Out.Evv = []

    # objects
    Sim.env = sim.Environment(trace=trace)
    sim.random_seed(seed=rs)
    Sim.Demand = [DemandArrival(part_type=p, mean_time=Sim.Ins.MTBO[p]) for p in Sim.rP]
    Sim.InvRvw = [InventoryReview(m=[m for m in Sim.rM if Sim.Ins.RvwPrd[m] == v], p=v)
                  for v in set(Sim.Ins.RvwPrd)]
    Sim.PurOrd = []

    ReleasePO(True)
    Sim.env.run(till=T)
    # ?how to setup monitors/statistics with salabim

    # extend all trajectories to t terminal simulation time    
    [Sim.Out.Blg[p].ext(Sim.env.now()) for p in Sim.rP]
    [Sim.Out.Inv[m].ext(Sim.env.now()) for m in Sim.rM]
    # truncate all trajectories
    [Sim.Out.Blg[p].trunc() for p in Sim.rP]
    [Sim.Out.EvB[p].trunc() for p in Sim.rP]
    [Sim.Out.Inv[m].trunc() for m in Sim.rM]

    return Sim.Out



def PrnEvv(E, t1=None, t2=None):
    t1 = 0 if t1 is None else t1
    t2 = np.inf if t2 is None else t2
    for e in E:
        if t1 <= e[0] <= t2:
            print(f"{e[0]:7.3f}  {e[1]}", end="  ")
            print("["+" ".join([f"{x:2}" for x in e[2]])+"]")


def Check(O):
    # time chronology (monotonously nondecreasing)
    vi = [len(np.where(I.t[1:] - I.t[:-1] < 0)[0]) for I in O.Inv]
    vb = [len(np.where(B.t[1:] - B.t[:-1] < 0)[0]) for B in O.Blg]
    print("time chronology violations:")
    print("  Inv.t", vi)
    print("  Blg.t", vb)


def SnapOut(O,t):
    ii = [np.where(I.t <= t)[0][-1] for I in O.Inv]
    jj = [np.where(B.t <= t)[0][-1] for B in O.Blg]
    for m,(I,i) in enumerate(zip(O.Inv,ii)):
        assert I.t[i] <= t <= I.t[(i+1) if i+1<I.t.size else i], "find O.Inv[{m}].t[{i}] out of time window"
    for p,(B,j) in enumerate(zip(O.Blg,jj)):
        assert B.t[j] <= t <= B.t[(j+1) if j+1<B.t.size else j], "find O.Inv[{p}].t[{j}] out of time window"
    print(f"  t ={t:5.2f}")
    print( "Blg =" + "["+" ".join([f"{B.v[j]:2}" for j,B in zip(jj,O.Blg)])+"]")
    print( "Inv =" + "["+" ".join([f"{I.v[i]:2}" for i,I in zip(ii,O.Inv)])+"]")


def PltOut(O,fno=None):
    if fno is None:
        fig = plt.figure(1)
    else:
        fig = plt.figure(fno)
    fig.clf()
    fig.set_size_inches(9.3, 6.2)
    fig.tight_layout(pad=1.06)
    lf,tp,wd,ht = plt.get_current_fig_manager().window.geometry().getRect()
    plt.get_current_fig_manager().window.setGeometry(400, 32, wd, ht)
    plt.subplots_adjust(left=0.06, right=0.99, bottom=0.04, top=0.98, wspace=0.0, hspace=0.09)

    ax = plt.subplot(211)
    plt.ylabel("Backlog")
    plt.xlabel("")
    [plt.step(B.t, B.v, where="post",linestyle="-") for B in O.Blg]
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymin=0)

    ax = plt.subplot(212)
    plt.ylabel("Inventory")
    plt.xlabel("Time")
    [plt.step(I.t, I.v, where="post",linestyle="-") for I in O.Inv]
    ax.set_xlim(xmin=0)
    ax.set_ylim(ymin=0)


def PltInv(O,fno=None):
    if fno is None:
        fig = plt.figure(1)
    else:
        fig = plt.figure(fno)
    fig.clf()
    fig.set_size_inches(9.3, 6.2)
    fig.tight_layout(pad=1.06)
    lf,tp,wd,ht = plt.get_current_fig_manager().window.geometry().getRect()
    plt.get_current_fig_manager().window.setGeometry(400, 32, wd, ht)
    plt.subplots_adjust(left=0.06, right=0.99, bottom=0.04, top=0.98, wspace=0.0, hspace=0.09)

    for m,I in enumerate(O.Inv):
        ax = plt.subplot(len(O.Inv),1,m+1)
        if m == len(O.Inv)//2:
            plt.ylabel("Inventory")
        if m == len(O.Inv):
            plt.xlabel("Time")
        else:
            plt.xlabel("")
            ax.set_xticks([])
        plt.step(I.t, I.v, where="post",linestyle="-")
        ax.set_xlim(xmin=0)
        ax.set_ylim(ymin=0)
        # ax.set_xticklabels()
    return ax


def Performance(Ins,Out):
    pass


def Analyze(Ins, O=None):
    # Analyze Balance b/w Material Consumption & Inventory Replenishment Rate
    #   OUL RvwPrd OrdRt Inv
    
    # dRt : demand (depletion) rate
    # dOu : order up to level in demand days
    # dRP : ratio of review period to order up to level in demand days
    dRt, dOu, dRP = [0.0]*Ins.nMtrl, [0.0]*Ins.nMtrl, [0.0]*Ins.nMtrl
    # nOrd   : number of Orders
    # nStOut : number of Stock Outs
    # AvgBlg : Avg. Backlog
    nOrd, nStOut, AvgBlg = [0]*Ins.nProd, [0]*Ins.nProd, [0]*Ins.nProd
    # AvgInv : Avg Inventory (holding)
    AvgInv = [0]*len(O.Inv)

    for m in range(Ins.nMtrl):
        dRt[m] = sum([Ins.BOM[p][m]/Ins.MTBO[p] for p in range(Ins.nProd)])
        dOu[m] = Ins.OrdUpTo[m] / dRt[m]
        dRP[m] = dOu[m] / Ins.RvwPrd[m]
    if O is not None:
        for p,B in enumerate(O.Blg):
            nOrd[p] = sum([1 for t in B.t if t > 0])
            nStOut[p] = sum([1 for i in range(len(B.v)-1) if B.v[i] < B.v[i+1]])
            AvgBlg[p] = np.inner(np.diff(B.t),B.v[:-1]) / B.t[-1]
        AvgBlgE = [0]*Ins.nProd
        T = O.Blg[0].t[-1]
        for p,E in enumerate(O.EvB):
            AvgBlgE[p] = Ins.InitBlg[p] + np.inner((T - E.t),E.v)/T
        for m,I in enumerate(O.Inv):
            AvgInv[m] = sum([I.v[i]*(I.t[i+1]-I.t[i]) for i in range(len(I.v)-1) if I.v[i] > 0]) / I.t[-1]

    print("Instance Analysis:")
    print(f"{' dRt':^6}  {' dOu':^6}  {' dRP':^6}")
    for m in range(Ins.nMtrl):
        print(f"{dRt[m]:6.2f}  {dOu[m]:6.2f}  {dRP[m]:6.2f}")
    
    print("Backlog Statistics")
    print(f" {'p':>2}  {'nO':>3} {'nSO':>3} {'Avg':>5} {'Area':^6} {'Avg2':>5}")
    for p,B in enumerate(O.Blg):
        print(f" {p:>2}  {nOrd[p]:3} {nStOut[p]:3} {AvgBlg[p]:5.2f} {np.inner(np.diff(B.t),B.v[:-1]):6.1f} {AvgBlgE[p]:5.2f}")

    print("Inventory Statistics")
    print(f" {'m':>2}  {'OUL':>3} {' dRt':^5}  {' dOu':^5}  {' dRP':>5}  {'Avg':>5}")
    for m,I in enumerate(O.Inv):
        print(f" {m:>2}  {Ins.OrdUpTo[m]:3} {dRt[m]:5.2f}  {dOu[m]:5.1f}  {dRP[m]:5.1f}  {AvgInv[m]:5.1f}")

    return (dRt, dOu, dRP, nOrd, nStOut), (AvgBlg, AvgInv)


def Test1():
    # main()
    Ins = BuildInstance(InstanceCase())
    RunSlb(Ins, T=300, rs=3)
    PltOut(Sim.Out)


def Test2(T=None):
    global Ins, Out
    if T is None:
        T = 30
    OUL = [60, 30, 60, 20, 10, 15, 60, 20, 15, 25, 15, 20, 30, 15, 15, 10]
    Ins, Out = [], []
    for i,f in enumerate([1.0, 0.7, 0.3, 0.2]):
        Ins.append(BuildInstance(InstanceCase()))
        Ins[-1].OrdUpTo = [int(o*f) for o in OUL]
        Out.append(RunSlb(Ins[-1], T=T, rs=123))
        PltOut(Out[-1], i+5)
        PltInv(Out[-1], i+10)



# Instantiation of module global objects
Ins = None
Out = None


# new data structure: 
# Runs[:] = [SimOutput(n,p,m) for i range(numExperiments)]

print()
print("-Tally Statistics of Inv.StockOut while Blg>0 or ++Blg events (@Demand Arrival or @PurchArrival)")
print(" ReleasePO")
print()
