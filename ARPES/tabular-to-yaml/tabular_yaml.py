import pandas as pd, numpy as np, yaml, pprint, argparse, re, os
from pandas import ExcelWriter

# filename = 'mpes-nexus_metadata_parameters.xlsx'
def csv_to_yaml(args):
    yaml_filename = args.filename.replace(args.filename.split(".", 1)[1], 'yaml')
    temp_df = pd.read_csv(args.filename)
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

def stripspaces(string):
    return re.sub(r"\s+", "", str(string), flags=re.UNICODE)

def cleanDF(df):
    df = df.fillna('') 
    df['Nexus hierarchy'] = df['Nexus hierarchy'].str.split(':').str[-1]
    MergedTypeClass = df['type:units'].str.split(':').str[0].apply(stripspaces) + df['NX class'].astype(str).apply(stripspaces)
    # print(df['Nexus hierarchy'])
    # df['Name'] = df['Name'].apply(stripspaces)
    # df['Nexus hierarchy'] = df['Nexus hierarchy'].apply(stripspaces)
    df['Name'] = df['Nexus hierarchy'].apply(stripspaces) + " (" + MergedTypeClass + ")"
    df['unit'] = df['type:units'].str.split(':').str[-1].apply(stripspaces)
    # df["Documentation"] = df["Documentation"].astype(str) + ""
    df.drop(columns=["Nexus hierarchy","type:units","NX class"], inplace = True)
    # df['NX variable'] = df['NX variable'].apply(stripspaces)
    df.set_index('Name', inplace=True)
    df.dropna(axis=0,thresh=3,inplace=True)
    df.dropna(axis=1,thresh=3,inplace=True)
    return df

def xlsx_to_yaml(args):
    # yaml_filename = filename.split(".", 1)[0]+"_converted.yaml"
    # print(yaml_filename)
    # yaml_filename = filename.replace(filename, 'yaml')
    xls = pd.ExcelFile(args.filename)
    names = xls.sheet_names
    # names = ["NXentry"] 
    if not os.path.exists(args.destination):
        os.makedirs(args.destination)
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    folder_path = os.path.join(dir_path,args.destination)

    for sheet in names:
        print("Processing sheet: " + sheet)
        yaml_filename = sheet + "_converted.yaml"
        temp_df = pd.read_excel(args.filename, engine='openpyxl',sheet_name=sheet,encoding='utf8')
        df = temp_df.drop_duplicates(subset=['Nexus hierarchy'],inplace=False)
        diff = len(temp_df)-len(df)

        if(diff != 0):
            print("WARNING: One or more column(s) had the same name and only the first was kept.")
            print("     Sheet:" + sheet)
            print("     Number of rows dropped:" + str(diff))

        df = cleanDF(df)
        print(df)
        sheet_dict = df.to_dict('index')
        sheet_dict = {
            outer_k: {
                inner_k: inner_v
                for inner_k, inner_v in outer_v.items()
                if inner_v != 0 and inner_k != "Exists"
            } 
            for outer_k, outer_v in sheet_dict.items()
        }
        # {x:y for x,y in sheet_dict.items() if y!=0}
        # print(sheet_dict.get('experiment_start_date (NX_DATE_TIME)', {}).get('Documentation'))
        # pprint.pprint(sheet_dict)
        file_path = os.path.join(folder_path,yaml_filename)
        # print(file_path)
        # pprint.pprint(sheet_dict)
        output={}
        tempstring = "(" + sheet + ")"
        output[tempstring] = sheet_dict
        with open(file_path, "w") as f:
            yaml.dump(output, f)
        # master[sheet] = sheet_dict

    # pprint.pprint(master)

    # with open(yaml_filename, "w") as f:
    #     yaml.dump(master, f)
    
    print("The new file has been saved as " + yaml_filename)

def to_xlsx(args):
    # print("to be done")
    xlsx_filename = args.filename.split(".", 1)[0]+"_converted.xlsx"
    with open(args.filename, 'r') as stream:
        try:
            parsed_yaml=yaml.safe_load(stream)
            writer = ExcelWriter(xlsx_filename)
            # pprint.pprint(parsed_yaml)
            for key in parsed_yaml:
                print(key)
                one_sheet = parsed_yaml[key]
                holder = []
                names = []
                for row in one_sheet:
                    values = one_sheet[row]
                    df = pd.DataFrame(data=values,index = [0])
                    # print("asdfasdf")
                    # print(df)
                    holder.append(df)
                    names.append(str(row))
                output = pd.concat(holder)
                output.insert(loc=0, column='Name', value=names)
                output.to_excel(writer,key,index=False)

            writer.save()
        except yaml.YAMLError as exc:
            print(exc)


def main(args):
    print("Parameter file yaml-tabular parser.")

    if args.filename.split(".", 1)[1] == "xlsx":
        xlsx_to_yaml(args)
    elif args.filename.split(".", 1)[1] == "csv":
        csv_to_yaml(args)
    elif args.filename.split(".", 1)[1] == "yaml":
        to_xlsx(args)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-n", "--filename", action="store", dest="filename", help="filename")

    parser.add_argument("-d", "--dest", action="store", dest="destination", help="Folder in which to save output files")

    args = parser.parse_args()
    main(args)