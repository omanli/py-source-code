""" Experiment with priority feature in Queue Component

    Job State: entities in priority queues  (next operation/task)
                  add self to request queue
                  rather than requesting the resource directly
               remember last/current server (mechanic) (resource)

    Srv State: keep track whether assigned (resource claimed?)

    find circumstances to switch server (mechanic) on a job
                       to make 
    
    handle service time dependent on the server skill/type

    use Scheduler.activate() rather than 
        Scheduler.process():self.standby()
"""

import salabim as sim


class SIM:
    env = None
    J   = None  # job cycle
    M   = None  # resource w capacity
    Y   = None  # scheduler
    fmt_t = "{:4.1f}"

def print_curr_time():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")

def print_event(e):
    print(SIM.fmt_t.format(SIM.env.now()), end=" ")
    print(f"[{SIM.M.available_quantity()}] {e}")



class M(sim.Resource):
    pass


class Y(sim.Component):
    def process(self):
        msg = {True:"Idle", False:"Busy"}
        while True:
            self.passivate()

            r1 = sim.random.random()
            r2 = sim.random.random()

            if (r1 > 0.4) and (SIM.M.available_quantity() > 0):
                SIM.J.request(SIM.M)
                print_event(f"Sch after Job req {r1:5.3f} {r2:5.3f}")
                continue

            if (r2 > 0.6) and (SIM.M in SIM.J.claimed_resources()):
                SIM.J.release(SIM.M)
                print_event(f"Sch after Job rel {r1:5.3f} {r2:5.3f}")
                continue

            print_event(f"Sch no action     {r1:5.3f} {r2:5.3f}")


class J(sim.Component):
    def process(self):
        while True:
            self.hold(sim.random.choice((1, 2, 2, 2, 4, 4)))
            SIM.Y.activate()



def Experiment(rs, T):
    SIM.env = sim.Environment(trace=False)
    SIM.env.random_seed(rs)

    SIM.J = J("Job")
    SIM.M = M("Mechanic", capacity=2)
    SIM.Y = Y("Scheduler")

    print_event("Exp starts")
    SIM.env.run(till=T)
    print_event("Exp ends\n\n")

    # SIM.M.available_quantity.print_statistics()
    # SIM.M.claimed_quantity.print_statistics()

    return


