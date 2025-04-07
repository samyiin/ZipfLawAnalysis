import numpy as np
import pandas as pd

from functools import reduce


# Define a custom compute_metrics function
def compute_metrics(eval_pred):
    logits, labels = eval_pred  # eval_pred returns logits and true labels
    predictions = np.argmax(logits, axis=-1)  # Convert logits to predicted class indices
    accuracy = (predictions == labels).mean()  # Calculate accuracy
    return {"accuracy": accuracy}


def compute_metrics_additional(eval_pred):
    """
    Compute precision, recall, F1 score, and accuracy for binary classification.
    Args:
        eval_pred: A tuple (logits, labels) returned by the Trainer's evaluation loop.
    Returns:
        A dictionary containing precision, recall, F1 score, and accuracy.
    """
    logits, labels = eval_pred  # Unpack logits and true labels
    predictions = np.argmax(logits, axis=-1)  # Convert logits to predicted class indices

    # Calculate True Positives, False Positives, False Negatives, True Negatives
    tp = ((predictions == 1) & (labels == 1)).sum()  # True Positives
    fp = ((predictions == 1) & (labels == 0)).sum()  # False Positives
    fn = ((predictions == 0) & (labels == 1)).sum()  # False Negatives
    tn = ((predictions == 0) & (labels == 0)).sum()  # True Negatives

    # Precision, Recall, and F1 Score
    precision = tp / (tp + fp + 1e-9)  # Add epsilon to avoid division by zero
    recall = tp / (tp + fn + 1e-9)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-9)

    precision_inverse = tn / (tn + fn + 1e-9)
    recall_inverse = tn / (tn + fp + 1e-9)

    # Accuracy
    accuracy = (tp + tn) / (tp + fp + fn + tn)

    return {
        "precision": precision,
        "precision_inverse": precision_inverse,
        "recall": recall,
        "recall_inverse": recall_inverse,
        "f1": f1,
        "accuracy": accuracy,
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn
    }


# balance data: same function as in ZipfLawAnalysis/Analysis/Comparison
def balance_data(df):
    # we will use median to balance
    login_counts = df['login'].value_counts()
    target_count = int(login_counts.median())  # You can use other quantiles as needed
    print(f"Target count per login: {target_count}")

    list_balanced_df = []
    for login, count in login_counts.items():
        temp_data = df[df['login'] == login]
        if count > target_count:
            # Random undersampling
            temp_data = temp_data.sample(target_count, random_state=42)
        list_balanced_df.append(temp_data)
    # Keep as is if <= target_count
    balanced_data = pd.concat(list_balanced_df, ignore_index=True)

    return balanced_data


def get_terms_counts(df, name_column='standardized_name', split_names=True):
    """

    :param df:
    :param name_column:
    :param split_names:
    :return:
    """
    df = df.copy()
    if split_names:
        df.loc[:, 'terms'] = df[name_column].str.split('_')
    else:
        df.loc[:, 'terms'] = df[name_column].apply(lambda x: [x])

    flattened_words = df['terms'].explode()

    # Count the occurrences of each word
    word_counts = flattened_words.value_counts()
    df_word_counts = word_counts.reset_index()
    df_word_counts.columns = ['terms', 'counts']
    return df_word_counts


def compare_terms_rank(df, top_k=40, name_column='standardized_name', split_names=False):
    # todo: This could have been solved with df_terms
    # Get the term frequency for each country
    df1 = get_terms_counts(df[df['claimed_country'] == 'China'],
                           name_column=name_column,
                           split_names=split_names)
    df2 = get_terms_counts(df[df['claimed_country'] == 'USA'],
                           name_column=name_column,
                           split_names=split_names)

    # Add ranks to the full dataframes
    df1['rank'] = range(1, len(df1) + 1)
    df2['rank'] = range(1, len(df2) + 1)

    # Set 'terms' as the index
    df1 = df1.set_index('terms')
    df2 = df2.set_index('terms')

    # Extract top-k terms and combine their unique terms
    top_k_df1 = df1.head(top_k)
    top_k_df2 = df2.head(top_k)
    combined_terms = pd.Index(top_k_df1.index).union(top_k_df2.index)

    # Create a DataFrame for comparison
    comparison_df = pd.DataFrame(index=combined_terms)

    # Lookup ranks in full dataframes; use NaN if the term doesn't exist
    comparison_df['rank_in_China'] = comparison_df.index.map(df1['rank'].to_dict())
    comparison_df['rank_in_USA'] = comparison_df.index.map(df2['rank'].to_dict())

    # Sort by ranks for readability
    comparison_df = comparison_df.sort_values(by=['rank_in_China', 'rank_in_USA'],
                                              key=lambda x: pd.to_numeric(x, errors='coerce'))

    return comparison_df


def check_balanced_average(df, criteria_col):
    # Calculate the percentage of single-letter variable names for each login
    login_percentages = (
        df.groupby('login')[criteria_col]
        .mean()
        .reset_index(name='percentage_criteria_true')
    )

    # Calculate the average percentage across all logins
    average_percentage = login_percentages['percentage_criteria_true'].mean()

    return average_percentage


def compare_balanced_average(df, criteria_col):
    percentage_of_single_letters = {'China': check_balanced_average(df[df['claimed_country'] == 'China'].copy(),
                                                                    criteria_col=criteria_col),
                                    'USA': check_balanced_average(df[df['claimed_country'] == 'USA'].copy(),
                                                                  criteria_col=criteria_col)}
    return percentage_of_single_letters


def calculate_balanced_term_frequency(df_terms, user_set, login_col='login', term_col='term'):
    """
    Compare to the function above check_balanced_average
    check_balanced_average can allow any criteria, but it will be average of that one criteria
    This function only have one criterion: sum of unique value, but it allows average on many unique values
    :param df_terms:
    :param user_set:
    :param login_col:
    :param term_col:
    :return:
    """
    df = df_terms.copy()

    # Step 1: Calculate frequency of each term per person
    term_counts_per_person = df.groupby([login_col, term_col]).size().reset_index(name='term_count')

    # Step 2: Calculate total terms per person
    total_terms = df.groupby(login_col).size().reset_index(name='total_terms')

    # Step 3: Merge to compute the normalized frequency for each term per person
    term_counts_per_person = term_counts_per_person.merge(total_terms, on=login_col)
    term_counts_per_person['normalized_frequency'] = term_counts_per_person['term_count'] / term_counts_per_person[
        'total_terms']

    # Step 4: Create all combinations of terms and names
    all_names = df[login_col].unique()
    all_terms = df[term_col].unique()
    all_combinations = pd.MultiIndex.from_product([all_names, all_terms], names=[login_col, term_col]).to_frame(
        index=False)

    # Step 5: Merge with term frequencies, filling missing terms with frequency 0
    term_counts_per_person = all_combinations.merge(
        term_counts_per_person[[login_col, term_col, 'normalized_frequency']],
        on=[login_col, term_col], how='left').fillna(
        {'normalized_frequency': 0})

    # step 6: filter to get only the americans
    term_counts_per_person = term_counts_per_person[term_counts_per_person[login_col].isin(user_set)]

    # Step 7: Calculate the average frequency for each term across all persons
    balanced_frequency = term_counts_per_person.groupby(term_col)['normalized_frequency'].mean().reset_index(
        name='balanced_frequency')

    return balanced_frequency


def calculate_term_counts_on_all_terms(df_terms, user_set, login_col='login', term_col='term'):
    df = df_terms.copy()

    # Step 1: Calculate frequency of each term per person
    term_counts_per_person = df.groupby([login_col, term_col]).size().reset_index(name='term_count')

    # Step 4: Create all combinations of terms and names
    all_names = df[login_col].unique()
    all_terms = df[term_col].unique()
    all_combinations = pd.MultiIndex.from_product([all_names, all_terms], names=[login_col, term_col]).to_frame(
        index=False)

    # Step 5: Merge with term frequencies, filling missing terms with frequency 0
    term_counts_per_person = all_combinations.merge(
        term_counts_per_person[[login_col, term_col, 'term_count']],
        on=[login_col, term_col], how='left').fillna(
        {'term_count': 0})

    # step 6: filter to get only the americans
    term_counts_per_person = term_counts_per_person[term_counts_per_person[login_col].isin(user_set)]

    # Step 7: Calculate the average frequency for each term across all persons
    total_term_counts = term_counts_per_person.groupby(term_col)['term_count'].sum().reset_index(
        name='total_term_counts')

    return total_term_counts


def compare_balanced_term_frequency(df_terms, login_col='login', term_col='term'):
    names_in_usa = set(df_terms[df_terms['claimed_country'] == 'USA'][login_col])
    names_in_china = set(df_terms[df_terms['claimed_country'] == 'China'][login_col])
    balanced_frequency_usa = calculate_balanced_term_frequency(df_terms, names_in_usa, login_col, term_col)
    total_term_counts_usa = calculate_term_counts_on_all_terms(df_terms, names_in_usa, login_col, term_col)

    balanced_frequency_china = calculate_balanced_term_frequency(df_terms, names_in_china, login_col, term_col)
    total_term_counts_china = calculate_term_counts_on_all_terms(df_terms, names_in_china, login_col, term_col)

    # Rename the 'balanced_frequency' columns
    balanced_frequency_usa = balanced_frequency_usa.rename(columns={'balanced_frequency': 'balanced_frequency_usa'})
    total_term_counts_usa = total_term_counts_usa.rename(columns={'total_term_counts': 'total_term_counts_usa'})

    balanced_frequency_china = balanced_frequency_china.rename(
        columns={'balanced_frequency': 'balanced_frequency_china'})
    total_term_counts_china = total_term_counts_china.rename(columns={'total_term_counts': 'total_term_counts_china'})

    # List of DataFrames
    dataframes = [balanced_frequency_usa, balanced_frequency_china, total_term_counts_usa, total_term_counts_china]

    # Merge all DataFrames on 'term' using reduce
    balanced_frequency_compare = reduce(lambda left, right: pd.merge(left, right, on='term', how='outer'), dataframes)

    return balanced_frequency_compare

