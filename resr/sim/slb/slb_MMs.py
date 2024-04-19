import salabim as sim

"""
M/M/s simulator
setup(arr_rate, svc_rate, num_srv, U, trace)
arr_rate : arrival rate per unit time
svc_rate : service rate per unit time per server
 num_srv : number of servers
       U : utilization rate


Two out of three parameters, arr_rate, svc_rate, U,
must be given, the third is calculated using the following
identity:

       U = arr_rate / (num_srv * svc_rate)
"""


'''
either use module level attributes/objects to be accessed 
       through the python default namespace rules
       global declaration is required in order to assign a new value 
       to a module level attribute from within a function/class 
       reading does not require global declaration but writing does
or use an explicit top level class to be used as namespace 

provide an assignment/setup function to provide help on 
module level attributes or top level class
'''



class Customer(sim.Component):
    def setup(self, svc_time):
        self.svc_time = svc_time

    def process(self):
        yield self.passivate()


class Arrivals(sim.Component):
    # count = 0
    def process(self):
        while True:
            c = Customer(svc_time = Model.svc_time_dist.sample())
            c.enter(Model.Queue)
            """
            self.count += 1
            if self.count % 10 == 0:
                print(Model.Queue.length())
            """
            # server logic (pick the first available server)
            for s in Model.Servers:
                if s.ispassive():
                    s.activate()
                    break
            yield self.hold(Model.iar_time_dist.sample())


class Server(sim.Component):
    def process(self):
        while True:
            while len(Model.Queue) == 0:
                yield self.passivate()
            c = Model.Queue.pop()
            yield self.hold(c.svc_time)
            c.activate()


'''
explicit top level class (informal dataclass) used as namespace 
to access (r/w) simulation model parameters and salabim module objects
'''
class Model():
    env = None
    svc_time_dist = None
    iar_time_dist = None
    Queue = None
    Servers = None
    Arrivals = None
    arr_rate = None
    svc_rate = None
    util = None
    num_srv = None


# setup paramters of the model
def setup(arr_rate=None, svc_rate=None, num_srv=1, util=None):
    if all((arr_rate is None, svc_rate is None, util is None)):
        raise ValueError(f"All three arr_rate={arr_rate} svc_rate={svc_rate} util={util} cannot be None")
    if all((arr_rate is not None, svc_rate is not None, util is not None)):
        raise ValueError(f"All three arr_rate={arr_rate} svc_rate={svc_rate} util={util} cannot be values")
    if util is not None:
        if arr_rate is None:
            arr_rate = util * num_srv * svc_rate
        else:
            svc_rate = arr_rate / (util * num_srv)

    Model.arr_rate = arr_rate
    Model.svc_rate = svc_rate
    Model.num_srv = num_srv
    Model.util = arr_rate / (num_srv * svc_rate)

    n, M, L, U = Model.num_srv, Model.svc_rate, Model.arr_rate, Model.util
    nS = U / (1 - U)
    nQ = nS - U
    tS = 1 / (n*M - L)
    tQ = tS - 1/M
    print(f"Avg. Num in Sys = {nS:7.4f}")
    print(f"Avg. Num in Que = {nQ:7.4f}")
    print(f"  Avg. Sys.Time = {tS:7.4f}")
    print(f"  Avg. Que.Time = {tQ:5.2f}")


'''
import slb_MMs as M
reload(M); M.setup(arr_rate=1, util=0.98, num_srv=3); M.run(1000,1,trace=False)
M.run(1000,2,trace=False)
M.run(1000,3,trace=False)
'''
def run(T, rs=0, trace=False):
    # sequence important, do environment creation first
    Model.env = sim.Environment(trace=trace)
    sim.random_seed(seed=rs)

    Model.svc_time_dist = sim.Exponential(rate=Model.svc_rate)
    Model.iar_time_dist = sim.Exponential(rate=Model.arr_rate)
    Model.Queue = sim.Queue("Waiting Line")
    Model.Servers = [Server() for i in range(Model.num_srv)]
    Model.Arrivals = Arrivals()

    Model.env.run(till=T)

    if not trace:
        print()
    Model.Queue.print_statistics()

