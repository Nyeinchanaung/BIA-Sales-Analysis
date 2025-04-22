import joblib


saved_objects = joblib.load('kmeans_with_scaler.pkl')
kmeans = saved_objects['model']
scaler = saved_objects['scaler']

cluster_definition = {0: 'Regular',
                      1: 'Inactive',
                      2: 'Premium',
                      3: 'New'}

def predict_cluster(recency_days, frequnecy, monetary):
    new_data = [[recency_days, frequnecy, monetary]]
    scaled_data = scaler.transform(new_data)
    predicted_cluster = kmeans.predict(scaled_data)
    return cluster_definition[predicted_cluster[0]]