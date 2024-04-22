""" Experiment with priority feature in Queue Component
"""

import salabim as sim

slb_Environment = sim.Environment
slb_Component = sim.Component
slb_Queue = sim.Queue


class SIM:
    env   = None
    A     = None
    Q     = None
    fmt_t = "{:4.1f}"


def print_curr_time():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")


def print_add(nm):
    print_curr_time()
    print(f"Add {nm}")

def print_Q():
    for e in SIM.Q:
        print(f"      {e.name()} {e.prior} {e.t_arr}")


class A(slb_Component):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.iat = [int(v) for v in "1 3 2 4 2 1".split()]
        self.pri = [int(v) for v in "3 2 1 3 2 1".split()]

    def process(self):
        for i,(t,p) in enumerate(zip(self.iat, self.pri)):
            self.hold(t)
            nm = f"e{i+1}"
            print_add(nm)
            e = slb_Component(name=nm)
            e.t_arr = SIM.env.now()
            e.prior = p
            SIM.Q.add_sorted(component=e, priority=p)
            print_Q()
            print()



def Run():
    SIM.env = slb_Environment(trace=False)
    SIM.A = A("Arrivals")
    SIM.Q = slb_Queue(name="PQ")

    print_curr_time()
    print("Sim ready to run()")
    SIM.env.run()

    return

