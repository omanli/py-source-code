# Bank Example with 3 clerks modeled w resources

import salabim as sim


class Top():
    env = None
    iartime_dist = None
    srvtime_dist = None
    Clerks = None
    nA,nD = 0,0
    # Top.Clerks.capacity()
    # Top.Clerks.claimed_quantity()
    # Top.Clerks.claimers().length()
    # Top.Clerks.requesters().length()


class CustomerGenerator(sim.Component):
    # count = 0
    # mx = 0
    def process(self):
        while True:
            Customer()
            """
            self.count += 1
            Top.Clerks.claimed_quantity()
            Top.Clerks.requesters().length()
            if CustomerGenerator.count % 10 == 0:
                print(Top.Clerks.capacity(), ":", 
                      Top.Clerks.claimed_quantity(), Top.Clerks.requesters().length(), ":", 
                      Top.Clerks.claimed_quantity() + Top.Clerks.requesters().length())
                      # "-", Top.Clerks.claimed_quantity()-Top.Clerks.claimers().length()
            """
            yield self.hold(Top.iartime_dist.sample())


class Customer(sim.Component):
    def process(self):
        Top.nA += 1
        # print(f"A : {Top.env.now():6.3f}  N={Top.Clerks.claimed_quantity()+1 + Top.Clerks.requesters().length()}  N={Top.nA-Top.nD}")
        yield self.request(Top.Clerks)
        yield self.hold(Top.srvtime_dist.sample())
        self.release() # not really required
        Top.nD += 1
        # print(f"D : {Top.env.now():6.3f}  N={Top.Clerks.claimed_quantity() + Top.Clerks.requesters().length()}  N={Top.nA-Top.nD}")


# no need to try this test anymore
def Test(C,L,rs=1):
    env = sim.Environment(trace=False)
    sim.random_seed(seed=rs)
    iar_time_dist = sim.Exponential(1)
    svc_time_dist = sim.Exponential(4)
    S = sim.Resource("servers", capacity=C)
    for _ in range(C):
        c = Customer()
        c.request(S)
        # c.hold(svc_time_dist.sample())
    print(S.capacity(), ":", 
          S.claimed_quantity(), S.requesters().length(), ":", 
          S.claimed_quantity() + S.requesters().length())
    for _ in range(L):
        c = Customer()
        c.request(S)
    print(S.capacity(), ":", 
          S.claimed_quantity(), S.requesters().length(), ":", 
          S.claimed_quantity() + S.requesters().length())


"""
import slb_Bank_res as Br
reload(Br); Br.run(5000,C=3,IA=["E",7],SRV=["E",20],rs=15)
reload(Br); Br.run(5000,C=1,IA=["U",0,40],SRV=["U",10,28],rs=15)
Br.Top.Clerks.print_statistics()
Br.Top.Clerks.requesters().print_statistics()
Br.Top.Clerks.print_info()
"""
def run(T, C=1, IA=None, SRV=None, rs=1, ps=False):
    if IA is None:
        IA = ["U",5,15]
    if SRV is None:
        SRV = ["U",20,40]
    if IA[0] == "U":
        Top.iartime_dist = sim.Uniform(lowerbound=IA[1],upperbound=IA[2])
        ArrRt = 2 / (IA[0] + IA[1])
    elif IA[0] == "E":
        Top.iartime_dist = sim.Exponential(mean=IA[1])
        ArrRt = 1 / IA[1]
    if SRV[0] == "U":
        Top.srvtime_dist = sim.Uniform(lowerbound=SRV[1],upperbound=SRV[2])
        SrvRt = 2 / (SRV[1] + SRV[2])
    elif SRV[0] == "E":
        Top.srvtime_dist = sim.Exponential(mean=SRV[1])
        SrvRt = 1 / SRV[1]

    Top.env = sim.Environment(trace=False)
    sim.random_seed(seed=rs)
    Top.Clerks = sim.Resource("clerks", capacity=C)
    
    CustomerGenerator()

    Top.env.run(till=T)

    # Top.Clerks.print_statistics()
    Top.Clerks.requesters().print_statistics()
    # Top.Clerks.print_info()
    print()

    Util = ArrRt / (C*SrvRt)
    print(f"Arrival Rate = {ArrRt:5.3f}")
    print(f"Service Rate = {SrvRt:5.3f}")
    print(f" Utilization = {Util:5.3f}")
    
