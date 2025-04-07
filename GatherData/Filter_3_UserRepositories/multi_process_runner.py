import os
import sys

# Change it to your google drive path where this notebook located.
drive_path = '/Users/samyiin/Projects/ZipfLawAnalysis'
os.chdir(drive_path)
sys.path.append(drive_path)

import random
import pandas as pd
import json
from tqdm import tqdm
import subprocess
from multiprocessing import Pool
from Utils.Secrete import SecreteLoader

def run_script(params):
    """
    Run the script with specific parameters.
    """
    command = [
        'python', 'GatherData/Filter_3_UserRepositories/AddDetailsToRepositories.py',
        '--API_key', params['API_key'],
        '--country', params['country'],
        '--start', params['start'],
        '--end', params['end']
    ]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Print stdout line by line
        for line in process.stdout:
            print(line, end="")  # End with "" to avoid adding extra newlines
        for error in process.stderr:
            print(error, end="")
        
    except subprocess.CalledProcessError as e:
        print(f"Error for {params['country']}:\n{e.stderr}")
if __name__ == "__main__":
    secrete_loader = SecreteLoader()
    
    parameter_sets = [
        # # Sam
        # {'API_key': secrete_loader.get_github_apikey('Sam'), 
        #  'country': 'United States', 'start': '100', 'end': '100000'},
        # # Hamzeh
        # {'API_key': secrete_loader.get_github_apikey('Hamzeh'), 
        #  'country': 'United States', 'start': '3600', 'end': '7200'},
        # # Yonghao
        # {'API_key': secrete_loader.get_github_apikey('Yonghao'), 
        #  'country': 'United States', 'start': '7200', 'end': '10800'},
        # # Adi
        # {'API_key': secrete_loader.get_github_apikey('Adi'), 
        #  'country': 'United States', 'start': '10800', 'end': '14400'},
        # # Maha
        # {'API_key': secrete_loader.get_github_apikey('Maha'), 
        #  'country': 'United States', 'start': '14400', 'end': '18000'},
        # # Bakri
        # {'API_key': secrete_loader.get_github_apikey('Bakri'), 
        #  'country': 'United States', 'start': '18000', 'end': '21600'}, 
        # # Yosef
        # {'API_key': secrete_loader.get_github_apikey('Yosef'), 
        #  'country': 'United States', 'start': '21600', 'end': '25200'}, 
        # # Eviatar
        # {'API_key': secrete_loader.get_github_apikey('Eviatar'),
        #  'country': 'United States', 'start': '25200', 'end': '28800'}, 
        # # Itay
        # {'API_key': secrete_loader.get_github_apikey('Itay'),
        #  'country': 'United States', 'start': '28800', 'end': '32400'}, 
        # # Daniel
        # {'API_key': secrete_loader.get_github_apikey('Daniel'), 
        #  'country': 'United States', 'start': '32400', 'end': '36000'}, 
        # David
        {'API_key': secrete_loader.get_github_apikey('David'), 
         'country': 'China', 'start': '0', 'end': '1000000'}, 
        # # Tehila
        # {'API_key': secrete_loader.get_github_apikey('Tehila'),
        #  'country': 'China', 'start': '3600', 'end': '7200'}, 
        # # Mohanmmod
        # {'API_key': secrete_loader.get_github_apikey('Mohanmmod'), 
        #  'country': 'China', 'start': '7200', 'end': '11000'}, 
        # # Majd
        # {'API_key': secrete_loader.get_github_apikey('Majd'), 
        #  'country': 'China', 'start': '11000', 'end': '15169'}, 
        ]
    # Run the scripts concurrently
    with Pool(processes=len(parameter_sets)) as pool:  # Create a pool with 20 processes
        pool.map(run_script, parameter_sets)



