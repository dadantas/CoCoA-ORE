#Script to test the performance of the CoCoA tool
import csv
import os
import subprocess
import sys
from multiprocessing import Pool
from tqdm import tqdm

def test_file(file_info):
    file_to_test, flags, files_dir = file_info

    result = file_to_test
    if os.path.isfile(files_dir + file_to_test):
        # Get the output of the main.py with flags -o -d
        p = subprocess.run(["python3", "main.py"] + flags + [files_dir + file_to_test], capture_output=True)
        safe = True
        with open(files_dir + file_to_test, 'r') as file:
            safe = "Safe sample" in file.read(40)
        
        if p.returncode != 0:
            result = "Error"
            
        else:
            result = p.stdout.decode('utf-8').rstrip('\n')

        return file_to_test, result, safe
    return file_to_test, result, None

if __name__ == "__main__":
    info_xss = ("../SARD2_XSS/", ["-o", "-d", "-p"], "output_XSS.csv","CoCoA Testes Unitários - XSS.csv")
    info_sqli = ("../SARD_SQLI_Merged/", ["-s","-o", "-d", "-p"], "output_SQLi.csv", "CoCoA Testes Unitários - SQLI.csv")
    info = info_sqli if len(sys.argv) >= 2 and sys.argv[1] == "--xss" else info_xss

    files_dir, flags, output, csv_file = info_xss if len(sys.argv) >= 2 and sys.argv[1] == "--xss" else info_sqli

    rows = []

    print("Testing files in: ", files_dir)

    with open(files_dir + csv_file, 'r') as file:
        csv_reader = csv.reader(file)
        rows = [row for row in csv_reader]

    files_to_test = [(row[1], flags, files_dir) for row in rows]
    with Pool() as pool:
        results = list(tqdm(pool.imap(test_file, files_to_test), total=len(files_to_test), desc="Testing files"))

    count = 0
    error_count = 0
    true_positives, false_positives, true_negatives, false_negatives = 0, 0, 0, 0
    for i, (file_to_test, result, safe) in enumerate(results):
        if safe is None:
            continue
        
        rows[i][10] = result
       
        count += 1
        if result == "Error":
            error_count += 1
            continue
        if "Vulnerabilitys" in result:
            if safe:
                false_positives += 1
            else:
                true_positives += 1
        else:
            if safe:
                true_negatives += 1
            else:
                false_negatives += 1
                print(file_to_test)

    with open(output, 'w') as file:
        csv_writer = csv.writer(file)
        csv_writer.writerows(rows)
    print()
    print("Total files found: " + str(count))
    print("Error count: " + str(error_count))
    print()
    print("Total wrong classifications: " + str(false_positives + false_negatives))
    print("True positives: " + str(true_positives))
    print("False positives: " + str(false_positives))
    print("True negatives: " + str(true_negatives))
    print("False negatives: " + str(false_negatives))
    print()
    print("Accuracy (ignoring errors): " + str((true_positives + true_negatives) / (count-error_count)))
    print("Accuracy (with errors): " + str((true_positives + true_negatives) / count))
    print("Precision: " + str(true_positives / (true_positives + false_positives) if true_positives + false_positives > 0 else 0))
    print("Recall: " + str(true_positives / (true_positives + false_negatives) if true_positives + false_negatives > 0 else 0))
    print("F1-score: " + str(2 * true_positives / (2 * true_positives + false_positives + false_negatives) if true_positives + false_positives + false_negatives > 0 else 0))