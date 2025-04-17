import pandas as pd
import numpy as np
import os
from Utils.GmailAPI import GmailCloudService

email_1_expected_columns = ['nickname', 'login', 'id', 'type', 'site_admin', 'name', 'company', 'blog',
                            'location', 'email', 'hireable', 'bio', 'twitter_username',
                            'public_repos', 'public_gists', 'followers', 'following', 'created_at',
                            'updated_at', 'country', 'claimed_country', 'native_language',
                            'parent_native_language', 'requires_result', 'sent_email_1',
                            'sent_email_1_date', 'note', 'no_bother']

email_1_html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Email</title>
</head>
<body>
    <p>Dear USER_NAME,</p>

    <p>
        I hope this message finds you well. My name is Sam, and I am part of 
        Prof. Dror Feitelson’s Lab at the Hebrew University of Jerusalem. Our team conducts research on variable naming preferences among programmers, 
        and we are currently exploring differences between programmers in the USA and China.
    </p>

    <p>
        I came across your GitHub profile and selected your repositories due to its relevance and quality, and I truly appreciate the effort you’ve put into it.
        We would greatly appreciate your help in answering three quick questions:
    </p>

    <ol>
        <li><strong>Which country are you located in?</strong></li>
        <li><strong>Are you a native English speaker?</strong></li>
        <li><strong>Are both of your parents native English speakers?</strong></li>
    </ol>

    <p>
        For clarity, a native English speaker is someone who has learned and used English as their first 
        language from early childhood and continues to use it as their primary language.
    </p>

    <p><em>Please be assured that:</em></p>
    <ol>
        <li>This is a genuine research inquiry; we are not promoting any products or services.</li>
        <li>Your participation is entirely voluntary, and you may choose not to respond without any consequences.</li>
        <li>Any information you provide will be kept confidential and used solely for research purposes.</li>
        <li>Data will be securely stored and we will not publish any personally identifiable details.</li>
    </ol>

    <p>
        <span style="color: purple; font-weight: bold;">Thank you for considering this request. Your answers would be invaluable to our research.</span>
    </p>

    <p>Best regards,</p>

    <p>
        <strong>Prof. Dror G. Feitelson</strong><br>
        <a href="https://orcid.org/0000-0002-2733-7709">https://orcid.org/0000-0002-2733-7709</a><br>
        <a href="https://www.cs.huji.ac.il/w~feit/">https://www.cs.huji.ac.il/w~feit/</a>
    </p>

    <p>
        <strong>Hsin-Chun Yin (Sam)</strong><br>
        <a href="https://orcid.org/0009-0007-5036-4493">https://orcid.org/0009-0007-5036-4493</a><br>
        <a href="https://www.linkedin.com/in/samyiin">www.linkedin.com/in/samyiin</a>
    </p>

    <p>
        Experimental Systems Lab<br>
        Hebrew University of Jerusalem
    </p>
</body>
</html>

"""

class SendEmailOneManager:
    def __init__(self, auto_update_response=False, root_dir="Utils/"):
        # resume the latest state
        self.database = os.path.join(root_dir, 'SentEmailControlSystem/SentEmail1/')
        self.all_state_code = [os.path.splitext(f)[0] for f in os.listdir(self.database)
                               if os.path.isfile(os.path.join(self.database, f)) and f.endswith('.csv')]
        self.all_state_code = [int(x) for x in self.all_state_code]
        self.latest_state_code = max(self.all_state_code)
        self.df_latest_state = pd.read_csv(os.path.join(self.database, f'{self.latest_state_code}.csv'))
        # Check if df_all_users contains the right columns
        if not set(self.df_latest_state.columns) == set(email_1_expected_columns):
            raise ValueError("The DataFrame does not match the expected columns.")

        # this is just for backup, incase anything went wrong
        self.sent_email_list_file_path = os.path.join(self.database,'backup_sent_email_list.txt')

        # all the responses: If there are new responses, appeand to the end of the csv and call the update responses
        self.response_csv = os.path.join(root_dir, "SentEmailControlSystem/Email1Responses/responses.csv")
        if os.path.exists(self.response_csv) and auto_update_response:
            self.email_1_update_responses()

    def email_1_select_users(self, k, country, random_state=42):
        '''
        So far country supports United States or China
        '''
        # Exclude the sent users, Select the user of certain countries
        df_user_pool = self.df_latest_state[(self.df_latest_state['sent_email_1'] != True) &
                                            (self.df_latest_state['country'] == 'United States')]
        # then randomly pick k from them
        random_rows = df_user_pool.sample(n=k, random_state=random_state)
        return random_rows


    def email_1_mark_sent_users(self, send_user_rows, sent_date):
        """
        The send_user_rows must be from email_1_select_users else it won't be correct
        :param send_user_rows:
        :param sent_date:
        :return:
        """
        self.df_latest_state.loc[send_user_rows.index, 'sent_email_1'] = True
        self.df_latest_state.loc[send_user_rows.index, 'sent_email_1_date'] = sent_date
        self.save_latest_state()

    def email_1_get_all_users(self):
        return self.df_latest_state
        
    def email_1_get_already_sent_users(self):
        return self.df_latest_state[self.df_latest_state['sent_email_1'] == True]

    def email_1_double_check_exclude_sent_users(self, df_sending_users):
        df_already_sent = self.email_1_get_already_sent_users()
        common_emails = df_sending_users['email'].isin(df_already_sent['email'])
        df_matching_rows = df_sending_users[common_emails]
        return df_matching_rows

    def email_1_send_single_email(self, user_name, user_email):
        updated_html_content = email_1_html_content.replace("USER_NAME", user_name)
        subject = 'Research Inquiry from Experimental Systems Lab at HUJI'
        GmailCloudService().send_email(user_email, subject, updated_html_content, content_is_html=True)

    def email_1_send_multiple_email(self, df_users):
        '''
        in case of failiure, save the sent email before sending email
        This file will renew everytime we call email_1_send_multiple_email
        '''
        loaded_emails = []
        with open(self.sent_email_list_file_path, "w") as file:
            file.write("")
        
        for i, row in df_users.iterrows():
            # Reading the emails back from the file
            with open(self.sent_email_list_file_path, "r") as file:
                loaded_emails = [line.strip() for line in file]  # Remove trailing newline characters
                
            loaded_emails.append(row['email'])
            
            # Writing the emails to a file
            with open(self.sent_email_list_file_path, "w") as file:
                for email in loaded_emails:
                    file.write(email + "\n")  # Write each email followed by a newline

            # finally send the email
            self.email_1_send_single_email(row['nickname'], row['email'])

    def email_1_send_random_selected_email(self, k, country, today_date):
        '''
        country must be either 'United States' or "China'
        '''
        if country not in ['United States', 'China']:
            raise ValueError
        # select k users
        random_rows = self.email_1_select_users(k, country)
        # check if the email address already been sent
        repeated_emails = len(self.email_1_double_check_exclude_sent_users(random_rows))
        if repeated_emails > 0:
            raise ValueError
        # send to these users for here we just print whom to send: self.email_1_send_multiple_email(random_rows)
        for i, row in random_rows.iterrows():
            print(row['nickname'], row['email'])
        
        # if everything goes well, simple store the result (If not, then we need to see who is sent)
        self.email_1_mark_sent_users(random_rows, today_date)

    def email_1_update_responses(self):
        """
        All the responds of email one will be under self.response_csv
        It should countain these columns:
        nickname, email, claimed_country, native_language, parent_native_language, no_bother, requires_result, note
        Self use so no need sanity check
        """
        responses = pd.read_csv(self.response_csv)
        # check responses is correct
        if responses['email'].duplicated().any():
            raise ValueError("There are duplicate emails in the response data: check your response and manually resolve this!")
            
        response_expected_columns = ['nickname', 'email', 'claimed_country', 'native_language', 'parent_native_language', 'no_bother', 'requires_result', 'note']
        if not set(responses.columns) == set(response_expected_columns):
            raise ValueError("The response DataFrame does not match the expected columns.")
        # align the email column
        responses['email'] = responses['email'].str.strip()
        self.df_latest_state['email'] = self.df_latest_state['email'].str.strip()
        # change the value of respond
        for column in ['no_bother', 'requires_result']:
            responses[column] = responses[column].astype(int)
            responses[column] = responses[column].map({1: True, 0: False})

        # step 1: double check if any of the email in responses is duplicated or not exist in self.df_latest_state['email']
        email_counts = self.df_latest_state['email'].value_counts()
        # Find emails in responses that appear more than twice in self.df_latest_state
        duplicates_in_state = [
            email for email in responses['email']
            if email_counts.get(email, 0) > 2
        ]
        if duplicates_in_state:
            raise ValueError(f"Emails appear more than twice in self.df_latest_state: {duplicates_in_state}")
        # Find emails in responses that do not exist in self.df_latest_state
        missing_in_state = [
            email for email in responses['email']
            if email not in email_counts
        ]
        if missing_in_state:
            print(f"Emails in responses not found in self.df_latest_state: {missing_in_state}")
            
        # step 2: nickname column is repeated, drop it
        if 'nickname' in responses.columns:
            responses = responses.drop(columns=['nickname'])
        
        # step 3: re-initialize the result of self.df_latest_state
        # for columns in [claimed_country, native_language, parent_native_language, no_bother, requires_result, note]
        #     if sent_email_1 == True, then fillin "NoRespond", else fillin Nan
        for column in ['claimed_country', 'native_language', 'parent_native_language', 'no_bother', 'requires_result', 'note']:
            self.df_latest_state[column] = self.df_latest_state[column].astype('object')
            self.df_latest_state[column] = (self.df_latest_state['sent_email_1'].apply(lambda x: "NoRespond" if x==True else None))
                        
        # step 4: update columns: claimed_country, native_language, parent_native_language, no_bother, requires_result, note  
        for column in ['claimed_country', 'native_language', 'parent_native_language', 'no_bother', 'requires_result', 'note']:
            map_email_to_column = responses.set_index('email')[column]
            self.df_latest_state.loc[
                self.df_latest_state['email'].isin(responses['email']),
                column
            ] = self.df_latest_state['email'].map(map_email_to_column)
        

        # setp 5: save latest state
        self.save_latest_state()

    def email_1_get_responded_users(self):
        # I don't have a no_response column, my bad, so I will enforce native_language must be some value
        return self.df_latest_state[(self.df_latest_state['sent_email_1'] == True) & 
                                    (self.df_latest_state['native_language'] != 'NoRespond')]
        
    def save_latest_state(self):
        # should check if the state code already exist?
        self.df_latest_state.to_csv(os.path.join(self.database, f'{self.latest_state_code + 1}.csv'),
                                    index=False)
        # update the latest state
        self.update_latest_state()

    def update_latest_state(self):
        self.all_state_code = [os.path.splitext(f)[0] for f in os.listdir(self.database)
                               if os.path.isfile(os.path.join(self.database, f)) and f.endswith('.csv')]
        self.all_state_code = [int(x) for x in self.all_state_code]
        self.latest_state_code = max(self.all_state_code)
        self.df_latest_state = pd.read_csv(os.path.join(self.database, f'{self.latest_state_code}.csv'))
        if not set(self.df_latest_state.columns) == set(email_1_expected_columns):
            print("The DataFrame does not match the expected columns.")
            raise ValueError


    
