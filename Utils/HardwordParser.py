import inflection
import re


class HardwordParser:
    @staticmethod
    def parse_hard_word(name, ignore_numbers=False):
        # This regex finds "words" (upper/lower combos), numbers, or separators
        tokens = re.findall(r'[A-Za-z]+|\d+', name)

        result = []
        for token in tokens:
            # If it's all digits, just keep it
            if token.isdigit():
                if not ignore_numbers:
                    result.append(token)
            else:
                # Apply split rule:
                # Split before capital letter if:
                #   - preceded by lowercase
                #   - followed by lowercase
                subparts = re.split(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', token)
                result.extend(subparts)

        return result

    @staticmethod
    def classify_naming_convention(name):
        # SCREAMING_SNAKE_CASE
        if re.fullmatch(r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$', name):
            return 'SCREAMING_SNAKE_CASE'

        # PascalCase: must have at least one lowercase not at the start
        if re.fullmatch(r'(?=.*[a-z])([A-Z][a-z0-9]*)+$', name):
            return 'PascalCase'

        # camelCase: starts lowercase, followed by capitalized words
        if re.fullmatch(r'^[a-z][a-z0-9]*([A-Z][a-z0-9]*)+$', name):
            return 'camelCase'

        # snake_case: at least one underscore, each word lowercase or numeric
        if re.fullmatch(r'^[a-z][a-z0-9]*(_[a-z0-9]+)+$', name):
            return 'snake_case'

        # lowercase (or single lowercase letter), possibly with numbers
        if re.fullmatch(r'^[a-z][a-z0-9]*$', name):
            return 'lowercase'

        # If none matched
        return 'unknown'
