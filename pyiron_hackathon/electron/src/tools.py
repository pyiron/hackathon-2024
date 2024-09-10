from scipy.constants import Boltzmann, eV

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
    tab.add["U"] = lambda j: j.content["output/generic/dft/energy_int"][-1]
    tab.add.get_total_number_of_atoms
    tab.add.get_sigma
    tab.run()
    df = tab.get_dataframe()
    df["f"] = df.F / df.Number_of_atoms
    df["e0"] = df.E0 / df.Number_of_atoms
    df["u"] = df.U / df.Number_of_atoms
    df["fel"] = df.F - df.E0
    df["T"] = df.sigma / kB
    df.sort_values(by="T", inplace=True)
    return df
