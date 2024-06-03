#
## CONFIGURE LOCAL SETUP

```sh
mkdir aws-batch-fargate #Create a directory for the proyect
cd aws-batch-fargate #Cd into the directory
git init
```

```sh
mkdir Docker #Create Docker folder
mkdir .github/workflows #Create .github folder and workflows folfer for github action config
mkdir test-resources #Create a folder for the test dataset
```

```sh
cd test-resources #Cd into resourcer folder
wget https://raw.githubusercontent.com/Andresmup/ArchivosDataScience/main/payments.csv #Download demo csv dataset with payments
```

## CONFIGURE S3 BUCKETS

```sh
aws s3 mb s3://prod-source-payments-for-processing #Create a bucket with name prod-source-payments-for-processing
```

```sh
aws s3 mb s3://prod-destination-payments-batch-processed #Create a bucket with name rod-destination-payments-batch-processed
```

```sh
aws s3 cp test-resources/payments.csv s3://prod-source-payments-for-processing #Upload the local content test-resources/payments.csv to the bucket prod-source-payments-for-processing
```

## DOCKER DEV

```sh
cd Docker
touch Dockerfile
touch main.py
touch requirements.txt
```

```sh
docker build -t aws-batch-payment-processing .
```

## LOCAL TEST AND SETUP

```sh
docker run --rm -v ~/.aws:/root/.aws aws-batch-payment-processing orders-dataset-for-batch-processing payments.csv results-batch-payment-processing results.json
```

## ECR MANUAL SETUP

```sh
aws ecr create-repository --repository-name batch-payment-processing
```

```sh
aws_account_id=$(aws sts get-caller-identity --query "Account" --output text)
```
```sh
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $aws_account_id.dkr.ecr.us-east-1.amazonaws.com
```

```sh
docker tag batch-payment-processing:latest $aws_account_id.dkr.ecr.us-east-1.amazonaws.com/batch-payment-processing:latest
```

```sh
docker push $aws_account_id.dkr.ecr.us-east-1.amazonaws.com/batch-payment-processing:latest
```

## POLICY AND ROLE CREATION

### Setup

```sh
touch policy-prod-source.json
touch policy-prod-dest.json
touch policy-get-token.json
touch policy-push-ecr.json
```

### Policies

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::prod-source-payments-for-processing/*"
        }
    ]
}
```

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::prod-destination-payments-batch-processed/*"
        }
    ]
}
```

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "GetAuthorizationToken",
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken"
            ],
            "Resource": "*"
        }
    ]
}
```

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowPushOnly",
            "Effect": "Allow",
            "Action": [
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:BatchCheckLayerAvailability",
                "ecr:CompleteLayerUpload",
                "ecr:InitiateLayerUpload",
                "ecr:PutImage",
                "ecr:UploadLayerPart"
            ],
            "Resource": "arn:aws:ecr:us-east-1:604476232840:repository/batch-payment-processing"
        }
    ]
}
```

```sh
aws iam create-policy --policy-name AllowGetObjectsProdSourcePaymentBucket --policy-document file://policy-prod-source.json
aws iam create-policy --policy-name AllowPutObjectProdDestinationPaymentBucket --policy-document file://policy-prod-dest.json
aws iam create-policy --policy-name AllowGetTokenECRLogin --policy-document file://policy-get-token.json
aws iam create-policy --policy-name AllowPushOnlyBatchPaymentProcessing --policy-document file://policy-push-ecr.json
```

### Roles

```sh
aws iam create-role --role-name github-action-machine-push-ecr-image --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::$aws_account_id:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:<github_account>/<repository>:*"
                }
            }
        }
    ]
}'

aws iam attach-role-policy --role-name ecsS3ProdPayment --policy-arn arn:aws:iam::$aws_account_id:policy/AllowGetTokenECRLogin
aws iam attach-role-policy --role-name ecsS3ProdPayment --policy-arn arn:aws:iam::$aws_account_id:policy/AllowPushOnlyBatchPaymentProcessing
```


```sh
aws iam create-role --role-name ecsS3ProdPayment --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}'

aws iam attach-role-policy --role-name ecsS3ProdPayment --policy-arn arn:aws:iam::$aws_account_id:policy/AllowPushOnlyBatchPaymentProcessing
aws iam attach-role-policy --role-name ecsS3ProdPayment --policy-arn arn:aws:iam::$aws_account_id:policy/AllowPutObjectProdDestinationPaymentBucket
```

```sh
aws iam create-role --role-name ecsTaskExecutionRole --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}' --description "Role for ecs execution" --max-session-duration 3600 --permissions-boundary "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
```

```sh
aws iam create-role --role-name AWSServiceRoleForECS --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}' --description "AWSServiceRoleForECS" --max-session-duration 3600 --permissions-boundary "arn:aws:iam::aws:policy/aws-service-role/AmazonECSServiceRolePolicy"
```

```sh
aws iam create-role --role-name AWSServiceRoleForBatch --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "batch.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}' --description "AWSServiceRoleForBatch" --max-session-duration 3600 --permissions-boundary "arn:aws:iam::aws:policy/aws-service-role/BatchServiceRolePolicy"
```

## GITHUB ACTION CONFIG

```sh
touch .github/workflows/publish-container.yaml
```

```yaml
# Name of the GitHub Actions workflow
name: Docker image for ECR

# Trigger this workflow on pushes to the 'prod' branch
on:
  push:
    branches:
      - prod

# Define permissions for the workflow
permissions:
  id-token: write  # Allow writing ID tokens
  contents: read   # Allow reading repository contents

# Define the jobs to be run in this workflow
jobs:
  build_and_publish:
    # Use the latest version of Ubuntu to run the job
    runs-on: ubuntu-latest
    steps:
      # Step to checkout the repository
      - name: Checkout Repo
        uses: actions/checkout@v4

      # Step to configure AWS credentials
      - name: Connect to AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-session-name: aws-push-ecr-session          # Name of the session for assuming the role
          role-to-assume: ${{ secrets.AWS_IAM_ROLE }}      # IAM role to assume, stored in GitHub secrets
          aws-region: ${{ secrets.AWS_REGION }}            # AWS region, stored in GitHub secrets

      # Step to login to Amazon ECR
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      # Step to build, tag, and push the Docker image to Amazon ECR
      - name: Build, tag, and push docker image to Amazon ECR
        env:
          REGISTRY: ${{ steps.login-ecr.outputs.registry }}        # ECR registry URL from the login step
          REPOSITORY: ${{ secrets.AWS_ECR_REPOSITORY }}            # ECR repository name, stored in GitHub secrets
          IMAGE_TAG: ${{ github.sha }}                             # Git commit SHA as the image tag
        run: |
          cd Docker                                                # Navigate to the Docker directory
          docker build -t $REGISTRY/$REPOSITORY:$IMAGE_TAG .       # Build the Docker image
          docker tag $REGISTRY/$REPOSITORY:$IMAGE_TAG $REGISTRY/$REPOSITORY:latest  # Tag the image as 'latest'
          docker push $REGISTRY/$REPOSITORY:$IMAGE_TAG             # Push the image with the commit SHA tag
          docker push $REGISTRY/$REPOSITORY:latest                 # Push the image with the 'latest' tag
```

> AWS_ECR_REPOSITORY with the ARN of the ECR Repo

> AWS_IAM_ROLE with the ARN of the role to assume

> AWS_REGION with the region (eg: us-east-1)