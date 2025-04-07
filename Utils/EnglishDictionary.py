import nltk
# nltk.download('words', download_dir='Database/nltk_data')
# nltk.download('brown', download_dir='Database/nltk_data')
from nltk.corpus import words
# This word_frequency actually includes GoogleBooksNgram
# https://github.com/rspeer/wordfreq.git
# Limited for n-grams
from wordfreq import word_frequency
import numpy as np
# This will give all conjugations of a verb
# https://pypi.org/project/word-forms/
from word_forms.word_forms import get_word_forms

import pandas as pd
class EnglishDictionary:
    def __init__(self):
        # This will only be called in the root directory of the project.
        # By default we use the NLTK dictionary
        self.dictionary = set(words.words())
        irregular_verbs_csv = 'Database/EnglishDictionarySource/irregular_verbs.csv'
        self.df_irregular_verbs = pd.read_csv(irregular_verbs_csv)

    def load_NLTK_dictionary(self):
        # Load the NLTK word list
        self.dictionary = set(words.words())

    def _load_word_list(self, file_path):
        """Load a large word list from a file into a set."""
        with open(file_path, 'r') as f:
            return set(line.strip().lower() for line in f)

    def load_ENABLE(self):
        # Credit: https://github.com/dolph/dictionary.git
        word_list_path = 'Database/EnglishDictionarySource/enable1.txt'
        self.dictionary = self._load_word_list(word_list_path)

    def load_LargeWordList_1(self):
        # Credit: https://github.com/dwyl/english-words.git
        word_list_path = 'Database/EnglishDictionarySource/words_alpha.txt'
        self.dictionary = self._load_word_list(word_list_path)

    def load_SCOWL(self):
        # Credit: https://github.com/en-wl/wordlist.git
        '''
        clone and go to terminal
        make
        ./scowl word-list scowl.db > wl.txt
        :return:
        '''
        word_list_path = 'Database/EnglishDictionarySource/wl.txt'
        self.dictionary = self._load_word_list(word_list_path)

    def is_english(self, word):
        return (word in self.dictionary) or (word.lower() in self.dictionary)

    def get_word_natural_frequency(self, word):
        freq = word_frequency(word, 'en')
        return freq

    def word_forms(self, word):
        # Unused....
        return get_word_forms(word)

    def is_irregular_past_tense(self, verb):
        for index, row in self.df_irregular_verbs.iterrows():
            if verb == row['Past Simple'] or verb == row['-ed']:
                if verb != row['Base Form']:
                    return True
        return False




