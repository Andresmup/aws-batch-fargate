import pandas as pd
import boto3
import io
import json
import argparse

def main(source_bucket, source_file, destination_bucket, destination_file):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=source_bucket, Key=source_file)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))

    payment_type = df["payment_type"].value_counts().to_dict()
    total_purchase = df["payment_value"].sum().item()
    average_purchase = df["payment_value"].mean().item()
    max_value_purchase = df["payment_value"].max()
    min_value_purchase = df["payment_value"].min()
    payments_with_instalments = df["order_id"][df["payment_installments"] > 1].count().item() 

    data_dict = {
    "total_purchase": total_purchase,
    "average_purchase": average_purchase,
    "max_value_purchase": max_value_purchase,
    "min_value_purchase": min_value_purchase,
    "payments_with_instalments": payments_with_instalments,
    "payment_type": payment_type
    }

    json_data = json.dumps(data_dict)

    s3.put_object(Bucket=destination_bucket, Key=destination_file, Body=json_data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Source and destination, bucket and file are required.")
    parser.add_argument("--source_bucket", required=True, help="Source bucket is required")
    parser.add_argument("--source_file", required=True, help="Source file name is required")
    parser.add_argument("--destination_bucket", required=True, help="Destination bucket is required")
    parser.add_argument("--destination_file", required=True, help="Destination file name is required")
    args = parser.parse_args()
    main(args.source_bucket, args.source_file, args.destination_bucket, args.destination_file)