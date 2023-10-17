"""CDN manager."""
import os
from io import BytesIO
import boto3
import streamlit as st
from PIL import Image

# Constants
CLOUDFRONT_DIST_NAME = os.getenv("CLOUDFRONT_DIST_NAME")
CATEGORIES = [
    "ALL",
    "race-events",
    "offroad",
    "car-shows",
    "misc",
    "rallyx",
    "gfx",
    "food",
    "clients",
]
SUBCATEGORIES = ["ALL", "general", "other", "photo", "video"]
BUCKET_LIST = [CLOUDFRONT_DIST_NAME]
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# Initialize boto3 S3 client
s3 = boto3.client("s3", aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)


def generate_cloudfront_url(bucket, key):
    """Generate a CloudFront URL for a given S3 key."""
    return f"https://{bucket}/{key}"


def get_all_buckets():
    """Retrieve a list of all available buckets."""
    # the app should pull all buckets available to ourselves
    buckets = [bucket["Name"] for bucket in s3.list_buckets()["Buckets"]]
    filtered_buckets= []
    for bucket in buckets:
        if 'www' in bucket or 'cdn' in bucket:
            filtered_buckets.append(bucket)
    return filtered_buckets


def view_bucket_content():
    """View bucket."""
    st.title("S3 CDN Manager")

    # Sidebar selection for buckets, categories, and subcategories
    available_buckets = get_all_buckets()
    selected_bucket = st.sidebar.selectbox("Select a Bucket:", available_buckets)
    selected_category = st.sidebar.selectbox("Select a Category:", CATEGORIES)
    selected_subcategory = st.sidebar.selectbox("Select a Subcategory:", SUBCATEGORIES)

    prefix = ""
    if selected_category != "ALL":
        prefix = f"{selected_category}/"
        if selected_subcategory != "ALL":
            prefix += f"{selected_subcategory}/"

    # Fetch objects from the selected S3 bucket
    objects = s3.list_objects_v2(Bucket=selected_bucket, Prefix=prefix)

    num_cols = 3
    # Display content in a grid
    cols = st.columns(num_cols)
    for index, key in enumerate([obj["Key"] for obj in objects.get("Contents", [])]):
        col = cols[index % num_cols]

        if key.lower().endswith((".jpg", ".jpeg", ".png")):
            img_data = s3.get_object(Bucket=selected_bucket, Key=key)["Body"].read()
            img = Image.open(BytesIO(img_data))
            col.image(img, caption=generate_cloudfront_url(selected_bucket, key))
        elif key.lower().endswith((".mp4", ".mkv", ".avi")):
            video_data = s3.get_object(Bucket=selected_bucket, Key=key)["Body"].read()
            col.video(video_data, format="video/mp4")
            col.markdown(f"**{generate_cloudfront_url(selected_bucket, key)}**")

        # Action buttons with unique keys for each widget
        if col.button("Delete", key=f"delete_{key}"):
            s3.delete_object(Bucket=selected_bucket, Key=key)
            st.success(f"Deleted {key}!")

        download_url = f"https://{selected_bucket}/{key}"
        col.markdown(f"[Download]({download_url})", unsafe_allow_html=True)

        new_name = col.text_input("Rename to:", key=f"rename_{key}")
        if new_name:
            new_key = f"{'/'.join(key.split('/')[:-1])}/{new_name}.{key.split('.')[-1]}"
            s3.copy_object(Bucket=selected_bucket, CopySource=key, Key=new_key)
            s3.delete_object(Bucket=selected_bucket, Key=key)
            st.success(f"Renamed {key} to {new_key}!")


def get_distribution_id_by_domain(domain_name):
    """
    Fetch the CloudFront distribution ID based on the domain name.

    Parameters:
        domain_name (str): The domain name of the CloudFront distribution.

    Returns:
        str: The CloudFront distribution ID if found, otherwise None.
    """
    cloudfront = boto3.client("cloudfront")
    paginator = cloudfront.get_paginator("list_distributions")

    # Iterate through all distributions
    for page in paginator.paginate():
        for distribution in page["DistributionList"]["Items"]:
            if distribution["DomainName"] == domain_name:
                return distribution["Id"]

    return None


def upload_content():
    """Upload content."""
    st.title("Upload to S3 Bucket")

    # Sidebar selection for buckets
    available_buckets = get_all_buckets()
    selected_bucket = st.sidebar.selectbox("Select a Bucket:", available_buckets)

    # File uploader, category, subcategory, and item name input
    uploaded_file = st.file_uploader(
        "Choose a file", type=["jpg", "jpeg", "png", "mp4", "mkv", "avi"]
    )
    category = st.selectbox("Select Category:", CATEGORIES[1:])  # exclude the "ALL"
    subcategory = st.selectbox(
        "Select Subcategory:", SUBCATEGORIES[1:]  # exclude the "ALL"
    )

    if uploaded_file:
        fname = str(uploaded_file.name)
        fname = fname.lower().replace(" ", "-")
        item_name = st.text_input("Item Name:", fname)

        if st.button("Upload to CDN"):
            # If a file is uploaded and item name is provided, upload to S3
            # if uploaded_file and item_name:
            file_bytes = uploaded_file.read()
            # file_extension = uploaded_file.name.split(".")[-1]
            s3_key = f"{category}/{subcategory}/{item_name}"

            # Upload to S3
            s3.put_object(
                Bucket=selected_bucket,
                Key=s3_key,
                Body=file_bytes,
                ContentType=uploaded_file.type,  # to maintain the file's original content type
            )
            st.success(f"File uploaded successfully to {s3_key}!")


def main():
    """main.py"""
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Choose a Page:", ["View Bucket Content", "Upload Content"])

    if page == "View Bucket Content":
        view_bucket_content()
    elif page == "Upload Content":
        upload_content()


if __name__ == "__main__":
    main()
