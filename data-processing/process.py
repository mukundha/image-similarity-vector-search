import json
import pandas as pd
import os
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

items_path = os.environ.get('ITEMS_PATH')
image_metadata_file = os.environ.get('IMAGE_METADATA_FILE')
images_folder = os.environ.get('IMAGES_FOLDER')
cass_user = os.environ.get('ASTRA_USER')
cass_pw = os.environ.get('ASTRA_PASSWORD')
scb_path = os.environ.get('SECURE_CONNECT_BUNDLE')
keyspace = os.environ.get('KEYSAPCE')
table_name = os.environ.get('TABLE_NAME')
json_data = []
inception_model = hub.KerasLayer("https://tfhub.dev/google/imagenet/inception_v3/feature_vector/4", trainable=False)

def pandas_factory(colnames, rows):
    return pd.DataFrame(rows, columns=colnames)

cloud_config= {
  'secure_connect_bundle': scb_path
}
auth_provider = PlainTextAuthProvider(cass_user, cass_pw)
cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
session = cluster.connect()
session.set_keyspace(keyspace)
session.row_factory = pandas_factory

# This is a long running operation, 
# so this code is just to make sure we can skip
# already loaded data
def get_existing_data():
    paging_state=None
    existing_df = pd.DataFrame()
    fetch_count = 0
    while (fetch_count<=30):    
        rs=session.execute('SELECT DISTINCT item_id from amazon_products', paging_state=paging_state)
        paging_state=rs.paging_state
        result = rs._current_rows
        existing_df = pd.concat([existing_df,result], ignore_index=True)
        if ( result.shape[0]<5000):
            break
        fetch_count +=1
    return existing_df

items_df = pd.read_csv(items_path)
items_df['item_name_language'] = items_df['item_name'].apply(lambda x: x[0]['language_tag'] if isinstance(x, list) and len(x) > 0 else None)
items_df['item_name'] = items_df['item_name'].apply(lambda x: x[0]['value'] if isinstance(x, list) and len(x) > 0 else None)
items_df['brand_language'] = items_df['brand'].apply(lambda x: x[0]['language_tag'] if isinstance(x, list) and len(x) > 0 else None)
items_df['brand'] = items_df['brand'].apply(lambda x: x[0]['value'] if isinstance(x, list) and len(x) > 0 else None)
items_df['product_type'] = items_df['product_type'].apply(lambda x: x[0]['value'] if isinstance(x,list) and len(x) >0 else None)

image_metadata_df = pd.read_csv(image_metadata_file)
existing_df = get_existing_data()

for _,row in items_df.iterrows(): 
    file = None
    if existing_df[existing_df.item_id==row.item_id].shape[0] > 0:
        print(f'skipping existing ID {row.item_id}')
        continue

    try:
        file = image_metadata_df.loc[image_metadata_df.image_id == row.main_image_id,'path'].values[0]
    except:
        print(f'{row.main_image_id} not found, skipping')
        continue    
    image_path = os.path.join(images_folder,file)
    image = tf.io.read_file(image_path)
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.image.convert_image_dtype(image, tf.float32)
    image = tf.image.resize(image, (299, 299))
    image = tf.expand_dims(image, axis=0)    
    embedding = inception_model(image)
    embedding = np.array(embedding[0])
    embedding_list = embedding.tolist()

    insert_query = f"INSERT INTO {keyspace}.{table_name} " \
               f"(brand, bullet_point, color, item_id, item_name, item_weight, model_name, model_number, " \
               f"product_type, main_image_id, other_image_id, item_keywords, country, marketplace, domain_name, " \
               f"node, material, style, item_dimensions, fabric_type, product_description, color_code, finish_type, " \
               f"item_shape, pattern, spin_id, model_year, \"3dmodel_id\", item_name_language, brand_language, " \
               f"image_embedding) " \
               f"VALUES (:brand, :bullet_point, :color, :item_id, :item_name, :item_weight, :model_name, " \
               f":model_number, :product_type, :main_image_id, :other_image_id, :item_keywords, :country, " \
               f":marketplace, :domain_name, :node, :material, :style, :item_dimensions, :fabric_type, " \
               f":product_description, :color_code, :finish_type, :item_shape, :pattern, :spin_id, :model_year, " \
               f":\"3dmodel_id\", :item_name_language, :brand_language, :image_embedding)"
    prepared_stmt = session.prepare(insert_query)
    serialized_row = {}
    for key, value in row.to_dict().items():                
        if isinstance(value, (dict, list, float)) and key!='image_embedding':
            serialized_row[key] = json.dumps(value)                
        else:
            serialized_row[key] = value
    serialized_row['image_embedding'] = embedding_list
    session.execute(prepared_stmt, serialized_row)    
