import pandas as pd
from sklearn.neighbors import NearestNeighbors
import numpy as np

# Load data from Excel
file_path = 'SubscriptionUseCase_Dataset.xlsx'

user_data = pd.read_excel(file_path, sheet_name='User_Data')
subscriptions = pd.read_excel(file_path, sheet_name='Subscriptions')
plans = pd.read_excel(file_path, sheet_name='Subscription_Plans')
subscription_logs = pd.read_excel(file_path, sheet_name='Subscription_Logs')
billing_info = pd.read_excel(file_path, sheet_name='Billing_Information')

# Merge datasets step-by-step
full_data = subscriptions.merge(user_data, left_on='User Id', right_on='User Id', how='left')
full_data = full_data.merge(plans, left_on='Product Id', right_on='Product Id', how='left')
full_data = full_data.merge(billing_info.groupby('subscription_id').agg(
    total_billed=('amount', 'sum'),
    avg_billed=('amount', 'mean'),
    failed_payments=('payment_status', lambda x: sum(x != 'paid'))
).reset_index(), left_on='Subscription Id', right_on='subscription_id', how='left')

# Fill missing billing info with zeros
full_data[['total_billed', 'avg_billed', 'failed_payments']] = full_data[['total_billed', 'avg_billed', 'failed_payments']].fillna(0)

# Feature Engineering with .copy() to avoid SettingWithCopyWarning
features = full_data[['User Id', 'Price', 'Auto Renewal Allowed', 'total_billed', 'avg_billed', 'failed_payments']].copy()
features['Auto Renewal Allowed'] = features['Auto Renewal Allowed'].map({'Yes': 1, 'No': 0})
features = features.dropna()

# Aggregate per user for user features
user_features = features.groupby('User Id').agg({
    'Price': 'mean',
    'Auto Renewal Allowed': 'mean',
    'total_billed': 'mean',
    'avg_billed': 'mean',
    'failed_payments': 'mean'
}).fillna(0)

print("User IDs available for recommendation:", user_features.index.tolist())

# Prepare plans feature matrix (plans to recommend from)
plans_features = plans.copy()
plans_features['Auto Renewal Allowed'] = plans_features['Auto Renewal Allowed'].map({'Yes': 1, 'No': 0})
plans_features = plans_features[['Product Id', 'Price', 'Auto Renewal Allowed']]

# Fit KNN on plans features
knn = NearestNeighbors(n_neighbors=3, metric='euclidean')
knn.fit(plans_features[['Price', 'Auto Renewal Allowed']])

def recommend_plans_for_user(user_id, n_recommendations=3):
    if user_id not in user_features.index:
        return f"User {user_id} not found."

    user_vector = user_features.loc[user_id, ['Price', 'Auto Renewal Allowed']].values.reshape(1, -1)
    
    distances, indices = knn.kneighbors(user_vector, n_neighbors=n_recommendations)
    recommended_plans = plans_features.iloc[indices[0]]

    return recommended_plans[['Product Id', 'Price', 'Auto Renewal Allowed']]

# Example usage:
user_to_recommend = 1
print(f"Top {3} Recommended Plans for User {user_to_recommend}:")
print(recommend_plans_for_user(user_to_recommend))
