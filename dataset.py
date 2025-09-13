import pandas as pd

# Path to your Excel file
file_path = "SubscriptionUseCase_Dataset.xlsx"

# Load all sheets into separate DataFrames
xls = pd.read_excel(file_path, sheet_name=None)

# Access individual sheets
user_data = xls['User_Data']
subscriptions = xls['Subscriptions']
subscription_plans = xls['Subscription_Plans']
subscription_logs = xls['Subscription_Logs']
billing_info = xls['Billing_Information']

# Preview
print(user_data.head())
print(subscriptions.head())
print(subscription_plans.head())
print(subscription_logs.head())
print(billing_info.head())
