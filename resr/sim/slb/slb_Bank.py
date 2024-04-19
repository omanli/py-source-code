# Bank Example with 1 clerk

import salabim as sim
import sys


'''
module objects must be created before function definitions
so that they appear in the module symbols dictionary and 
so that they do not get generated as local name for a new function/class definition
'''
print("Module initialization")
waitingline = None
env = None


class CustomerGenerator(sim.Component):
    def setup(self, maxCustomers=None):
        # assuming only one instance is created per simulation model run
        self.customer_count = 0
        if max_customers is None:
            self.max_customers = sim.inf
    def process(self):
        print("CustomerGenerator process starts")
        while True:
            Customer()
            self.customer_count += 1
            if self.customer_count >= self.max_customers:
                
            yield self.hold(sim.Uniform(5, 15).sample())


class Customer(sim.Component):
    def process(self):
        self.enter(waitingline)
        if clerk.ispassive():
            clerk.activate()
        yield self.passivate()


class Clerk(sim.Component):
    def process(self):
        print("Clerk process starts")
        while True:
            while len(waitingline) == 0:
                yield self.passivate()
            self.customer = waitingline.pop()
            yield self.hold(30)
            self.customer.activate()


def run(T,rs=1,ps=False):
    global waitingline, env, clerk, yolo

    sim.random_seed(seed=rs)
    env = sim.Environment(trace=True)

    print("Setting up")
    waitingline = sim.Queue("waitingline")
    c = Customer()
    cg = CustomerGenerator()
    clerk = Clerk()

    env.run(till=T)
    if ps:
        print()
        waitingline.print_statistics()


if __name__ == "__main__":
    # sys.argv[0] is the path+filename
    if len(sys.argv) >= 2:
        st = int(sys.argv[1])
    else:
        st = 20
    run(T=st)
