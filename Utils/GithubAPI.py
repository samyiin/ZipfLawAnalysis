import requests
import pandas as pd
import time


'''
Define some custom error types
'''


class RateLimitError(Exception):
    def __init__(self, message="Rate limit exceeded", wait_time=None):
        super().__init__(message)
        self.wait_time = wait_time  # e.g., seconds to wait before retrying

    def __str__(self):
        base_message = super().__str__()
        return base_message


class UnknownError(Exception):
    def __init__(self):
        message = "Unknown Error"
        super().__init__(message)

    def __str__(self):
        base_message = super().__str__()
        return base_message


class GithubRequestMachine:
    def __init__(self, github_fine_grained_access_token):
        self.access_token = github_fine_grained_access_token

    def make_secure_request(self, url):
        # Replace 'YOUR_ACCESS_TOKEN' with your actual GitHub personal access token
        headers = {'Authorization': f'token {self.access_token}',
                   "X-GitHub-Api-Version": "2022-11-28"}
        while True:
            # Make a GET request
            try:
                response = requests.get(url, headers=headers)
                return response
            except:
                # Hit the secondary limit:
                print("Hit secondary limit: sleep for 5 seconds")
                time.sleep(5)


    def make_github_request(self, url, retry_after_rate_limit=False):
        response = self.make_secure_request(url)
        while response.status_code != 200:
            if int(response.headers.get('x-ratelimit-remaining')) == 0:
                reset_time = int(response.headers.get("x-ratelimit-reset"))
                wait_time = reset_time - int(time.time())
                if not retry_after_rate_limit:
                    raise RateLimitError(wait_time=wait_time)
                # else we will wait and retry
                print(f"Hit Rate Limit, sleep for {wait_time + 5} seconds...")
                time.sleep(wait_time + 5)
                # try again: This time it supposed to work
                response = self.make_secure_request(url)
            else:
                # other type of failure
                print(response)
                raise UnknownError()
        # if response.status_code == 200:
        response_json = response.json()
        return response_json

    @staticmethod
    def _construct_search_query(dic_constraints):
        constraints = []
        for k, v in dic_constraints.items():
            if v is None:
                continue
            constraints.append(k.strip() + ":" + v.strip())
        query = "+".join(constraints)
        return query

    '''
    The website for how to access search endpoint:
    https://docs.github.com/en/rest/search/search?apiVersion=2022-11-28
    The website for how to construct search query is here:
    https://docs.github.com/en/search-github/searching-on-github
    So far this end point supports target_type: 'users', 'repositories', 'code', 'commits'
    '''

    def search_endpoint(self, target_type, dic_constraints, page_num, retry_after_rate_limit=False):
        # construct query
        query = self._construct_search_query(dic_constraints)
        url = f'https://api.github.com/search/{target_type}?q={query}&per_page=100&page={page_num}'
        res = self.make_github_request(url, retry_after_rate_limit)
        return res

    '''
    The website for how to access repository endpoint, and all services of this endpoint:
    https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28
    So far the services we use:
    'languages': list the size of each language in this repo
    'contributors': check who and how much each contributed
    'branches': list all the branches of this repo
    'stats/commit_activity': number of commits in each day of the week in the latest 52 weeks
    'stats/contributors': number of contributors in this repo
    'commits': all the commits in this repo
    '''

    def repository_service_endpoint(self, repo_name, service, retry_after_rate_limit=False):
        url = f'https://api.github.com/repos/{repo_name}/{service}'
        res = self.make_github_request(url, retry_after_rate_limit)
        return res

    '''
    The website for how to access user endpoint, and all services of this endpoint:
    https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28
    So far the services we use:
    None: don't use this feature, this feature is movevd to get_user_info
    'repos': list all the repository for a user
    'events': list all events of the user
    '''

    def user_service_endpoint(self, user_login, service, page_num, retry_after_rate_limit=False):
        url = f'https://api.github.com/users/{user_login}/{service}?per_page=100&page={page_num}'
        res = self.make_github_request(url, retry_after_rate_limit)
        df_repos = pd.DataFrame(res)
        return df_repos

    '''
    Get information of a single user from the user endpoint
    We create a separate method so that the caching will not take too much time
    '''

    def user_endpoint(self, user_login, retry_after_rate_limit=False):
        url = f'https://api.github.com/users/{user_login}'
        res = self.make_github_request(url, retry_after_rate_limit)
        return res

    def check_rate_limit(self):
        """
        This function will check the rate limit left for me
        :return:
        """
        url = 'https://api.github.com/rate_limit'
        res = self.make_github_request(url)
        df = pd.DataFrame.from_dict(res['resources'], orient='index')
        print(df)
