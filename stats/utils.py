import logging
from requests import get
from datetime import datetime

def today():
    return datetime.today().strftime('%Y-%m-%d')

def basedir():
    return "../../project-zap/stats/"

def download_to_file(url, filename, headers={}):
    errors = open("errors.txt", 'a')

    with open(filename, "wb") as file:
        try:
            print("Downloading " + url)
            response = get(url, headers=headers)
            if response.status_code == 200:
                file.write(response.content)
            else:
                print("Failed to download " + url)
                errors.write("Failed accessing " + url + " status code: " + str(response.status_code))
                errors.write("\n\n")
        except Exception as x:
            print("Failed to download " + url)
            errors.write("Failed accessing " + url + "\n")
            errors.write(logging.traceback.format_exc())
            errors.write("\n\n")

    errors.close()