import pandas as pd
import numpy as np
import json


def read_data(file, filename):
    data_json = {}

    # Read the entire sheet
    df = pd.read_excel(file, sheet_name='Sheet1', header=None)

    # Slice the relevant portion (assuming data starts from B2 and headers are in rows 2 and 3)
    start_row, end_row = 1, 2
    start_col, end_col = 1, 9

    # Extract the headers
    headers = df.iloc[start_row:end_row + 1, start_col:end_col + 1]
    heads = ['Load_Size', 'Machine Type', 'Finish', 'Fabric', 'Recipe', 'FNO']
    stepID = 0
    for i in heads:
        mask = headers.eq(i)
        positions = list(zip(*np.where(mask)))

        if i in ['Finish', 'Fabric']:
            header_position = headers.eq(i)
            header_positions = list(zip(*np.where(header_position)))
            value = headers.iloc[header_positions[0][0], header_positions[0][1] + 3]
            data_json[i] = value
        else:
            header_position = headers.eq(i)
            header_positions = list(zip(*np.where(header_position)))
            value = headers.iloc[header_positions[0][0], header_positions[0][1] + 1]
            data_json[i] = value

    # Select the data from the DataFrame starting from the 4th row (index 3)
    data = df.iloc[3:, ]

    # Extract the column names from the first row of the data
    data_columns = data.iloc[0]

    # Drop the first row of the data (which contains the column names)
    data = data.drop(3).reset_index(drop=True)

    # Set the column names
    data.columns = data.iloc[0]

    # Forward fill relevant columns
    data['LTRs'] = data['LTRs'].ffill(axis=0)
    data['RPM'] = data['RPM'].ffill(axis=0)
    data['Centigrade'] = data['Centigrade'].ffill(axis=0)
    data['ACTION'] = data['ACTION'].ffill(axis=0)
    data['MINS.'] = data['MINS.'].ffill(axis=0)

    # Initialize variables for tracking previous action and step
    prev_action = None
    step = 0
    modified_chemicals = []


    for index, row in data.iterrows():
        if pd.notnull(row['ACTION']):
            if row['ACTION'] != prev_action:
                step = index + 1
                row = row.fillna('None')
                dict_row = row.to_dict()
                dict_row['Chemicals'] = [{'name': row['Chemical Name'], '%': row['%'], 'Dosage': row['Dosage']}]
                dict_row.pop('Chemical Name')
                dict_row.pop('%')
                dict_row.pop('Dosage')
                data_json[step] = dict_row
                prev_action = row['ACTION']
            else:
                row = row.fillna('None')
                data_json[step]['Chemicals'].append(
                    {'name': row['Chemical Name'], '%': row['%'], 'Dosage': row['Dosage']})

    # Process the data to create the modified chemicals data
    for i in data_json.values():
        if isinstance(i, dict) and i.get('ACTION') != 'UnLoad':
            processed_step = {
                'step_id': stepID,
                'step_no': i.get('STEP', 'None') if i.get('STEP', 'None') not in [None, "None"] else 0,
                'action': i.get('ACTION', 'None'),
                'minutes': 0.0 if i.get('MINS.') in ["MINS.", "None", None] else round(float(i['MINS.']), 1),
                'litres': 0 if i.get('LTRs') in ["LTRs", "None", None] else i['LTRs'],
                'rpm': 0 if i.get('RPM') in ["RPM", "None", None] else i['RPM'],
                'temperature': 0 if i.get('Centigrade') in ["Centigrade", "None", None] else i['Centigrade'],
                'PH': 0 if i.get('PH') in ["PH", "None", None] else i['PH'],
                'LR': 0 if i.get('LR') in ["LR", "None", None] else i['LR'],
                'TDS': 0 if i.get('TDS') in ["TDS", "None", None] else i['TDS'],
                'TSS': 0 if i.get('TSS') in ["TSS", "None", None] else i['TSS'],
                'chemicals': []
            }
            stepID = stepID + 1

            for j in i.get('Chemicals', []):
                # Safely convert the percentage to a float, defaulting to 0.0 if conversion fails
                try:
                    percentage = round(float(j['%']), 6)
                except ValueError:
                    percentage = 0.0

                if j['name'] != 'None':
                    chemical = {
                        'recipe_name': j['name'],
                        'percentage': percentage,
                        'dosage': j['Dosage'] if j['Dosage'] not in [None, "None"] else 0,
                    }
                    processed_step['chemicals'].append(chemical)

            modified_chemicals.append(processed_step)

    # Construct the final recipe data
    recipe = {
        'file_name': filename,
        'load_size': data_json.get('Load_Size', 'None'),
        'machine_type': data_json.get('Machine Type', 'None'),
        'finish': data_json.get('Finish', 'None'),
        'fabric': data_json.get('Fabric', 'None'),
        'recipe_no': data_json.get('Recipe', 'None'),
        'Fno': data_json.get('FNO', 'None'),
        'step': modified_chemicals[1:]
    }

    return recipe

