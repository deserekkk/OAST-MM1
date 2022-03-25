from logging import debug
from statistics import mean
from time import time
from typing import List, Tuple

from numpy.random import default_rng


class Simulator:
    def __init__(self, lam, mi, servers: int, time_limit: float,
                 events_limit: int, seed: int):
        self.lam = lam  # Lambda
        self.mi = mi  # Mi
        self.servers = servers  # Number of servers
        self.time_limit = time_limit  # Max simulation time
        self.events_limit = events_limit  # Max number of events
        self.busy = 0  # Busy servers counter
        self.start_time = 0  # Simulation start time
        self.arrivals = 0  # Incoming clients counter
        self.queued = 0  # Queue length counter
        self.served = 0  # Served clients counter
        self.event_list: List[Tuple] = []  # Event list
        self.rng = default_rng(seed)  # Random number generator
        self.event_history = {}  # Dict with statistics for each event
        self.stats = {  # Statistics measurements
            'in_queue': [],
            'in_system': [],
            'busy': []
        }

    def end(self):
        """End simulation condition."""

        return ((time() - self.start_time) > self.time_limit) or \
               (self.served >= self.events_limit)

    def run(self):
        """Run simulation."""

        debug('Starting simulation')
        self.start_time = time()

        # Add primary event on list
        self.arrivals += 1
        ev = ('arrival', self.start_time, self.arrivals)
        self.event_list.append(ev)
        debug(f'Adding to event list {ev}')

        while not self.end():
            # Take event from list
            ev = self.pop_list()
            ev_type, ev_time, ev_id = ev
            debug(f'New event appeared {ev}')

            if ev_type == 'arrival':
                # What the queue looks like before the event
                self.update_stats()

                if not self.servers_busy():
                    self.busy += 1
                    eos_ev = (f'end_of_service', ev_time + self.serve_time(),
                              ev_id)
                    self.event_list.append(eos_ev)
                    debug(f'Adding to event list {eos_ev}')
                else:
                    self.queued += 1
                    wait_ev = (f'waiting', self.earliest_eos_time(), ev_id)
                    self.event_list.append(wait_ev)
                    debug(f'Adding to event list {wait_ev}')

                self.arrivals += 1
                new_ev = ('arrival', ev_time + self.arrival_time(),
                          self.arrivals)
                self.event_list.append(new_ev)
                debug(f'Adding to event list {new_ev}')

            elif 'waiting' in ev_type:
                if not self.servers_busy():
                    self.busy += 1
                    self.queued -= 1
                    eos_ev = (f'end_of_service', ev_time + self.serve_time(),
                              ev_id)
                    self.event_list.append(eos_ev)
                    debug(f'Adding to event list {eos_ev}')
                else:
                    wait_ev = (f'{ev_type}', self.earliest_eos_time(), ev_id)
                    self.event_list.append(wait_ev)
                    debug(f'Updating in event list {wait_ev}')

            elif 'end_of_service' in ev_type:
                self.served += 1
                self.busy -= 1
                debug(f'{ev_type}: Incrementing served, decrementing busy')

        debug('Simulation done')

    def pop_list(self):
        """Returns next to come event."""

        # Sort ascending by time
        self.event_list.sort(key=lambda x: x[1])
        # Take event with smallest time
        ev = self.event_list[0]
        # Remove it from list by overwriting list bypassing zero element
        self.event_list = self.event_list[1:]

        # Statistics update
        ev_type, ev_time, ev_id = ev
        if self.event_history.get(ev_id):
            ev_slot = self.event_history[ev_id]
            if ev_slot.get(ev_type):
                ev_slot[ev_type].append(ev_time)
            else:
                ev_slot[ev_type] = [ev_time]
        else:
            self.event_history[ev_id] = {
                ev_type: [ev_time]
            }

        # Return the event
        return ev

    def earliest_eos_time(self):
        """Returns time of earliest end_of_service event."""

        # Filter all end_of_service events
        eos_events = list(
            filter(
                lambda x: 'end_of_service' in x[0], self.event_list
            )
        )
        # Sort ascending by time
        eos_events.sort(key=lambda x: x[1])
        # Take eos event with earliest time and return its time
        return eos_events[0][1]

    def serve_time(self):
        """Generate serving time."""

        return self.rng.exponential(1 / self.mi)

    def arrival_time(self):
        """Generate arrival time."""

        return self.rng.exponential(1 / self.lam)

    def servers_busy(self):
        """Check if server is busy by comparing number of end_of_service
        events with number of servers."""

        return self.busy >= self.servers

    def get_result(self):
        service_times = []
        system_times = []
        filtered_history = [v for v in self.event_history.values() if
                            v.get('end_of_service')]
        for ev_dict in filtered_history:
            last_arrival = ev_dict.get('arrival', [0])[-1]
            last_waiting = ev_dict.get('waiting', [0])[-1]
            last_eos = ev_dict.get('end_of_service', [0])[-1]

            # czas obsługi = ev.eos - ev.last_waitin lub
            # ev.eos - ev.arrival
            if not last_waiting:
                service_times.append(last_eos - last_arrival)
            else:
                service_times.append(last_eos - last_waiting)

            # czas przebywania w systemie = ev.eos - ev.arrival
            system_times.append(last_eos - last_arrival)

        # Średnia ilosc klientów w kolejce
        mean_clients_in_queue = mean(self.stats['in_queue'])
        real_mean_clients_in_queue = (self.lam / self.mi) ** 2 / (
                1 - self.lam / self.mi)

        # Średnia ilosc klientów w systemie
        mean_clients_in_system = mean(self.stats['in_system'])
        real_mean_clients_in_system = (self.lam / self.mi) / (
                1 - self.lam / self.mi)

        # Średni czas obsługi
        mean_service_time = mean(service_times)
        real_mean_service_time = 1 / self.mi

        # Średni czas przebywania w systemie
        mean_system_time = mean(system_times)
        real_mean_system_time = 1 / (self.mi - self.lam)

        # Prawd. że serwer pusty
        server_empty_prob = 1 - mean(self.stats['busy'])
        real_server_empty_prob = 1 - self.lam / self.mi

        return {
            'mean_clients_in_queue': mean_clients_in_queue,
            'real_mean_clients_in_queue': real_mean_clients_in_queue,
            'mean_clients_in_system': mean_clients_in_system,
            'real_mean_clients_in_system': real_mean_clients_in_system,
            'mean_service_time': mean_service_time,
            'real_mean_service_time': real_mean_service_time,
            'mean_system_time': mean_system_time,
            'real_mean_system_time': real_mean_system_time,
            'server_empty_prob': server_empty_prob,
            'real_server_empty_prob': real_server_empty_prob
        }

    def update_stats(self):
        self.stats['in_system'].append(self.queued + self.busy)
        self.stats['in_queue'].append(self.queued)
        self.stats['busy'].append(self.busy)
