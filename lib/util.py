import os


def create_folder(f):
    try:

        # script_file_path = __file__
        # current_working_dir = os.getcwd()

        # Check if the directory exists, if not, create it
        if not os.path.exists(f):
            os.makedirs(f)

        return True
    except OSError as error:
        print(f"Error: Creating directory {f}. {error}")
        return False