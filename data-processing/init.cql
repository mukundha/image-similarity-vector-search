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