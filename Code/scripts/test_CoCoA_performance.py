#Script to test the performance of the CoCoA tool
#And all the prints are not commented out
#folders to test must be on the master_dir variable (.../WebApps/ by default)
import csv
import os
import subprocess
import sys
from multiprocessing import Pool
import re

run_count = 5 #number of times to run each file
master_dir = "../WebApps/"
info = [("performance.csv", []), ("performance_e.csv", ["-e"]), ("performance_o.csv", ["-o"])]


def test_file(file_info,flags, timeout=5):
    # Unpack file_info
    file_to_test, files_dir = file_info

    result = file_to_test
    if os.path.isfile(files_dir + file_to_test):
        # Get the output of the main.py with flags -o -d
        try:
            p = subprocess.run(["python3", "main.py"] + flags + [file_to_test], capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            result = "Timeout"
            return file_to_test, result, None
        if p.returncode != 0:
            result = "Error"
        else:
            result = p.stdout.decode('utf-8').rstrip('\n')

        return file_to_test, result
    return file_to_test, result, None

def extract_performace_values(output):
    # print("---Lexer %s seconds ---" % (time.time() - start_time))
    search = re.compile(r"---Lexer (.+) seconds ---")
    lexer_time = float(search.search(output).group(1)) if search.search(output) else None
    #print("---Translator %s seconds ---" % (time.time() - start_time))
    search = re.compile(r"---Translator (.+) seconds ---")
    translator_time = float(search.search(output).group(1)) if search.search(output) else None
    #print("---Encryptor %s seconds ---" % (time.time() - start_time))
    search = re.compile(r"---Encryptor (.+) seconds ---")
    encryptor_time = float(search.search(output).group(1)) if search.search(output) else None
    #print("---VD %s seconds ---" % (time.time() - start_time))
    search = re.compile(r"---VD (.+) seconds ---")
    vd_time = float(search.search(output).group(1)) if search.search(output) else None
    
    #disk usage by the encrypted index read the dump file size filesize.txt
    filesize = os.path.getsize("filesize.txt")
    
    return lexer_time, translator_time, encryptor_time, vd_time, filesize
if __name__ == "__main__":

    php_files = []
    for path, subdires, files in os.walk(master_dir):
        for file in files:
            if file.endswith(".php"):
                php_files.append(os.path.join(path, file))
    php_files = [(file, master_dir) for file in php_files]
    
    for output, flags in info:    
        rows = []
        rows = [["WebApp", "Lexer Time", "Translator Time", "Encryptor Time", "VD Time", "Encrypted Index Size"]]
        print("Testing files in: ", master_dir)
        count = 0

        results = []
        for file in php_files:
            count += 1
            print("Testing file: " + str(file[0]))
            avgs = []
            for i in range(run_count):
                result = test_file(file, flags)
                if result[1] == "Error" or result[1] == "Timeout":
                    print("Error in file: " + file[0])
                    #delete that file from the directory
                    os.remove(file[0])
                    sys.exit(1)
                result = extract_performace_values(result[1])

                avgs.append(result)
            avgs = [sum(x)/run_count for x in zip(*avgs)]
            result = [file[0]] + avgs
            #remove cientific notation and use comma as decimal separator
            print(result)
            rows.append(result)


        #group results by WebApp
        grouped = {}
        for result in rows[1:]:
            app = result[0].split("/")[2]
            if app in grouped:
                #sum the values
                for i in range(1, len(result)):
                    grouped[app][i] = grouped[app][i] + result[i]
            else:
                grouped[app] = result
        # #create a new csv with the output
        #dont use cientific notation
        for key in grouped:
            grouped[key] = [f"{x:.20f}".replace(".",",") if x is not None else "" for x in grouped[key][1:]]
        rows = rows[0:1]
        for key in sorted(grouped.keys(), key=lambda x: x.lower()):
            rows.append([key] + grouped[key])
        with open(output, 'w', newline='') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerows(rows)
        print("Total files found: " + str(count))
   
