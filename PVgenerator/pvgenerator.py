import numpy as np
import pandas as pd

def generate_pv_series(temperature:pd.DataFrame, irradiance:pd.DataFrame, 
    parameters:dict={
        'Pmpp': 8.18 * 31.2, # maximum power point = maximum power point current * maximum power point voltage
        'FF': (8.18 * 31.2)/(8.89 * 37.8), # fill factor = maximum power point / (short circuit current * open source voltage)
        'Voc': 37.8, # open circuit current
        'Isc': 8.89, # short circuit current
        'T0': 25+273.15, # standard module temperature
        'E0': 1000, # standard irradiance
        'eta_inv': 0.9, # inverter efficiency
        'NOCT': 45.7, # nominal operating cell temperature
        'module_area': 1.6, # size of module
        'module_number':1 # amount of modules
    }, measurementfilter:dict={
        'maximum_temperature':40, # maximum temperature
        'maximum_irradiance':1000 # maximum irridation
    }):
    """
    generates artificial Photo-Voltaic time series from temperature [degree Celsius] and irradiance [Watt/square meter] dataframes.
    """
    assert temperature.shape == irradiance.shape, 'mismatching input shapes'
    assert list(temperature.columns) == list(irradiance.columns), 'mismatching column names'
    # read inputs:
    T = temperature.to_numpy()
    E = irradiance.to_numpy()
    p = parameters
    # remove faulty measurements:
    Tmask = T >= measurementfilter['maximum_temperature']
    Emask = E >= measurementfilter['maximum_irradiance']
    T[Tmask]=np.nan
    E[Emask]=np.nan
    # calculate cell temperature:
    Tcell = T + (p['NOCT']-20)/800 * E + 275.15
    # calculate photovoltaic power:
    P = (
        p['FF'] * p['Isc'] * p['Voc'] * p['T0'] / (p['E0'] * np.log(10**6 * p['E0']) ) 
        * (E * np.log(10**6 * E))/Tcell * p['eta_inv'] * p['module_number'] 
    )
    # make dataframe:
    P = pd.DataFrame(P, columns=temperature.columns)
    return P

# the script generating the series dataframe:
# The inputs are dataframes with the columns temperature and irridation
if __name__ == "__main__":
    import os
    # load data into dataframe:
    for folder in os.walk('./datasets'):
        # find the locations:
        locations = [names.split(' ')[0] for names in folder[2]]
        unique_locations = set(locations)
        # load the datasets:
        datasets = {u:None for u in unique_locations}
        for f in folder[2]:
            df = pd.read_csv('./datasets/'+f, index_col=0, sep=";", na_values = 'NULL')
            loc = f.split(' ')[0]
            if datasets[loc] is None:
                datasets[loc] = df
            else:
                datasets[loc] = datasets[loc].append(df) 
    # make single dataframes for data:
    temperature = pd.concat([datasets[loc][datasets[loc].columns[0]] for loc in list(datasets.keys())],1)
    temperature.columns = list(datasets.keys())
    irridation = pd.concat([datasets[loc][datasets[loc].columns[1]] for loc in list(datasets.keys())],1)
    irridation.columns = list(datasets.keys())
    # generate artifical loads:
    photovoltaic_loads = generate_pv_series(temperature, irridation)
    # store data:
    photovoltaic_loads.to_excel('generated loads.xlsx')
