from logging import debug
from statistics import mean
from time import time
from typing import List, Tuple

from numpy.random import default_rng


class Simulator:
    def __init__(self, lam: float, mi: float, on_time: float, off_time: float,
                 servers: int, time_limit: float, events_limit: int, seed: int,
                 variant: str):
        self.lam = lam  # Lambda
        self.mi = mi  # Mi
        self.on_time_param = on_time  # On time
        self.off_time_param = off_time  # Off time
        self.servers = servers  # Number of servers
        self.time_limit = time_limit  # Max simulation time
        self.events_limit = events_limit  # Max number of events
        self.running = True  # Server status
        self.variant = variant  # Busy servers counter
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

        # Add primary events to the list
        ev = ('server_off', self.start_time + self.on_time(), 0)
        self.event_list.append(ev)
        debug(f'Adding to event list {ev}')

        self.arrivals = 1
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

                if not self.servers_busy() and self.running:
                    self.busy += 1
                    eos_ev = (f'end_of_service', ev_time + self.serve_time(),
                              ev_id)
                    self.event_list.append(eos_ev)
                    debug(f'Adding to event list {eos_ev}')
                else:
                    self.queued += 1
                    wait_ev = (f'waiting', self.earliest_available_time(),
                               ev_id)
                    self.event_list.append(wait_ev)
                    debug(f'Adding to event list {wait_ev}')

                self.arrivals += 1
                new_ev = ('arrival', ev_time + self.arrival_time(),
                          self.arrivals)
                self.event_list.append(new_ev)
                debug(f'Adding to event list {new_ev}')

            elif ev_type == 'waiting':
                if not self.servers_busy() and self.running:
                    self.busy += 1
                    self.queued -= 1
                    eos_ev = (f'end_of_service', ev_time + self.serve_time(),
                              ev_id)
                    self.event_list.append(eos_ev)
                    debug(f'Adding to event list {eos_ev}')
                else:
                    wait_ev = (f'{ev_type}', self.earliest_available_time(),
                               ev_id)
                    self.event_list.append(wait_ev)
                    debug(f'Updating in event list {wait_ev}')

            elif ev_type == 'end_of_service':
                if self.running:
                    self.served += 1
                    self.busy -= 1
                    debug(f'{ev_type}: Incrementing served, decrementing busy')
                else:
                    remaining_time = self.get_remaining_time(ev_type, ev_time,
                                                             ev_id)
                    eos_ev = (f'{ev_type}', self.earliest_available_time() +
                              remaining_time, ev_id)
                    self.event_list.append(eos_ev)
                    debug(f'Updating in event list {eos_ev}')

            elif ev_type == 'server_off':
                on_ev = ('server_on', ev_time + self.off_time(), ev_id)
                self.event_list.append(on_ev)
                self.running = False
                debug(f'Scheduling server ON {on_ev}')

            elif ev_type == 'server_on':
                off_ev = ('server_off', ev_time + self.on_time(), ev_id)
                self.event_list.append(off_ev)
                self.running = True
                debug(f'Scheduling server OFF {off_ev}')

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

    def earliest_available_time(self):
        """Returns time of the earliest end_of_service event or server_on
        depending on variant and system status event."""

        if self.running:
            ev_type = 'end_of_service'
        else:
            ev_type = 'server_on'

        events = list(
            filter(
                lambda x: x[0] == ev_type, self.event_list
            )
        )
        # Sort ascending by time
        events.sort(key=lambda x: x[1])
        # Take eos event with the earliest time and return its time
        return events[0][1]

    def serve_time(self):
        """Generate serving time."""

        return self.rng.exponential(1 / self.mi)

    def off_time(self):
        """Generate off time."""

        return self.rng.exponential(self.off_time_param)

    def on_time(self):
        """Generate on time."""

        return self.rng.exponential(self.on_time_param)

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
        start_ev_time = filtered_history[0].get('arrival')[0]
        end_ev_time = filtered_history[-1].get('end_of_service')[-1]

        simulation_time = end_ev_time - start_ev_time

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
        real_mean_clients_in_queue = (self.lam / self.mi) ** 2 / (1 - self.lam /
                                                                  self.mi)

        # Średnia ilosc klientów w systemie
        mean_clients_in_system = mean(self.stats['in_system'])
        real_mean_clients_in_system = (self.lam / self.mi) / (1 - self.lam /
                                                              self.mi)

        # Średni czas obsługi
        mean_service_time = mean(service_times)
        real_mean_service_time = 1 / self.mi

        # Prawdopodobieństwo, że serwer włączony lub wyłączony
        on_times = self.event_history[0].get('server_off')
        off_times = self.event_history[0].get('server_on')
        if len(off_times) != len(on_times):
            on_times = on_times[:-1]
        on_sum = sum(off_times) - sum(on_times)
        off_sum = sum(on_times[1:]) - sum(off_times[:-1])
        p_on = on_sum / (on_sum + off_sum)
        p_off = off_sum / (on_sum + off_sum)

        on_off_sum = self.on_time_param + self.off_time_param
        real_p_on = self.on_time_param / on_off_sum
        real_p_off = self.off_time_param / on_off_sum

        # Średni czas przebywania w systemie
        mean_system_time = mean(system_times)

        ro_prim = self.lam / self.mi / real_p_on
        real_mean_system_time = (ro_prim + self.lam * self.off_time_param *
                                 real_p_off) / (1 - ro_prim) / self.lam

        # Prawd. że serwer pusty
        server_empty_prob = 1 - mean(self.stats['busy'])
        real_server_empty_prob = 1 - self.lam / self.mi

        return {
            'mean_system_time': mean_system_time,
            'real_mean_system_time': real_mean_system_time
        }

    def update_stats(self):
        self.stats['in_system'].append(self.queued + self.busy)
        self.stats['in_queue'].append(self.queued)
        self.stats['busy'].append(self.busy)

    def get_remaining_time(self, ev_type, ev_time, ev_id):
        # Wariant A: zapamiętanie pozostałego czasu obsługi i dokończenie po
        #  wznowieniu serwera
        # Wariant B: Retransmisja całości po wznowieniu serwera
        events_history = self.event_history.get(ev_id, {})
        serve_start_time = events_history.get('waiting', [0])[-1]
        if not serve_start_time:
            serve_start_time = events_history.get('arrival')[-1]

        serve_time = ev_time - serve_start_time

        if self.variant == 'B':
            return serve_time

        srv_on_history = self.event_history.get(0).get('server_off')

        server_off_time = srv_on_history[-1]

        remaining_time = ev_time - server_off_time

        return remaining_time
