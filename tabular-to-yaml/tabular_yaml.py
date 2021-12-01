import pandas as pd, numpy as np, yaml, pprint, argparse

# filename = 'mpes-nexus_metadata_parameters.xlsx'
def csv_to_yaml(filename):
    yaml_filename = filename.replace(filename.split(".", 1)[1], 'yaml')
    temp_df = pd.read_csv(filename)
    temp_df.dropna(inplace=True)
    df = temp_df.drop_duplicates(subset=['Name'],inplace=False)
    diff = len(temp_df)-len(df)

    if(diff != 0):
        print("WARNING: One or more column(s) had the same name and only the first was kept.")
        print("     Number of rows dropped:" + str(diff))

    df.set_index('Name', inplace=True)
    sheet_dict = df.to_dict('index')
    with open(yaml_filename, "w") as f:
        yaml.dump(sheet_dict, f)


def xlsx_to_yaml(filename):
    yaml_filename = filename.replace(filename.split(".", 1)[1], 'yaml')
    xls = pd.ExcelFile(filename)
    names = xls.sheet_names
    # names = ["General"]
    master = {}

    for sheet in names:
        temp_df = pd.read_excel(filename, engine='openpyxl',sheet_name=sheet)
        df = temp_df.drop_duplicates(subset=['Name'],inplace=False)
        diff = len(temp_df)-len(df)

        if(diff != 0):
            print("WARNING: One or more column(s) had the same name and only the first was kept.")
            print("     Sheet:" + sheet)
            print("     Number of rows dropped:" + str(diff))

        df.set_index('Name', inplace=True)
        df.dropna(axis=0,thresh=3,inplace=True)
        df.dropna(axis=1,thresh=3,inplace=True)
        df.replace(["\n","\"],["","])
        sheet_dict = df.to_dict('index')
        master[sheet] = sheet_dict

    # pprint.pprint(master)

    with open(yaml_filename, "w") as f:
        yaml.dump(master, f)
    
    print("The new file has been saved as " + yaml_filename)

def to_xlsx(filename):
    print("to be done")
    
    with open(filename, 'r') as stream:
        try:
            parsed_yaml=yaml.safe_load(stream)
            # pprint.pprint(parsed_yaml)
            for key in parsed_yaml:
                one_sheet = parsed_yaml[key]
                pprint.pprint(one_sheet)
                df = pd.DataFrame(data=one_sheet, index=[0])
                print("asdfasdf")
                print(df)
        except yaml.YAMLError as exc:
            print(exc)


def main(args):
    """ Main entry point of the app """
    print("Parameter file yaml-xlsx parser.")
    if args.filename.split(".", 1)[1] == "xlsx":
        xlsx_to_yaml(args.filename)
    elif args.filename.split(".", 1)[1] == "csv":
        csv_to_yaml(args.filename)
    elif args.filename.split(".", 1)[1] == "yaml":
        to_xlsx(args.filename)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-n", "--filename", action="store", dest="filename", help="filename")

    args = parser.parse_args()
    main(args)