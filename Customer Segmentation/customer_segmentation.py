import joblib


saved_objects = joblib.load('kmeans_with_scaler.pkl')
kmeans = saved_objects['model']
scaler = saved_objects['scaler']

cluster_definition = {0: 'Regular',
                      1: 'Inactive',
                      2: 'Premium',
                      3: 'New'}
# predict_cluster(20, 1, 1000)
def predict_cluster(recency_days, frequnecy, monetary):
    new_data = [[recency_days, frequnecy, monetary]]
    scaled_data = scaler.transform(new_data)
    predicted_cluster = kmeans.predict(scaled_data)
    cluster_center = kmeans.cluster_centers_[predicted_cluster]
    importance = scaled_data[0] - cluster_center
    return cluster_definition[predicted_cluster[0]], importance[0]