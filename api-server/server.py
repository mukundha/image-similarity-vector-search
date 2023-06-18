from flask import Flask, request
from flask_cors import CORS
import base64
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import pandas as pd 
import os 

inception_model = hub.KerasLayer("https://tfhub.dev/google/imagenet/inception_v3/feature_vector/4", trainable=False)
cass_user = os.environ.get('CASS_USER')
cass_pw = os.environ.get('CASS_PW')
scb_path =os.environ.get('SCB_PATH') 
keyspace = os.environ.get('KEYSPACE')
table_name = os.environ.get('TABLE_NAME')
image_metadata_file = os.environ.get('IMAGES_METADATA_FILE')
cloud_config= {
  'secure_connect_bundle': scb_path
}
auth_provider = PlainTextAuthProvider(cass_user, cass_pw)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()
session.set_keyspace(keyspace)

image_metadata_df = pd.read_csv(image_metadata_file)

app = Flask(__name__)
CORS(app)

@app.route('/upload', methods=['POST'])
def upload_photo():
    photo_data = request.json.get('photoData')
    image_data = base64.b64decode(photo_data.split(',')[1])
    image = tf.image.decode_jpeg(image_data, channels=3)
    image = tf.image.convert_image_dtype(image, tf.float32)
    image = tf.image.resize(image, (299, 299))
    image = tf.expand_dims(image, axis=0)    
    embedding = inception_model(image)
    embedding = np.array(embedding[0])
    embedding_list = embedding.tolist()

    q1 = f"SELECT * from amazon_products order by image_embedding ANN OF {embedding_list} LIMIT 5"
    rs1 = session.execute(q1)
    response = []
    for r in rs1:
        response.append({
            'item_id': r.item_id,
            'item_name': r.item_name,
            'image_id': f"https://storage.googleapis.com/demo-product-images/{image_metadata_df.path[image_metadata_df.image_id==r.main_image_id].values[0]}"
        })
    print(response)    
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

