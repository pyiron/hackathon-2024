import scipy.integrate as sit
import numpy as np
import scipy.optimize as so
import scipy.interpolate as si
from scipy.special import entr
from scipy.constants import Boltzmann, eV
from abc import ABC, abstractmethod
import dataclasses
import pandas as pd

kB = Boltzmann / eV


def run_job(pr, name, structure, T):
    j = pr.create.job.Vasp([name, "T", T])
    if not j.status.initialized:
        return j
    j.structure = structure
    j.input.incar["ISMEAR"] = -1
    j.input.incar["SIGMA"] = kB * T
    j.input.incar["NEDOS"] = 5000
    j.set_encut(400)  # blazej SFE paper
    j.set_kpoints([34] * 3)
    j.calc_static()
    j.server.queue = "s_cmmg"
    j.server.cores = 32
    j.server.run_time = 10 * 60
    j.run()
    return j


def get_dataframe(pr):
    tab = pr.create.table("Table", delete_existing_job=True)
    tab.add["F"] = lambda j: j.content["output/generic/dft/energy_free"][-1]
    tab.add["E0"] = lambda j: j.content["output/generic/dft/energy_zero"][-1]
    tab.add.get_total_number_of_atoms
    tab.add.get_sigma
    tab.run()
    df = tab.get_dataframe()
    df["f"] = df.F / df.Number_of_atoms
    df["e0"] = df.E0 / df.Number_of_atoms
    df["fel"] = df.F - df.E0
    df["T"] = df.sigma / kB
    return df


def integrate(y, x):
    if len(np.unique(np.diff(x))) == 1:
        return sit.romb(y, x[1] - x[0])
    else:
        return sit.trapezoid(y=y, x=x)


def efermi(e, T, mu):
    if T != 0:
        return 1 / (1 + np.exp(((e - mu) / kB / T)))
    else:
        return 1 * (e <= mu)


def occ(e, n, T, mu):
    f = efermi(e, T, mu)
    return integrate(f * n, e)


def find_mu(e, n, T, N, mu0=None):
    """
    Get Fermi energy from a given DOS at a given temperature following Fermi-Dirac distribution

    Args:
        e (np.array): Energies
        n (np.array): Frequencies / bin heights
        T (float): Temperature
        N (int): Number of electrons
        mu0 (float): Starting value for minimization

    Returns:
        (float): Fermi energy
    """
    if mu0 is None:
        mu0 = 0
    # https://journals.aps.org/prb/abstract/10.1103/PhysRevB.107.195122
    ret = so.minimize_scalar(
        lambda mu: (occ(e, n, T, mu) - N) ** 2,
        bracket=(e.min(), mu0, e.max()),
        tol=1e-7,
    )
    # problematic: at low T
    # ret = so.basinhopping(lambda mu: (occ(e, n, T, mu[0]) - N)**2, x0=[mu0],
    #                       minimizer_kwargs={'bounds': [(e.min(), e.max())]})
    if ret.success:
        if abs(occ(e, n, T, ret.x) - N) > 0.01:
            print(f"Got {occ(e, n, T, ret.x)} instead of {N}!")
        return ret.x
    else:
        return mu0


def find_fermi(e, n, T, N, mu0=None):
    mu = find_mu(e, n, T, N, mu0=mu0)
    f = efermi(e, T, mu)
    return f, mu


def energy_entropy(e, D, f, mu, gamma=2):
    # factor 2 to account for two spin channels -> assumption density is *not* spin polarized
    s = entr(f) + entr(1 - f)  # eq. 9
    S = gamma * kB * integrate(D * s, e)  # eq. 8
    U = integrate(D * (f - 1 * (e <= mu)) * e, e)  # eq. 7 This one works
    return U, S


@dataclasses.dataclass(frozen=True)
class Dos:
    energy: np.array
    density: np.array

    def fermi_distribution(self, T, mu):
        if T != 0:
            return 1 / (1 + np.exp(((self.energy - mu) / kB / T)))
        else:
            return 1 * (self.energy <= mu)

    def occupation(self, T, mu):
        f = self.fermi_distribution(T, mu)
        return integrate(f * self.density, self.energy)


class DosMode(ABC):
    @abstractmethod
    def get_dos(self, job):
        pass

    @abstractmethod
    def __repr__(self):
        pass


class DOSCAR(DosMode):
    def get_dos(self, job):
        return (
            job.content["output/electronic_structure/dos/energies"],
            job.content["output/electronic_structure/dos/tot_densities"][0],
        )

    def __repr__(self):
        return "DOSCAR()"


class InterpolatedDOSCAR(DosMode):
    def __init__(self, npoints=10_000, method="slinear"):
        self.npoints = npoints
        self.method = method

    def get_dos(self, job):
        DOS = si.interp1d(
            job.content["output/electronic_structure/dos/energies"],
            job.content["output/electronic_structure/dos/tot_densities"][0],
            kind="cubic",
        )
        energy = np.linspace(
            job.content["output/electronic_structure/dos/energies"].min(),
            job.content["output/electronic_structure/dos/energies"].max(),
            10000,
        )
        density = DOS(energy)
        return energy, density

    def __repr__(self):
        return f"InterpolatedDOSCAR({self.npoints}, {self.method})"


class Gaussian(DosMode):
    def __init__(self, smear=1e-1, npoints=5000):
        self.smear = smear
        self.npoints = npoints

    def _dos_gauss(self, e, w):
        ex = np.linspace(e.min() - 1, e.max() + 1, self.npoints)
        prefactor = 1 / len(e) * 1 / np.sqrt(np.pi) / self.smear
        ediff = ex[:, np.newaxis, np.newaxis, np.newaxis] - e[np.newaxis, ...]
        return ex, prefactor * (w * np.exp(-((ediff / self.smear) ** 2))).sum(
            axis=(1, 2, 3)
        )

    def get_dos(self, job):
        eigenvals = job.content["output/generic/dft/bands/eig_matrix"]
        NSPINS, NKPTS, NBANDS = eigenvals.shape
        # bring the weights in the same shape as eig values
        weights = job.content["output/electronic_structure/k_weights"].reshape(1, -1, 1)
        energy, density = self._dos_gauss(
            e=eigenvals,
            w=weights,
        )
        # ensures integrate(density, energy) == NBANDS*NSPINS
        density *= 3 - NSPINS
        return energy, density

    def __repr__(self):
        return f"SelfRolledGauss({self.smear}, {self.npoints})"


def get_eigenvalues(job):
    eigenvals = job.content["output/generic/dft/bands/eig_matrix"]
    weights = job.content["output/electronic_structure/k_weights"]
    weights *= 3 - eigenvals.shape[0]
    return {
        "energy": eigenvals.flatten(),
        "density": weights.flatten(),
    }


def electronic_entropy_from_job(j, Ts, mode=DOSCAR()):
    # pre tabulated DOS sucks, unless you happened to have set a high NEDOS
    energy, density = mode.get_dos(j)

    def iter(T):
        f, mu = find_fermi(
            energy,
            density,
            T,
            j.get_nelect(),
            mu0=j.content["output/electronic_structure/efermi"],
        )
        U, S = energy_entropy(energy, density, f, mu)
        return {"T": T, "U": U, "S": S, "mu": mu}

    df = pd.DataFrame([iter(T) for T in Ts])
    df["s"] = df.S / len(j.structure)
    df["u"] = df.U / len(j.structure)
    df["TS"] = df["T"] * df["S"]
    df["Ts"] = df["T"] * df["s"]
    df["Fel"] = df.U - df.TS
    df["fel"] = df.u - df.Ts
    return df
