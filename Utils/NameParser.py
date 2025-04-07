import inflection
import re


class NameParser:
    def split_name_to_terms(self, name, ignore_numbers=True):
        snake_case_name = inflection.underscore(name)
        list_terms = snake_case_name.split('_')
        if ignore_numbers:
            # something the inflection library didn't do well: it attached the numbers
            result = []
            for term in list_terms:
                # Extract all sequences of alphabetic characters
                words = re.findall(r'[a-zA-Z]+', term)
                result.extend(words)  # Add the extracted words to the result list
            return result
        else:
            return list_terms

    def standardize_name(self, name, ignore_numbers=True):
        list_terms = self.split_name_to_terms(name, ignore_numbers)
        return '_'.join(list_terms)

    def count_length_by_letter(self, name, ignore_numbers=True):
        if ignore_numbers:
            # we don't count numbers and underscore
            pattern = r'[0-9_]'
        else:
            # we only get rid of underscore
            pattern = r'[_]'
        name = re.sub(pattern, '', name)
        return len(name)

    def count_length_by_word(self, name, ignore_numbers=True):
        list_terms = self.split_name_to_terms(name, ignore_numbers)
        return len(list_terms)
