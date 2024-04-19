"""
Bank renege example

Covers:

- Resources: Resource
- Condition events

Scenario:
  A counter with a random service time and customers who renege. Based on the
  program bank08.py from TheBank tutorial of SimPy 2. (KGM)

  

import <this> as B
reload(B)
B.simulate(random_seed=32, num_customers=5, service_time="Exp(8)")

B.simulate(random_seed=32, num_customers=3, 
           interarrival_time="Seq[3,1,1,1,1]", 
           service_time="Seq[3.5,2.5,4.5,5.5]", 
           patience="Det(100)")
"""


from random import (
    seed as Seed,
    expovariate as Exponential,
    uniform as Uniform,
)
import simpy


def Finite_Sequence(L):
    for x in L:
        yield x


class SIM():
    # simulation model parameters & prob.distributions
    num_customers     = None  # max Num of Customer Arrivals to simulate
    interarrival_time = None  # interarrival times sample generator
    service_time      = None  # service times sample generator
    patience          = None  # time before renege sample generator
    num_tellers       = None  # Num of Tellers working at the counter
    random_seed       = None  # RNG stream initialization seed

    # simpy Simulation objects
    env               = None  # Environment Onject (simpy.Environment)
    bank_counter      = None  # Bank Counter (Tellers) Resource Object simulation object (simpy.Resource)

    # default value
    RANDOM_SEED = 123
    NUM_TELLERS = 1          # Number of tellers at the counter
    NEW_CUSTOMERS = 5        # Total number of customers
    INTERVAL_TIME = 10.0     # Generate new customers roughly every x minutes
    SERVICE_TIME = 5.0       # Time duration a customer spends at the counter
    MIN_PATIENCE = 1         # Min. customer patience
    MAX_PATIENCE = 3         # Max. customer patience

    # printing format strings
    fmt_time = "{:8.3f}"
    fmt_cid  = "C{:03d}"
    fmt_stat = "{:.3f}"



def Customer_Arrivals():
    """ Source creates Customers at random interarrival times
    """
    print(f"Model class num_C: {SIM.num_customers}")
    for i in range(SIM.num_customers):
        t = SIM.interarrival_time()
        yield SIM.env.timeout(t)
        c = Customer(i)
        SIM.env.process(c)


def Customer(i):
    """ Customer arrives, is served and leaves
        or reneges after patience runs out
    """
    name = SIM.fmt_cid.format(i)
    arrive = SIM.env.now
    print((f"{SIM.fmt_time.format(arrive)}: {name} Arrives "
           f"Q={len(SIM.bank_counter.queue)} " 
           f"S={SIM.bank_counter.count} / {SIM.bank_counter.capacity}"))

    """ SIM.bank_counter.users : list of request objects
        SIM.bank_counter.queue : list of request objects
        len(SIM.bank_counter.users)
        len(SIM.bank_counter.queue)
    """

    with SIM.bank_counter.request() as request:
        # Wait for the counter or leave when patience expires
        event = yield request | SIM.env.timeout(SIM.patience())
        # type(results) = <simpy.events.ConditionValue>

        wait = SIM.env.now - arrive

        if request in event:
            # Teller starts taking care of this Customer's Transaction 
            # (end of Waiting) (start of Service)
            print((f"{SIM.fmt_time.format(SIM.env.now)}: {name} "
                   f"Svc Starts [WaitingTime={SIM.fmt_stat.format(wait)}]"))

            t = SIM.service_time()
            yield SIM.env.timeout(t)
            # Teller completes this Customer's Transaction 
            # (end of Service)
            sojourn = SIM.env.now - arrive
            print((f"{SIM.fmt_time.format(SIM.env.now)}: {name} "
                   f"Departs    [SystemTime={SIM.fmt_stat.format(sojourn)}]"))
        else:
            # Customers reneges
            # (end of Waiting) (customer leaves)
            print((f"{SIM.fmt_time.format(SIM.env.now)}: {name} "
                   f"Reneges    [WaitingTime={SIM.fmt_stat.format(wait)}]"))



def sample_generator(spec):
    if spec[:4] == "Exp(":
        val = spec[4:-1]
        return (lambda : Exponential(1.0 / float(val)))
    if spec[:4] == "Uni(":
        val = spec[4:-1]
        return (lambda : Uniform(*(float(v) for v in val.split(',')[:2])))
    if spec[:4] == "Det(":
        val = spec[4:-1]
        return (lambda : float(val))
    if spec[:4] == "Seq[":
        val = spec[4:-1]
        g = Finite_Sequence((float(v) for v in val.split(',')))
        return g.__next__

    raise ValueError(f"Invalid spec[:4]={spec[:4]}")



def simulate(
        random_seed=None, 
        num_tellers=None, 
        num_customers=None, 
        interarrival_time=None, 
        service_time=None,
        patience=None
    ):
    # model parameters
    SIM.num_customers = SIM.NEW_CUSTOMERS if num_customers is None else num_customers
    SIM.random_seed = SIM.RANDOM_SEED if random_seed is None else random_seed
    SIM.num_tellers = SIM.NUM_TELLERS if num_tellers is None else num_tellers

    interarrival_time = f"Exp({SIM.INTERVAL_TIME})" if interarrival_time is None else interarrival_time
    service_time = f"Exp({SIM.SERVICE_TIME})" if service_time is None else service_time
    patience = f"Uni({SIM.MIN_PATIENCE},{SIM.MAX_PATIENCE})" if patience is None else patience

    SIM.interarrival_time = sample_generator(interarrival_time)
    SIM.service_time = sample_generator(service_time)
    SIM.patience = sample_generator(patience)

    # Setup and start the simulation
    print('Bank Renege Model Simulation')
    print(f"{SIM.fmt_time.format(0)}: Simulation Starts")
    Seed(SIM.random_seed)
    SIM.env = simpy.Environment()

    # Start processes and run
    SIM.bank_counter = simpy.Resource(SIM.env, capacity=SIM.num_tellers)
    SIM.env.process(Customer_Arrivals())
    SIM.env.run()
