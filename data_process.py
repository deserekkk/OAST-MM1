from json import loads
from pathlib import Path

from pandas import DataFrame

lst_of_dcts: list[dict] = loads(Path('results.json').read_bytes())

confidences = {}

for dicto in lst_of_dcts:
    lam = dicto.pop('lam')
    rho = dicto.pop('rho')
    dicto.update({
        'lam': round(lam, 3),
        'rho': round(rho, 3)
    })
    simulator_mean_results = dicto.pop('simulator_mean_results')
    kolejnosc = ['mean_system_time', 'real_mean_system_time']
    miejsca = [3, 3]
    dicto.update({
        k: round(simulator_mean_results[k], m) for k, m in
        zip(kolejnosc, miejsca)
    })
    cfd = dicto.pop('confidence_intervals')
    confidences[round(rho, 3)] = cfd

    dicto.update(cfd)

from matplotlib import pyplot as plt, patches
import numpy as np

lams = np.array([dct['lam'] for dct in lst_of_dcts])
mean_system_time = np.array([dct['mean_system_time'] for dct in lst_of_dcts])
real_mean_system_time = np.array([dct['real_mean_system_time']
                                  for dct in lst_of_dcts])
ci_95 = np.array([dct['system_time']['0.95'] for dct in lst_of_dcts])
ci_99 = np.array([dct['system_time']['0.99'] for dct in lst_of_dcts])

plt.plot(lams, real_mean_system_time, color='purple', lw=2)
plt.plot(lams, mean_system_time, color='black', lw=1)

plt.fill_between(lams,
                 [x[0] for x, time in zip(ci_99, mean_system_time)],
                 [x[1] for x, time in zip(ci_99, mean_system_time)],
                 color='red')
plt.fill_between(lams,
                 [x[0] for x, time in zip(ci_95, mean_system_time)],
                 [x[1] for x, time in zip(ci_95, mean_system_time)],
                 color='green')

pop_a = patches.Patch(color='green', label='Przedział ufności 0.95%')
pop_b = patches.Patch(color='red', label='Przedział ufności 0.99%')
pop_c = patches.Patch(linestyle='solid', color='purple',
                      label='Estymata ze wzoru')
pop_d = patches.Patch(linestyle='solid', color='black', label='Wynik symulacji')
plt.legend(handles=[pop_c, pop_d, pop_b, pop_a])

plt.title('Średnie opóźnienie w systemie z zaznaczonym przedziałem ufności')
plt.xlabel(r'λ [$s^{-1}$]')
plt.ylabel('Średnie opóźnienie [s]')
plt.savefig('opoznienia.svg')
plt.show()

df = DataFrame(lst_of_dcts)
df.to_csv('wyniki.csv', index=False)
