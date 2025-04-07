"""
Regarding all possible exceptions that might go wrong: I don't handle any of them.
The only "handle" I did is, if anything else went smooth, the only problem is parsing the file using ast, then I will
try again by converting the file to from python 2 to python 3, and parse again.
"""

import ast
import pandas as pd
import subprocess
import os
import re
import shutil


def copy_file_to_dir(original_file_path, filename, dest_dir_path):
    """
    By our build, we will assume that filename.py exists in original_dir_path
    and also dest_dir_path exists
    And also if file with same name exists in dest_dir_path, then we will rename this file with number (i)

    :param original_file_path:
    :param filename:
    :param dest_dir_path:
    :return:
    """

    if not os.path.isfile(original_file_path):
        raise Exception("File not exist: original_file_path")

    os.makedirs(dest_dir_path, exist_ok=True)

    dest_file_path = os.path.join(dest_dir_path, filename)

    # Check for naming conflicts and append (x) if needed
    counter = 1
    while os.path.exists(dest_file_path):
        # split the filename and extension (.py)
        file_name_no_ext, file_ext = os.path.splitext(filename)
        dest_file_path = os.path.join(dest_dir_path, f"{file_name_no_ext}({counter}){file_ext}")
        counter += 1

    # Copy the file to the destination
    try:
        shutil.copy(original_file_path, dest_file_path)
    except:
        # I met a problem with symbolic link: it only shows when I do ls in terminal, it looks like "cv.py@"
        # we can't do anything about it, it is linking to something else.
        pass


class PythonFileCleaner:
    """
    This class helps reformat a python file, so that we can parse it later.
    Some problem we met are:
    file encoding not utf-8
    problematic indentations
    mixed tabs/spaces
    non-ASCII characters
    python 2 files
    Notice, except for python2 to python3 conversion, all the rest of fixing is inplace!! So use carefully. Arguably
    they should not be inplace?
    """

    def safe_open_file(self, file_path, operation):
        """
        Force open the file with utf-8 encoding.
        :param file_path:
        :param operation:
        :return:
        """
        with open(file_path, "r", encoding='utf-8', errors='ignore') as f:
            if operation == "read":
                return f.read()
            elif operation == "readlines":
                return f.readlines()
            else:
                raise ValueError("operation must be read or readlines")

    def fix_indentation(self, file_path, indent_size=4):
        """
        Fix inconsistent indentation in a Python file by replacing tabs with spaces.

        Args:
            file_path (str): Path to the Python file.
            indent_size (int): Number of spaces to replace each tab with. Default is 4.
            :param indent_size:
            :param file_path:
            :param encoding:
        """
        try:
            lines = self.safe_open_file(file_path, 'readlines')

            # Replace tabs with spaces
            fixed_lines = [line.replace("\t", " " * indent_size) for line in lines]

            # Write the fixed lines back to the file
            with open(file_path, "w", encoding='utf-8') as f:
                f.writelines(fixed_lines)

        except Exception as e:
            raise Exception(f"Error fixing indentation in {file_path}: {e}")

    def fix_nonASCII(self, file_path):
        """Fix common issues like mixed tabs/spaces and non-ASCII characters."""
        try:
            lines = self.safe_open_file(file_path, 'readlines')

            fixed_lines = []
            for line in lines:
                # Remove non-ASCII characters
                line = re.sub(r'[^\x00-\x7F]+', '', line)
                fixed_lines.append(line)

            # Write the cleaned lines back to the file
            with open(file_path, "w", encoding='utf-8') as f:
                f.writelines(fixed_lines)

        except Exception as e:
            raise Exception(f"Error fix_nonASCII file {file_path}: {e}")

    def convert_python2_to_python3(self, file_path):
        """Convert Python 2 code to Python 3 using the 2to3 tool."""
        try:
            # This way of naming temp is messy but probably effective?
            directory = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            temp_file_dir = os.path.join(directory, "_2to3_remake_files")

            # Run 2to3 on the file and write the converted code to a temporary file
            result = subprocess.run(
                ["2to3", "-w", "-n", "-o", temp_file_dir, file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            if result.returncode == 0:
                # Copy file if it does not exist in the temp directory
                output_file_path = os.path.join(temp_file_dir, file_name)
                # print(f"2to3 conversion success for {file_path}")
                return output_file_path
            else:
                raise Exception("2to3 tool exists but 2to3 conversion failed.")
        except FileNotFoundError:
            raise FileNotFoundError("2to3 tool is not installed or not found in PATH.")

    def clear_2to3_created_files(self, directory_path):
        temp_file_dir = os.path.join(directory_path, "_2to3_remake_files")
        if os.path.exists(temp_file_dir):
            shutil.rmtree(temp_file_dir)

    def cleanup_python_file(self, python_file_path, dest_file_directory):
        # fix irregular indentations
        self.fix_indentation(python_file_path)
        # fix non ascii characters
        self.fix_nonASCII(python_file_path)

        try:
            # first try parse with python 3
            content = self.safe_open_file(python_file_path, "read")
            # try to parse the content
            tree = ast.parse(content)
        except:
            # convert the file to python 3, override python_file_path variable
            try:
                python_file_path = self.convert_python2_to_python3(python_file_path)
                # first try parse again
                content = self.safe_open_file(python_file_path, "read")
                tree = ast.parse(content)
            except:
                # if it failed at parsing or 2to3 conversion then that's it, we cannot parse this file
                raise Exception("Cannot clean up this file!")

        # if successfully parse then we save it to dest_file_directory
        file_name = os.path.basename(python_file_path)
        copy_file_to_dir(original_file_path=python_file_path,
                         filename=file_name,
                         dest_dir_path=dest_file_directory)


class ScopeTracker(ast.NodeVisitor):
    def __init__(self):
        # Scope flags
        self.in_function = False
        self.in_class = False
        self.in_lambda = False
        self.in_comprehension = False
        self.in_match = False
        self.in_for = False
        self.in_while = False
        self.in_if = False
        self.in_with = False
        self.in_try = False
        self.in_except = False
        self.in_finally = False

        # Nesting
        self.nested_scope_number = 0
        self.nested_indentation_number = 0

        # Collected identifiers
        self.identifiers = []

    def _record_identifier(self, name, classification, node):
        info = {
            "name": name,
            "classification": classification,
            "in_function": self.in_function,
            "in_class": self.in_class,
            "in_lambda": self.in_lambda,
            "in_comprehension": self.in_comprehension,
            "in_match": self.in_match,
            "in_for": self.in_for,
            "in_while": self.in_while,
            "in_if": self.in_if,
            "in_with": self.in_with,
            "in_try": self.in_try,
            "in_except": self.in_except,
            "in_finally": self.in_finally,
            "nested_scope_number": self.nested_scope_number,
            "nested_indentation_number": self.nested_indentation_number,
            "lineno": getattr(node, "lineno", None),
            "col_offset": getattr(node, "col_offset", None),
        }
        self.identifiers.append(info)

    # === CLASS ===
    def visit_ClassDef(self, node):
        self._record_identifier(node.name, "class name", node)

        prev = self.in_class
        self.in_class = True
        self.nested_scope_number += 1
        self.nested_indentation_number += 1

        self.generic_visit(node)

        self.nested_scope_number -= 1
        self.nested_indentation_number -= 1
        self.in_class = prev

    # === FUNCTIONS & PARAMETERS ===
    def visit_FunctionDef(self, node):
        if self.in_class:
            self._record_identifier(node.name, "method name", node)
        else:
            self._record_identifier(node.name, "function name", node)

        param_type = "method parameter" if self.in_class else "function parameter"

        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            self._record_identifier(arg.arg, param_type, arg)
        if node.args.vararg:
            self._record_identifier(node.args.vararg.arg, param_type, node.args.vararg)
        if node.args.kwarg:
            self._record_identifier(node.args.kwarg.arg, param_type, node.args.kwarg)

        prev = self.in_function
        self.in_function = True
        self.nested_scope_number += 1
        self.nested_indentation_number += 1

        self.generic_visit(node)

        self.nested_scope_number -= 1
        self.nested_indentation_number -= 1
        self.in_function = prev

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Lambda(self, node):
        for arg in node.args.args:
            self._record_identifier(arg.arg, "lambda parameter", arg)

        prev = self.in_lambda
        self.in_lambda = True
        self.nested_scope_number += 1

        self.generic_visit(node)

        self.nested_scope_number -= 1
        self.in_lambda = prev

    # === ASSIGNMENTS ===
    def visit_Assign(self, node):
        for target in node.targets:
            self._handle_assignment_target(target)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        self._handle_assignment_target(node.target)
        self.generic_visit(node)

    def _handle_assignment_target(self, target):
        if isinstance(target, ast.Name):
            self._record_identifier(target.id, "variable", target)
        elif isinstance(target, ast.Attribute):
            if isinstance(target.value, ast.Name) and target.value.id == "self":
                self._record_identifier(target.attr, "instance variable", target)

    # === FOR ===
    def visit_For(self, node):
        self._extract_targets(node.target, "for_loop variable")

        prev = self.in_for
        self.in_for = True
        self.nested_indentation_number += 1

        self.generic_visit(node)

        self.nested_indentation_number -= 1
        self.in_for = prev

    def visit_AsyncFor(self, node):
        self.visit_For(node)

    # === WITH ===
    def visit_With(self, node):
        for item in node.items:
            if item.optional_vars:
                self._extract_targets(item.optional_vars, "with_statement variable")

        prev = self.in_with
        self.in_with = True
        self.nested_indentation_number += 1

        self.generic_visit(node)

        self.nested_indentation_number -= 1
        self.in_with = prev

    def visit_AsyncWith(self, node):
        self.visit_With(node)

    # === TRY/EXCEPT/FINALLY ===
    def visit_Try(self, node):
        prev_try = self.in_try
        self.in_try = True
        self.nested_indentation_number += 1
        self.visit_statements(node.body)
        self.nested_indentation_number -= 1
        self.in_try = prev_try

        for handler in node.handlers:
            self.visit(handler)

        if node.finalbody:
            prev_finally = self.in_finally
            self.in_finally = True
            self.nested_indentation_number += 1
            self.visit_statements(node.finalbody)
            self.nested_indentation_number -= 1
            self.in_finally = prev_finally

        if node.orelse:
            self.visit_statements(node.orelse)


    def visit_ExceptHandler(self, node):
        if node.name:
            self._record_identifier(node.name, "exception variable", node)

        prev = self.in_except
        self.in_except = True
        self.nested_scope_number += 1
        self.nested_indentation_number += 1

        self.generic_visit(node)

        self.nested_scope_number -= 1
        self.nested_indentation_number -= 1
        self.in_except = prev

    # =======IF=============
    def visit_If(self, node):
        prev = self.in_if
        self.in_if = True
        self.nested_indentation_number += 1

        self.generic_visit(node)

        self.nested_indentation_number -= 1
        self.in_if = prev

    # ==========WHILE=========

    def visit_While(self, node):
        prev = self.in_while
        self.in_while = True
        self.nested_indentation_number += 1

        self.generic_visit(node)

        self.nested_indentation_number -= 1
        self.in_while = prev

    # === COMPREHENSIONS ===
    def visit_comprehension(self, node):
        self._extract_targets(node.target, "comprehension variable")
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self._visit_comprehension(node)

    def visit_SetComp(self, node):
        self._visit_comprehension(node)

    def visit_DictComp(self, node):
        self._visit_comprehension(node)

    def visit_GeneratorExp(self, node):
        self._visit_comprehension(node)

    def _visit_comprehension(self, node):
        prev = self.in_comprehension
        self.in_comprehension = True
        self.nested_scope_number += 1

        self.generic_visit(node)

        self.nested_scope_number -= 1
        self.in_comprehension = prev

    # === MATCH ===
    def visit_MatchAs(self, node):
        if node.name:
            self._record_identifier(node.name, "pattern_matching variable", node)

    def visit_Match(self, node):
        prev = self.in_match
        self.in_match = True
        self.nested_scope_number += 1
        self.nested_indentation_number += 1
        self.generic_visit(node)
        self.nested_scope_number -= 1
        self.nested_indentation_number -= 1
        self.in_match = prev

    # === IMPORT ===
    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name.split('.')[0]
            self._record_identifier(name, "import alias", alias)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            self._record_identifier(name, "import alias", alias)

    # === Helpers ===
    def _extract_targets(self, target, classification):
        if isinstance(target, ast.Name):
            self._record_identifier(target.id, classification, target)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self._extract_targets(elt, classification)

    def visit_statements(self, stmts):
        for stmt in stmts:
            self.visit(stmt)

    def generic_visit(self, node):
        super().generic_visit(node)


class PythonIdentifierExtractor:
    CLEANED_PYTHON_FILE_DIR = "CleanedPythonFiles"

    def __init__(self):
        self.python_file_cleaner = PythonFileCleaner()

    def cleanup_python_file(self, python_file_path):
        """
        Create a directory under the same dir of python_file_path
        Store the cleaned file inside

        :param python_file_path:
        :return: the temp directory created, the cleaned file inside the temp directory
        """
        # This way of naming temp is messy but probably effective?
        directory = os.path.dirname(python_file_path)
        temp_file_dir = os.path.join(directory, self.CLEANED_PYTHON_FILE_DIR)
        try:
            self.python_file_cleaner.cleanup_python_file(python_file_path, dest_file_directory=temp_file_dir)
        except:
            raise Exception("Cannot cleanup this file")

    def clear_temp_dir(self, python_file_path):
        directory_path = os.path.dirname(python_file_path)
        # clear the 2to3 directory
        self.python_file_cleaner.clear_2to3_created_files(directory_path)
        # clear the directory of cleaned python files
        temp_file_dir = os.path.join(directory_path, self.CLEANED_PYTHON_FILE_DIR)
        if os.path.exists(temp_file_dir):
            shutil.rmtree(temp_file_dir)

    def extract_identifiers_with_cleaning(self, python_file_path):
        # first clean the python file, generate a clean copy under self.CLEANED_PYTHON_FILE_DIR
        self.cleanup_python_file(python_file_path)

        # if the cleaning process is success, we take this temp clean python file
        # override python_file_path
        file_name = os.path.basename(python_file_path)
        directory = os.path.dirname(python_file_path)
        temp_file_dir = os.path.join(directory, self.CLEANED_PYTHON_FILE_DIR)
        cleaned_python_filepath = os.path.join(temp_file_dir, file_name)

        # Extract the identifiers
        df = self.extract_identifiers_without_cleaning(python_file_path)

        # clean up all the temp file, dir we created along the way
        self.clear_temp_dir(python_file_path)

        return df

    def extract_identifiers_without_cleaning(self, python_file_path):
        with open(python_file_path, "r", encoding='utf-8', errors='ignore') as f:
            content = f.read()
        tree = ast.parse(content)
        tracker = ScopeTracker()
        tracker.visit(tree)
        return pd.DataFrame(tracker.identifiers)

