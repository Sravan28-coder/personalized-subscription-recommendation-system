import pandas as pd
from sklearn.neighbors import NearestNeighbors

# Load Excel file
file_path = "SubscriptionUseCase_Dataset.xlsx"  # Make sure this is the correct path
xls = pd.ExcelFile(file_path)

# Read all sheets
users = pd.read_excel(xls, 'User_Data')
subscriptions = pd.read_excel(xls, 'Subscriptions')
plans = pd.read_excel(xls, 'Subscription_Plans')
logs = pd.read_excel(xls, 'Subscription_Logs')
billing = pd.read_excel(xls, 'Billing_Information')

# Merge subscriptions with plans
subscriptions_merged = subscriptions.merge(plans, left_on='Product Id', right_on='Product Id', how='left')

# Merge with users
subscriptions_full = subscriptions_merged.merge(users, left_on='User Id', right_on='User Id', how='left')

# Preprocess features
features = subscriptions_full[['User Id', 'Price', 'Auto Renewal Allowed']].dropna()
features['Auto Renewal Allowed'] = features['Auto Renewal Allowed'].map({'Yes': 1, 'No': 0})

# Group by user for average behavior
user_features = features.groupby('User Id').agg({
    'Price': 'mean',
    'Auto Renewal Allowed': 'mean'
})

# Prepare plan features for recommendation
plans_features = plans[['Product Id', 'Name', 'Price', 'Auto Renewal Allowed']]
plans_features['Auto Renewal Allowed'] = plans_features['Auto Renewal Allowed'].map({'Yes': 1, 'No': 0})

# Train KNN model
knn = NearestNeighbors(n_neighbors=3, metric='euclidean')
knn.fit(plans_features[['Price', 'Auto Renewal Allowed']])

# Recommendation function with fallback
def recommend_plans_for_user(user_id, n_recommendations=3):
    if user_id not in user_features.index:
        print(f"User {user_id} not found or no subscription data. Recommending top {n_recommendations} cheapest plans.")
        fallback = plans.sort_values('Price').head(n_recommendations)
        return fallback[['Product Id', 'Name', 'Price']]

    user_vector = user_features.loc[user_id, ['Price', 'Auto Renewal Allowed']].values.reshape(1, -1)
    distances, indices = knn.kneighbors(user_vector, n_neighbors=n_recommendations)
    recommended_plans = plans_features.iloc[indices[0]]
    return recommended_plans[['Product Id', 'Name', 'Price']]

# Example usage
target_user_id = 1
recommendations = recommend_plans_for_user(target_user_id)
print(f"\nTop {len(recommendations)} Recommended Plans for User {target_user_id}:")
print(recommendations)
