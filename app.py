import pandas as pd
import streamlit as st
from sklearn.neighbors import NearestNeighbors

# === Load Data ===
file_path = "SubscriptionUseCase_Dataset.xlsx"
xls = pd.ExcelFile(file_path)

users = pd.read_excel(xls, 'User_Data')
subscriptions = pd.read_excel(xls, 'Subscriptions')
plans = pd.read_excel(xls, 'Subscription_Plans')
logs = pd.read_excel(xls, 'Subscription_Logs')
billing = pd.read_excel(xls, 'Billing_Information')

# === Merge Data ===
subscriptions_merged = subscriptions.merge(plans, on='Product Id', how='left')
subscriptions_full = subscriptions_merged.merge(users, on='User Id', how='left')

# === Feature Engineering ===
features = subscriptions_full[['User Id', 'Price', 'Auto Renewal Allowed']].dropna()
features['Auto Renewal Allowed'] = features['Auto Renewal Allowed'].map({'Yes': 1, 'No': 0})

user_features = features.groupby('User Id').agg({
    'Price': 'mean',
    'Auto Renewal Allowed': 'mean'
})

plans_features = plans[['Product Id', 'Name', 'Price', 'Auto Renewal Allowed']]
plans_features['Auto Renewal Allowed'] = plans_features['Auto Renewal Allowed'].map({'Yes': 1, 'No': 0})

# === Train KNN Model ===
knn = NearestNeighbors(n_neighbors=3, metric='euclidean')
knn.fit(plans_features[['Price', 'Auto Renewal Allowed']])

# === Recommendation Logic ===
def recommend_plans_for_user(user_id, n_recommendations=3):
    if user_id not in user_features.index:
        fallback = plans.sort_values(by='Price').head(n_recommendations)
        fallback['Reason'] = 'No history found - Showing cheapest plans'
        return fallback[['Name', 'Price', 'Auto Renewal Allowed', 'Reason']]
    
    user_vector = user_features.loc[user_id].values.reshape(1, -1)
    distances, indices = knn.kneighbors(user_vector, n_neighbors=n_recommendations)
    recommendations = plans_features.iloc[indices[0]]
    recommendations['Reason'] = 'Similar users liked this'
    return recommendations[['Name', 'Price', 'Auto Renewal Allowed', 'Reason']]

# === Streamlit UI ===
st.title("📊 Personalized Subscription Plan Recommender")

# Dropdown of user IDs and names
user_options = users[['User Id', 'Name']]
user_dict = dict(zip(user_options['Name'], user_options['User Id']))
selected_user_name = st.selectbox("Select a user to get plan recommendations:", list(user_dict.keys()))
selected_user_id = user_dict[selected_user_name]

# Button to get recommendations
if st.button("🎯 Get Recommendations"):
    st.markdown(f"### Top Recommendations for **{selected_user_name}**")
    results = recommend_plans_for_user(selected_user_id)
    st.dataframe(results, use_container_width=True)

# Optional: View all plans
with st.expander("🔍 View All Available Plans"):
    st.dataframe(plans[['Name', 'Price', 'Auto Renewal Allowed']], use_container_width=True)
