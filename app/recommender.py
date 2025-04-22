import pandas as pd
import numpy as np
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df_customer_feedback = pd.read_csv('dataset/blinkit_customer_feedback.csv')
df_customers = pd.read_csv('dataset/blinkit_customers.csv')
df_products = pd.read_csv('dataset/blinkit_products.csv')
df_orders = pd.read_csv('dataset/blinkit_orders.csv')
df_order_items = pd.read_csv('dataset/blinkit_order_items.csv')

df_orders['order_date'] = pd.to_datetime(df_orders['order_date'])

df_orders.sort_values(by='order_date', inplace=True)

df_orders_train = df_orders[:-500]
df_order_items_train = df_order_items.merge(df_orders_train, on='order_id', how='inner')

df_merge = df_customer_feedback.merge(df_customers, on='customer_id', how='inner')
df_merge = df_merge.merge(df_order_items_train, on='order_id', how='inner')
df_merge = df_merge.merge(df_products, on='product_id', how='inner')

df_merge['customer_id'] = df_merge['customer_id_x']

df = df_merge[['customer_id', 'customer_name','customer_segment','product_id', 'rating','product_name']]

df_customer_segment_rating = df[['customer_segment','rating', 'product_name', 'product_id']].groupby(['customer_segment','product_name', 'product_id']).mean().round(2)

df_customer_profile = df_customers[['customer_id','area','customer_segment','registration_date','total_orders','avg_order_value']]

df_customer_profile = df_customer_profile.merge(df_orders_train, on='customer_id', how='inner')

df_customers['registration_date'] = pd.to_datetime(df_customers['registration_date'])
df_customers['days_since_registration'] = (pd.to_datetime('today') - df_customers['registration_date']).dt.days

df_customer_profile['registration_date'] = pd.to_datetime(df_customer_profile['registration_date'])
df_customer_profile['days_since_registration'] = (pd.Timestamp.now() - df_customer_profile['registration_date']).dt.days

df_products_profile = df_products[['product_id', 'product_name', 'category', 'brand','price','mrp','margin_percentage']]

# Load data into Surprise format
reader = Reader(rating_scale=(1, 5))
data = Dataset.load_from_df(df[['customer_id', 'product_id', 'rating']], reader)

# Split data and train SVD model
trainset, testset = train_test_split(data, test_size=0.25)
model = SVD()
model.fit(trainset)

df_products_profile['content'] = df_products_profile['product_name'].astype(str) \
                                    + ' ' + df_products_profile['category'].astype(str) \
                                    + ' ' + df_products_profile['brand'].astype(str) \
                                    + ' price - ' + df_products_profile['price'].astype(str) \
                                    + ' mrp - ' + df_products_profile['mrp'].astype(str) \
                                    + ' margin - ' + df_products_profile['margin_percentage'].astype(str)

vectorizer = TfidfVectorizer()
product_tfidf = vectorizer.fit_transform(df_products_profile['content'])

class CollaborativeRecommender1:
    def __init__(self, top_n=10):
        self.top_n = top_n
        self.df_customer_segment_rating = df_customer_segment_rating
        self.df_customers = df_customers
        
    def recommend(self, customer_id):
        customer_segment = self.df_customers[self.df_customers['customer_id'] == customer_id]['customer_segment'].values[0]
        return self.df_customer_segment_rating.loc[customer_segment].reset_index().sort_values(by='rating', ascending=False).head(self.top_n)[['product_id', 'product_name']]

class CollaborativeRecommender2:
    def __init__(self, top_n=10):
        self.top_n = top_n
        self.model = model
        self.df_products = df_products
        
    def recommend(self, customer_id):
        product_ids = []
        ratings = []
        product_names = []
        for product_id in self.df_products['product_id'].unique():
            rating = self.model.predict(customer_id, product_id).est
            product_ids.append(product_id)
            ratings.append(rating)
            product_names.append(self.df_products[self.df_products['product_id'] == product_id]['product_name'].values[0])
    
        recommendations = pd.DataFrame({
            'product_id': product_ids,
            'rating': ratings,
            'product_name': product_names
        })
        recommendations = recommendations.sort_values('rating', ascending=False)
        return recommendations.head(self.top_n)[['product_id', 'product_name']]

class ContentBasedRecommender:
    def __init__(self, top_n=10):
        self.top_n = top_n
        self.product_tfidf = product_tfidf
        self.vectorizer = vectorizer
        self.df_customers = df_customers
        self.df_products_profile = df_products_profile
        
    def recommend(self, customer_id):
        customer = self.df_customers[self.df_customers['customer_id'] == customer_id]
        if customer.empty:
            print(f'Customer ID {customer_id} not found.')
            return []
        # Use customer segment as a preference (could be improved with more data)
        segment = customer.iloc[0]['customer_segment']
        # Use customer area
        area = customer.iloc[0]['area']
        # Use total orders
        total_orders = customer.iloc[0]['total_orders']
        # Use average order value
        avg_order_value = customer.iloc[0]['avg_order_value']
        # Use days since registration
        days_since_registration = customer.iloc[0]['days_since_registration']
        # Use customer profile
        profile = segment + ' ' + str(area) + ' ' + str(total_orders) + ' ' + str(avg_order_value) + ' ' + str(days_since_registration)
        profile_vec = self.vectorizer.transform([profile])
        # Compute cosine similarity between customer profile and products
        sims = cosine_similarity(profile_vec, self.product_tfidf).flatten()
        top_indices = sims.argsort()[-self.top_n:][::-1]
        recommendations = self.df_products_profile.iloc[top_indices][['product_id','product_name']]
        return recommendations

class HybridRecommender1:
    def __init__(self, top_n=10):
        self.top_n = top_n
        self.recommender1 = ContentBasedRecommender(int(top_n/2))
        self.recommender2 = CollaborativeRecommender1(int(top_n/2))
        
    def recommend(self, customer_id):
        recommendations1 = self.recommender1.recommend(customer_id)
        recommendations2 = self.recommender2.recommend(customer_id)
        return pd.concat([recommendations1, recommendations2], ignore_index=True)
    
class HybridRecommender2:
    def __init__(self, top_n=10):
        self.top_n = top_n
        self.recommender1 = ContentBasedRecommender(int(top_n/2))
        self.recommender2 = CollaborativeRecommender2(int(top_n/2))
        
    def recommend(self, customer_id):
        recommendations1 = self.recommender1.recommend(customer_id)
        recommendations2 = self.recommender2.recommend(customer_id)
        return pd.concat([recommendations1, recommendations2], ignore_index=True)