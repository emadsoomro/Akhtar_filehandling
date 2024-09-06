import pandas as pd

# Manually set the column names (adjust as needed)
column_names = ['STEP', 'ACTION', 'MIN.', 'LITRES', 'RPM', 'Chemical Name', 'Percentage', 'Dosage', 'Centigrade', 'PH', 'TDS', 'TSS']
df = pd.read_excel('file1.xls', sheet_name='Sheet1', header=None, names=column_names)

# Check if 'ACTION' exists
if 'ACTION' in df.columns:
    actions_df = df[df['ACTION'].notna()]

    # Mapping actions to chemical names
    action_chemicals = {}

    for index, row in actions_df.iterrows():
        action = row['ACTION']
        chemicals = df.loc[index+1:index+5, 'Chemical Name'].dropna().tolist()
        action_chemicals[action] = chemicals

    # Display the results
    for action, chemicals in action_chemicals.items():
        print(f"Action: {action} -> Chemicals: {', '.join(chemicals)}")
else:
    print("The column 'ACTION' was not found.")


# # Filter the DataFrame to get the rows where the action is defined
# actions_df = df[df['ACTION'].notna()]
#
# # Initialize a dictionary to store action-chemical mapping
# action_chemicals = {}
#
# # Iterate through the DataFrame to map actions to chemical names
# for index, row in actions_df.iterrows():
#     action = row['ACTION']
#     chemicals = df.loc[index+1:index+5, 'Chemical Name'].dropna().tolist()
#     action_chemicals[action] = chemicals
#
# # Display the mapping
# for action, chemicals in action_chemicals.items():
#     print(f"Action: {action} -> Chemicals: {', '.join(chemicals)}")
