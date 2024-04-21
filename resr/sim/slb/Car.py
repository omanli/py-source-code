import salabim as sim

slb_Environment = sim.Environment
slb_Component = sim.Component
Gamma = sim.random.gammavariate
Uniform = sim.random.uniform


class SIM:
    s_drive_shape = None
    s_drive_scale = None
    s_stop_min = None
    s_stop_max = None
    env = None
    n_loops = None


class Car(slb_Component):
    def process(self):
        while True:
            self.hold(Gamma(SIM.s_drive_shape, SIM.s_drive_scale))
            self.hold(Uniform(SIM.s_stop_min, SIM.s_stop_max))
            SIM.n_loops += 1


def Run(trace, rs, T, s_shape, s_scale, s_stop_min, s_stop_max):
    SIM.n_loops = 0
    SIM.s_drive_shape = s_shape
    SIM.s_drive_scale = s_scale
    SIM.s_stop_min    = s_stop_min
    SIM.s_stop_max    = s_stop_max

    SIM.env = slb_Environment(trace=trace)
    SIM.env.random_seed(rs)

    Car()

    SIM.env.run(till=T)

    print(f"Num Loops Completed: {SIM.n_loops}")

    return

