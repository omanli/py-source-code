import salabim as sim
import sys


class Car(sim.Component):
    def process(self):
        global process_loop_count, max_process_loop
        while True:
            process_loop_count += 1
            if process_loop_count >= max_process_loop:
                print(f"t={env.now():5.3f}  max_process_loop occured before t>=T")
                env.main().activate()
            else:
                print(f"t={env.now():5.3f}")
            yield self.hold(sim.random.expovariate(1))


T, max_process_loop = 5, 3
process_loop_count = 0
env = None


def main():
    global env
    env = sim.Environment(trace=True)
    sim.random_seed(seed="*")
    Car()
    env.run(till=5)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        T = int(sys.argv[1])
    if len(sys.argv) >= 3:
        max_process_loop = int(sys.argv[2])
    main()

