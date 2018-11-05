import cobra.io.json
import pytfa.io.json
from etfl.io.json import load_json_model

import numpy as np

from cobra.flux_analysis import single_gene_deletion

from tqdm import tqdm

import time


solver = 'optlang-gurobi'
#
# ecoli_fba = cobra.io.json.load_json_model('models/iJO1366_T0E0N0__20180606_121758.json')
# ecoli_fba.solver = solver
# ecoli_tfa = pytfa.io.json.load_json_model('models/iJO1366_T1E0N0__20180606_121751.json')
# ecoli_tfa.solver = solver

ecoli = load_json_model('models/iJO1366_T0E1N1_431_enz_128_bins__20180926_135704.json')
# ecoli = load_json_model('models/RelaxedModel '
#                         'iJO1366_T1E1N1_430_enz_256_bins__20180903_141648.json')
ecoli.solver = solver
ecoli.solver.configuration.verbosity = 1
ecoli.solver.configuration.tolerances.feasibility = 1e-9
try:
    ecoli.solver.problem.Params.NumericFocus = 3
except AttributeError:
    pass

ecoli.solver.configuration.presolve = True
ecoli.optimize()

print('Growth               : {}'.format(ecoli.solution.f))
print(' - Ribosomes produced: {}'.format(ecoli.solution.raw.EZ_rib))
print(' - RNAP produced: {}'.format(ecoli.solution.raw.EZ_rnap))



# --

def ko_gene(model, gene_id):
    # DIRTYYYY
    rxn_id = '{}_transcription'.format(gene_id)
    try:
        the_trans = model.reactions.get_by_id(rxn_id)
        initial_value = the_trans.upper_bound

        the_trans.upper_bound = 0

        growth = model.slim_optimize()
        #
        # the_trans.upper_bound = initial_value
    except KeyError:
        growth = np.nan

    return growth


def timeit(method):
    def timed(*args, **kwargs):
        if 'log_data' in kwargs:
            log_data = kwargs.pop('log_data')
        else:
            log_data = dict()

        ti = time.time()
        result = method(*args, **kwargs)
        tf = time.time()


        name = method.__name__
        log_data[name] = tf-ti

        print('{}: {}s'.format(method.__name__, tf-ti))

        return result
    return timed

@timeit
def ko_etfl(model):
    growth = dict()

    for g in tqdm(model.genes):
        with model as model:
            growth[g.id] = ko_gene(model, g.id)
    return growth

@timeit
def ko_fba(model):
    return single_gene_deletion(model)

@timeit
def ko_tfa(model):
    return single_gene_deletion(model)


log_data = dict()

# ko_fba(ecoli_fba, log_data = log_data)
# ko_tfa(ecoli_tfa, log_data = log_data)
values = ko_etfl(ecoli, log_data = log_data)

import pandas as pd
df = pd.DataFrame.from_dict(values, orient='index')
df.to_csv('outputs/gene_essentiality_etfl.csv')
