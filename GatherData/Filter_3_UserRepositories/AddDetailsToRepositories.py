import os
import random
import pandas as pd
import json
from tqdm import tqdm
import sys
sys.path.append(os.getcwd())
from Utils.GithubAPI import GithubRequestMachine, RateLimitError
import argparse


def search_for_user_repos(user_login, github_request_machine):
    list_df_repos = []
    page_num = 0
    while True:
        df_repos = github_request_machine.user_service_endpoint(user_login=user_login, service='repos', page_num=page_num, 
                                                                retry_after_rate_limit=True)
        # it is possible that a user just have exactly 200 repos. Then the final page have 100 but there is no next page.
        if len(df_repos) == 0:
            break
        list_df_repos.append(df_repos)
        if len(df_repos) < 100:
            break
        page_num += 1
    df_repos = pd.concat(list_df_repos, ignore_index=True)
    return df_repos

def store_single_user_repo(user_login, github_request_machine):
    user_directory_path = os.path.join('Database/UserData/', user_login)
    os.makedirs(user_directory_path, exist_ok=True)
    # construct the csv file
    repo_csv_path = os.path.join(user_directory_path, 'repos.csv')
    # "Cache" the file
    if os.path.exists(repo_csv_path):
        return
    df_repos = search_for_user_repos(user_login, github_request_machine)
    df_repos['user_login'] = user_login
    # save to csv
    df_repos.to_csv(repo_csv_path, index=False)

def store_users_repos(df_users, github_request_machine):
    for i in tqdm(range(len(df_users))):
        user_login = df_users.iloc[i]['login']
        try:
            store_single_user_repo(user_login, github_request_machine)
        except:
            print(f"Trouble: {i} {user_login}")
            continue

            
def init_user_info_directory(df_users):
    for i in tqdm(range(len(df_users))):
        user_login = df_users.iloc[i]['login']
        user_directory_path = os.path.join('Database/UserData/', user_login)
        os.makedirs(user_directory_path, exist_ok=True)
        # saves the user's information
        user_info = df_users.iloc[i].to_dict()
        with open(os.path.join(user_directory_path, 'user_info.json'), 'w') as json_file:
            json.dump(user_info, json_file, indent=4)

def add_language_details(df_repos, github_request_machine):
    # Add language details
    df_repos['language_details'] = None
    df_repos.reset_index(drop=True, inplace=True)
    for i in range(len(df_repos)):
        repo_full_name = df_repos.iloc[i]['full_name']
        df_repos.at[i, 'language_details'] = github_request_machine.repository_service_endpoint(repo_full_name, 'languages', retry_after_rate_limit=True)
    return df_repos

def add_branch_details(df_repos, github_request_machine):
    # Add branches detail
    df_repos['num_branches'] = None
    df_repos.reset_index(drop=True, inplace=True)
    for i in range(len(df_repos)):
        repo_full_name = df_repos.iloc[i]['full_name']
        branches = github_request_machine.repository_service_endpoint(repo_full_name, 'branches', retry_after_rate_limit=True)
        df_repos.at[i, 'num_branches'] = len(branches)
    return df_repos

def add_contributor_details(df_repos, github_request_machine):
    # Add commit details
    df_repos['contributors'] = None
    df_repos.reset_index(drop=True, inplace=True)
    for i in range(len(df_repos)):
        repo_full_name = df_repos.iloc[i]['full_name']
        contributors = github_request_machine.repository_service_endpoint(repo_full_name, 'contributors', retry_after_rate_limit=True)
        df_repos.at[i, 'contributors'] = contributors
    return df_repos


def add_detail_to_single_user_python_repos(user_login, github_request_machine):
    user_directory_path = os.path.join('Database/UserData/', user_login)
    os.makedirs(user_directory_path, exist_ok=True)
    # construct the csv file path
    repo_csv_path = os.path.join(user_directory_path, 'repos.csv')
    if not os.path.exists(repo_csv_path):
        print(f"User {user_login} haven't run store_users_repos yet!")
        return
    # construct a new csv file for filtered python repos
    python_repo_csv_path = os.path.join(user_directory_path, 'python_repo_details.csv')
    # Cache the file
    if os.path.exists(python_repo_csv_path):
        return
    # find all the python "original" repos
    df_repos = pd.read_csv(repo_csv_path)
    df_repos = df_repos[(df_repos['fork'] == False) &                    # Non-forked
                            (df_repos['mirror_url'].isnull()) &          # Not a mirror
                            (df_repos['is_template'] == False) &         # Not a template
                            (df_repos['language'] == 'Python')]          # Language is Python
    
    # add details to them
    df_repos = add_language_details(df_repos, github_request_machine)
    df_repos = add_branch_details(df_repos, github_request_machine)
    df_repos = add_contributor_details(df_repos, github_request_machine)
    # save this to csv
    df_repos.to_csv(python_repo_csv_path, index=False)

def add_details_to_python_repos(df_users, github_request_machine):
    for i in tqdm(range(len(df_users))):
        user_login = df_users.iloc[i]['login']
        try:
            add_detail_to_single_user_python_repos(user_login, github_request_machine)
        except:
            print(f"Trouble: {i} {user_login}")
            continue

def main(api_key, country, start_idx, end_idx):
    github_request_machine = GithubRequestMachine(api_key)

    # clip the df
    df_users = pd.read_csv("Database/TempData/GatherData/Filter_2_DecypherLocation/Results/users_filter_2.csv")
    df_users_country = df_users[df_users['country']== country]
    df_users_to_process = df_users_country[start_idx:end_idx]

    # process the clipped df
    init_user_info_directory(df_users_to_process)
    store_users_repos(df_users_to_process, github_request_machine)
    add_details_to_python_repos(df_users_to_process, github_request_machine)


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Fetch data with API key and filters.")
    parser.add_argument("--API_key", type=str, required=True, help="Your API key")
    parser.add_argument("--country", type=str, required=True, help="Country to fetch data for")
    parser.add_argument("--start", type=int, required=True, help="Start integer value")
    parser.add_argument("--end", type=int, required=True, help="End integer value")

    # Parse arguments
    args = parser.parse_args()
    print(f"start process {args.country} start: {args.start}")
    # run main with these arguments
    main(args.API_key, args.country, args.start, args.end)
    print(f"finish process {args.country} start: {args.start}")



        
        
        