import salabim as sim


from .Util import RV, TU


class SIM:
    env = None
    time_unit = None
    tu  = None
    ctu = None
    trace = False
    #
    num_events = None
    G = None
    #
    fmt_t   = "{:7.2f}"


def print_time_now():
    print(SIM.fmt_t.format(SIM.env.now()), end=": ")


def print_event(e):
    print_time_now()
    print(f"{e}")


class E(sim.Component):
    def __init__(self, name, iat, *args, **kwargs):
        super().__init__(name=name, *args, **kwargs)
        self.iat = iat

    def process(self):
        while True:
            # self.hold(SIM.ctu(self.iat.sample()))
            # self.hold(self.iat())
            # hold() handles the time_unit of the distribution
            # no need to convert explicitly
            self.hold(self.iat)
            print_event(self.name())
            SIM.num_events += 1



def Run(rs, T, tu=None, rsg=None):
    SIM.num_events = 0
    SIM.time_unit = 'hours'
    SIM.env = sim.Environment(time_unit=SIM.time_unit, trace=SIM.trace)
    SIM.ctu = {'hours'   : SIM.env.to_hours,
               'days'    : SIM.env.to_days,
               'minutes' : SIM.env.to_minutes,
              }[SIM.time_unit]
    SIM.tu  = 1 * TU[SIM.time_unit]
    SIM.env.random_seed(rs)
    tu = SIM.time_unit if tu is None else tu


    if rsg is None:
        g = SIM.env.Uniform(1000,9999)
        rsg = [int(g()) for _ in range(1,21)]

    print(T*SIM.ctu(TU[tu]))
    
    SIM.G = []
    SIM.G.append(E(name="Det", iat=RV('Seq', 'hours', None, [0.2*i*T*SIM.ctu(TU[tu]) for i in range(1,10)])))

    if rsg[0]:
        SIM.G.append(E(name="Exp1", iat=RV('Exponential', 'years',   rsg[0], 2.5/365)))
    if rsg[1]:
        SIM.G.append(E(name="Exp2", iat=RV('Exponential', 'hours',   rsg[1], 24*3)))
    if rsg[2]:
        SIM.G.append(E(name="Gmm",  iat=RV('Gamma',       'weeks',   rsg[2], 4, (3/7)/4)))
    if rsg[3]:
        SIM.G.append(E(name="Nor",  iat=RV('Normal',      'minutes', rsg[3], 3*24*60, 0.5*24*60)))
    if rsg[4]:
        SIM.G.append(E(name="Tri",  iat=RV('Triangular',  'seconds', rsg[4], 1*24*3600, 2*24*3600, 6*24*3600)))

    SIM.env.run(till=SIM.ctu(T * TU[tu]))
    
    print(f"\nNum Ev = {SIM.num_events}")

    return
