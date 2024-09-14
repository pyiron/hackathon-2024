import numpy as np
from scipy.special import entr
from scipy.constants import Boltzmann, eV

kB = Boltzmann / eV


def fermi_distribution(energy, temperature, fermi_energy):
    if temperature > 0:
        return 1 / (1 + np.exp(((energy - fermi_energy) / kB / temperature)))
    else:
        return 1 * (energy <= fermi_energy)


def get_fermi_energy(E, D, T, N, n_steps=30):
    mu = E.min()
    dmu = np.std(E)
    for _ in range(n_steps):
        if np.sum(fermi_distribution(E, T, mu) * D[:, None]) > N:
            mu -= dmu
        else:
            mu += dmu
        dmu /= 2
    return mu


def get_eigenvalues(job):
    eigenvals = job.content["output/generic/dft/bands/eig_matrix"]
    weights = job.content["output/electronic_structure/k_weights"]
    weights *= 3 - eigenvals.shape[0]
    return {
        "density": weights.squeeze(),
        "energy": eigenvals.squeeze(),
    }


def get_s(f):
    return entr(f) + entr(1 - f)


def get_S(E, D, T, N=12, gamma=1):
    fermi_energy = get_fermi_energy(E, D, T, N)
    f = fermi_distribution(E, T, fermi_energy)
    return gamma * kB * np.sum(get_s(f) * D[:, None])


def get_U(E, D, T, N=12):
    fermi_energy = get_fermi_energy(E, D, T, N)
    f = fermi_distribution(E, T, fermi_energy)
    fermi_energy_0 = get_fermi_energy(E, D, 0, N)
    return np.sum(D[:, None] * (f - (E < fermi_energy_0)) * (E - fermi_energy))
