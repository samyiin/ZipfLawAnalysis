import pandas as pd


class DatabaseManager:
    @staticmethod
    def load_df_terms():
        df_terms = pd.read_csv("Database/FinalNameData/df_terms.csv")
        df_terms.replace("NANPLACEHOLDER", 'nan', inplace=True)
        df_terms.replace("NULLPLACEHOLDER", 'null', inplace=True)
        df_terms.fillna('', inplace=True)
        df_terms["name_string"] = df_terms["name_string"].astype(str)
        df_terms["standardized_name"] = df_terms["standardized_name"].astype(str)
        df_terms["explanation"] = df_terms["explanation"].astype(str)
        df_terms["suggestion"] = df_terms["suggestion"].astype(str)
        df_terms["term_category"] = df_terms["term_category"].astype(int)
        return df_terms

    @staticmethod
    def load_df_names():
        df_names = pd.read_csv("Database/FinalNameData/df_names.csv")
        df_names.replace("NULLPLACEHOLDER", 'null', inplace=True)
        df_names.fillna('', inplace=True)
        return df_names


