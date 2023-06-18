# Image Similarity with Vector Search

Demonstrate Datastax [Astra's](https://docs.datastax.com/en/astra-serverless/docs/vector-search/overview.html) Vector search with Image similarity search using Amazon Berkeley Objects (ABO) Dataset

## Demo

https://github.com/mukundha/image-similarity-vector-search/assets/1277515/6846ef4e-beee-4b05-a50a-edec66d6df9f


Click [here](https://mukundha.web.app/) for a live demo. Try it on your mobile.

--- 

Follow along to setup this demo yourself and learn how to do image similarity with Vector search

This repository includes 3 sections 

1. Data processing
- Generate Vector embeddings for Images
- Load Vector embeddings into Astra
2. API - Similarity search 
- Exposes an API to perform Vector search and retrieve similar images
3. UI App
- Allows users to capture images and search for similar images

## 1. Data processing

Refer to [Citation](#citation) for how to download and get access to this dataset.

Dataset includes `147,702` products and `398,212` unique catalog images

Code is in `data-processing` folder.

#### Initialize DB

Review the Astra [Getting started](https://docs.datastax.com/en/astra-serverless/docs/getting-started/getting-started.html) guide, if needed.

Create the products table with Vector<> column to represent main_image_id of the product and SAI index for the Vector column. 

```
CREATE TABLE amazon_products (
    brand TEXT,
    bullet_point TEXT,
    color TEXT,
    item_id TEXT,
    item_name TEXT,
    item_weight TEXT,
    model_name TEXT,
    model_number TEXT,
    product_type TEXT,
    main_image_id TEXT,
    other_image_id TEXT,
    item_keywords TEXT,
    country TEXT,
    marketplace TEXT,
    domain_name TEXT,
    node TEXT,
    material TEXT,
    style TEXT,
    item_dimensions TEXT,
    fabric_type TEXT,
    product_description TEXT,
    color_code TEXT,
    finish_type TEXT,
    item_shape TEXT,
    pattern TEXT,
    spin_id TEXT,
    model_year TEXT,
    "3dmodel_id" TEXT,
    item_name_language TEXT,
    brand_language TEXT,
    image_embedding Vector<FLOAT,2048>,
    PRIMARY KEY (item_id,domain_name)
);

CREATE CUSTOM INDEX IF NOT EXISTS image_embedding_index ON demo.amazon_products (image_embedding) USING 'org.apache.cassandra.index.sai.StorageAttachedIndex'
```

#### Generate Vector embedding and Load data


You should download `abo-listings.tar` and `abo-images-small.tar` to your workstation, untar it.

```
tar -xvf abo-listings.tar
gunzip abo-listings/listings/metadata/listings_*.gz
```
```
import pandas as pd
import glob

json_files = "abo-listings/listings/metadata/listings_*.json"

dfs = []

for file in glob.glob(json_files):
    df = pd.read_json(file, lines=True)
    dfs.append(df)

merged_df = pd.concat(dfs)
output_file = "items.csv"
merged_df.to_csv(output_file, index=False)
```

Setup your environment

Refer [here](https://docs.datastax.com/en/astra-serverless/docs/getting-started/gs-drivers.html#_connect_to_your_astra_db_cluster), if you need help getting Astra credentials

```
export ITEMS_PATH=<path to items.csv generated in prev step>
export IMAGE_METADATA_FILE="<path>/abo-images-small/images/metadata/images.csv"
export IMAGES_FOLDER="<path>/abo-images-small/images/small"

export ASTRA_USER='ASTRA_CLIENTID'
export ASTRA_PASSWORD='ASTRA_CLIENTSECRET'
export SECURE_CONNECT_BUNDLE='SCB ZIP FILE PATH'
export KEYSPACE='KEYSPACE'
export TABLE_NAME='TABLE_NAME'
```

----
This code uses [Inception model](https://tfhub.dev/google/imagenet/inception_v3/feature_vector/5) to get feature vector for Images.

Vector size: 2048

----


```
python3 process.py
```

---
[Optional] This might run long, depending on your machine and network speed, it needs to load >100k images. You might want to parallelize this or split the items.csv to smaller chunks and run from multiple machines. Optimizing this is a exercise to the reader

It took me about an hour to load all image embeddings, with 3 nodes.

---

## Similarity Search API

API Spec

Request

```
POST /upload
Content-type: application/json

{"photoData":"data:image/jpeg;base64,xxxxx..."}
```

Response: Similar Images
```
[
    {
        "image_id": "https://storage.googleapis.com/demo-product-images/35/35952a54.jpg",
        "item_id": "B07RC7R3TC",
        "item_name": "xxx"
    },
    {
        "image_id": "https://storage.googleapis.com/demo-product-images/5a/5a735214.jpg",
        "item_id": "B081HN8L6R",
        "item_name": 'XXX"
    },
    {
        "image_id": "https://storage.googleapis.com/demo-product-images/24/2435b28d.jpg",
        "item_id": "B07T7KPCM1",
        "item_name": "Amazon Brand - Solimo Designer Birds 3D Printed Hard Back Case Mobile Cover for LG K7"
    },
    {
        "image_id": "https://storage.googleapis.com/demo-product-images/2e/2e271e7c.jpg",
        "item_id": "B081HMTVLV",
        "item_name": "XXX"
    },
    {
        "image_id": "https://storage.googleapis.com/demo-product-images/cf/cf9f5a3a.jpg",
        "item_id": "B07Z497KW2",
        "item_name": "XXX"
    }
]
```

Query
```
f"SELECT * from {table_name} order by image_embedding ANN OF {input_image_vector} LIMIT 5"
```

Code: `api-server/server.py`

---

## UI App

In `App.js`

Replace `Line 24` with your API Server URL

```
const response = await axios.post('<api-server>/upload', { photoData });
```

```
npm start
```
--- 

### Attribution

| Description | Credit |
|---|---|
| Credit for the data, including all images and 3D models| Amazon.com |
|Credit for building the dataset, archives and benchmark sets| <p> Jasmine Collins <p> Shubham Goel <p> Kenan Deng <p> Achleshwar Luthra <p> Leon Xu <p> Erhan Gundogdu <p> Xi Zhang <p> Tomas F. Yago Vicente <p> Thomas Dideriksen <p> Himanshu Arora <p> Matthieu Guillaumin<p> Jitendra Malik<p> **UC Berkeley, Amazon, BITS Pilani**


### Citation

[ABO: Dataset and Benchmarks for Real-World 3D Object Understanding](https://arxiv.org/abs/2110.06199)

[Dataset Homepage](https://amazon-berkeley-objects.s3.amazonaws.com/index.html#home)

```
@article{collins2022abo,
  title={ABO: Dataset and Benchmarks for Real-World 3D Object Understanding},
  author={Collins, Jasmine and Goel, Shubham and Deng, Kenan and Luthra, Achleshwar and
          Xu, Leon and Gundogdu, Erhan and Zhang, Xi and Yago Vicente, Tomas F and
          Dideriksen, Thomas and Arora, Himanshu and Guillaumin, Matthieu and
          Malik, Jitendra},
  journal={CVPR},
  year={2022}
}
```
----

`imagenet/inception_v3/feature_vector`

Feature vectors of images with Inception V3 trained on ImageNet (ILSVRC-2012-CLS).


|Publisher| Google License: Apache-2.0|
|--|--|
|Architecture|Inception V3|
|Dataset|ImageNet (ILSVRC-2012-CLS)|
|License | Apache2.0|
---