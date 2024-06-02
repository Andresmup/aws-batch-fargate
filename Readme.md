#


## LOCAL TEST AND SETUP

docker run --rm -v ~/.aws:/root/.aws aws-batch-payment-processing orders-dataset-for-batch-processing payments.csv results-batch-payment-processing results.json

## ECR 

aws ecr create-repository --repository-name batch-payment-processing

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 604476232840.dkr.ecr.us-east-1.amazonaws.com

docker build -t batch-payment-processing .

docker tag batch-payment-processing:latest 604476232840.dkr.ecr.us-east-1.amazonaws.com/batch-payment-processing:latest

docker push 604476232840.dkr.ecr.us-east-1.amazonaws.com/batch-payment-processing:latest
