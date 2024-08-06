import logging
import os


def get_abs_path(directory, file):
    directory_path = os.path.join(os.getcwd(), '', directory)
    file_path = os.path.join(directory_path, file)
    return file_path
# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    handlers=[
                        logging.FileHandler(get_abs_path('data', 'app.log')),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger(__name__)
