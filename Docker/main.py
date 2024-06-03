import pandas as pd  # Import the pandas library for data manipulation and analysis
import boto3  # Import the boto3 library to interact with AWS services
import io  # Import the io library to handle byte streams
import json  # Import the json library to handle JSON data
import argparse  # Import the argparse library to handle command-line arguments

def main(source_bucket, source_file, destination_bucket, destination_file):
    # Initialize an S3 client using boto3
    s3 = boto3.client('s3')
    
    # Retrieve the CSV file from the source S3 bucket
    obj = s3.get_object(Bucket=source_bucket, Key=source_file)
    
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))

    # Calculate various statistics from the DataFrame
    payment_type = df["payment_type"].value_counts().to_dict()  # Count the occurrences of each payment type
    total_purchase = df["payment_value"].sum().item()  # Calculate the total purchase value
    average_purchase = df["payment_value"].mean().item()  # Calculate the average purchase value
    max_value_purchase = df["payment_value"].max()  # Find the maximum purchase value
    min_value_purchase = df["payment_value"].min()  # Find the minimum purchase value
    payments_with_instalments = df["order_id"][df["payment_installments"] > 1].count().item()  # Count the orders with installments

    # Create a dictionary with the calculated statistics
    data_dict = {
        "total_purchase": total_purchase,
        "average_purchase": average_purchase,
        "max_value_purchase": max_value_purchase,
        "min_value_purchase": min_value_purchase,
        "payments_with_instalments": payments_with_instalments,
        "payment_type": payment_type
    }

    # Convert the dictionary to a JSON string
    json_data = json.dumps(data_dict)

    # Upload the JSON data to the destination S3 bucket
    s3.put_object(Bucket=destination_bucket, Key=destination_file, Body=json_data)

if __name__ == "__main__":
    # Set up argument parsing for command-line arguments
    parser = argparse.ArgumentParser(description="Source and destination, bucket and file are required.")
    parser.add_argument("--source_bucket", required=True, help="Source bucket is required")
    parser.add_argument("--source_file", required=True, help="Source file name is required")
    parser.add_argument("--destination_bucket", required=True, help="Destination bucket is required")
    parser.add_argument("--destination_file", required=True, help="Destination file name is required")
    
    # Parse the command-line arguments
    args = parser.parse_args()
    
    # Call the main function with the parsed arguments
    main(args.source_bucket, args.source_file, args.destination_bucket, args.destination_file)
