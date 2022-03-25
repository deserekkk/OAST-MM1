from itertools import product
from json import loads, JSONDecodeError, dumps
from logging import info
from multiprocessing import Pool
from pathlib import Path
from statistics import mean

from numpy.random import default_rng
from scipy.stats import t, sem, norm

from simulator import Simulator
from simulator_no_off import Simulator as SimulatorNoOff
from utils import setup_logger

logger = setup_logger()


class Simulation:
    def __init__(self, config_path, results_path):
        self.config_path = config_path
        self.results_path = results_path
        self.config = self.load_json(config_path)
        self.rng = self.get_rng()
        self.results = None

    @staticmethod
    def load_json(path):
        """Parse json file to dict."""

        config_file = Path(path)
        try:
            return loads(config_file.read_text(encoding='utf8'))
        except JSONDecodeError:
            return {}

    def run(self):
        multithreaded = self.config.get('multithreaded', False)
        mi_values = self.config.get('mi_values', [0.6])
        lam_values = self.config.get('lam_values', [1])
        on_values = self.config.get('on_values', [40])
        off_values = self.config.get('off_values', [35])
        server_counts = self.config.get('server_counts', [1])
        sim_repetitions = self.config.get('simulation_repetitions', 10)
        info('Simulation config loaded')

        info(f'Running simulator with k = {sim_repetitions} repetitions for each combination of mi, lam and server count values')

        combinations = product(mi_values, lam_values, on_values, off_values,
                               server_counts)
        if multithreaded:
            with Pool() as pool:
                self.results = pool.map(self.simulate, combinations)
        else:
            self.results = map(self.simulate, combinations)
        Path(self.results_path).write_text(dumps(list(self.results)))

    def simulate(self, combination):
        sim_repetitions = self.config.get('simulation_repetitions', 10)
        time_limit = self.config.get('time_limit', 10)
        events_limit = self.config.get('events_limit', 10000)
        variant = self.config.get('variant', 'A')

        mi, lam, on_time, off_time, servers = combination

        rho = lam / mi
        info(f'lam = {lam}, mi = {mi} ==> rho = {rho}')

        simulation_results = {
            'mi': mi,
            'lam': lam,
            'rho': rho
        }

        simulator_results = []
        for i in range(sim_repetitions):
            info(f'Running #{i + 1} simulation')
            if variant in ['A', 'B']:
                sim = Simulator(lam=lam, mi=mi, on_time=on_time,
                                off_time=off_time, servers=servers,
                                time_limit=time_limit,
                                events_limit=events_limit, variant=variant,
                                seed=self.rng.integers(999999))
            else:
                sim = SimulatorNoOff(lam=lam, mi=mi, servers=servers,
                                     time_limit=time_limit,
                                     events_limit=events_limit,
                                     seed=self.rng.integers(999999))

            sim.run()

            sim_res = sim.get_result()

            simulator_results.append(sim_res)

        # Convert the list of dicts, to a dict of lists
        result_keys = list(simulator_results[0].keys())
        aggregated_dict = {k: [] for k in result_keys}
        for res in simulator_results:
            for k, v in res.items():
                aggregated_dict[k].append(v)

        # Confidence intervals computed from dict of lists (N simulations)
        confidence_intervals_dict = {}
        for k, v in aggregated_dict.items():
            if 'real' not in k:
                if sim_repetitions >= 30:
                    confidence_intervals = {
                        alpha: norm.interval(alpha=alpha, loc=mean(v),
                                             scale=sem(v))
                        for alpha in [0.95, 0.99]
                    }
                else:
                    confidence_intervals = {
                        alpha: t.interval(alpha=alpha, df=len(v) - 1,
                                          loc=mean(v), scale=sem(v))
                        for alpha in [0.95, 0.99]
                    }
                key_name = k.replace('mean_', '')
                confidence_intervals_dict[key_name] = confidence_intervals
        simulation_results['confidence_intervals'] = confidence_intervals_dict

        # Take mean of aggregated data
        for k, v in aggregated_dict.items():
            aggregated_dict[k] = mean(v)
        simulation_results['simulator_mean_results'] = aggregated_dict

        return simulation_results

    def get_rng(self):
        seed = self.config.get('seed', 123)
        return default_rng(seed)

    def get_results(self):
        return self.results


def main():
    """Testing simulation."""

    logger.info('Starting simulation')

    sim = Simulation('config/config.json', 'results.json')
    sim.run()

    logger.info('Simulation ended')


if __name__ == '__main__':
    main()
