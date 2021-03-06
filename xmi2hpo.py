"""
This function takes as input xmi files generated by cTAKES and maps the HPO terms using the UMLS ID
from the xmi files and compare them to the UMLS ID from the HPO .obo file. UMLS ID = Cxxxxxxx. The UMLS ID
from cTAKES are abbreviated with 'cui'.
"""

from xml.dom import minidom
import obo_parser
import itertools
import re
import os
import argparse

# Create recent HPO library of HPO terms only related to phenotypic abnormalities (HP:0000118)
hpo_url = "http://purl.obolibrary.org/obo/hp.obo"
output = "HPO.tsv"
phenotypic_abnormalities = "HP:0000118"
children_category = True
obo_parser.convert_obo_to_tsv(hpo_url, output, phenotypic_abnormalities, children_category)

# Extract HPO ID, term and UMLS reference from the meta-tsv file
with open(output) as HPO:
    library = []
    for line in HPO:
        tsplit = line.split("\t")
        library.append([tsplit[0], tsplit[1], tsplit[13].strip("\n")])
HPO.close()

# Extract list of UMLS id from library(some terms have multiple UMLS ids)
library_UMLS = []
for line in library[1:]:
    library_UMLS.append(line[2])

# Read each xmi file in the input folder and extract their UMLS IDs
def xmi2hpo(input_path, output_path):
    """
    Main function:
    Args:
        input_path (str): Local path to the folder containing the xmi files to parse.
        output_path (str): Local path to the folder where the results are stored.
    """
    xmi_files = os.listdir(input_path)
    for file in xmi_files:
        if file.endswith(".xmi"):
            xmldoc = minidom.parse(input_path + "/" + file)
            UMLS_ID = []
            for element in xmldoc.getElementsByTagName("refsem:UmlsConcept"):
                if element.getAttribute('disambiguated') == "false":
                    UMLS_ID.append(["UMLS:%s" % element.getAttribute('cui')])

        # Mapp UMLS from the xmi file to UMLS from the library
        mapped_UMLS = []
        for line in UMLS_ID:
            for string in line:
                for lib in library_UMLS:
                    if string in lib:
                        mapped_UMLS.append(string)

        # find the HPO term for each mapped UMLS
        mapped_HPO = []
        for code in mapped_UMLS:
            for line in library:
                if code in line[2]:
                    mapped_HPO.append([line[0], line[1]])

        # remove duplicated mapped HPO terms
        mapped_HPO.sort()
        patient_HPO_final = list(mapped_HPO for mapped_HPO, _ in itertools.groupby(mapped_HPO))

        # Output in txt file
        # create output folder if not already exists
        sourcedir = os.getcwd()
        if os.path.isdir(sourcedir + "/" + output_path) is False:
            os.mkdir(sourcedir + "/" + output_path)

        # setup regex compiler to put a white space between HPO_id and HPO_term
        rx = re.compile(r'(?<=\d)(?=[^\d\s])')

        with open(output_path + "/" + file.strip(".txt.xmi") + ".HPO.txt", "w") as output:
            for item in patient_HPO_final:
                item = str().join(item)
                it = rx.sub('\t', item)
                output.write("%s\n" % it)
        output.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Map HPO terms to xmi files from cTAKES.")
    p.add_argument("-i", "--input_path", help="Local file path to the patient xmi files.")
    p.add_argument("-o", "--output_path", help="Local path to folder to store the results.")
    args = p.parse_args()

    xmi2hpo(
        args.input_path,
        args.output_path,
    )
