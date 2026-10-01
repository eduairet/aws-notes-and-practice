# Serverless Framework

- The Serverless Framework is an open-source framework that simplifies the deployment and management of serverless applications, including AWS Lambda functions. It provides a structured way to define your serverless application, manage dependencies, and deploy your code to the cloud.
- It automates the deployment process, allowing you to deploy your serverless applications with a single command.
- Infrastructure as code: You can define your serverless application, including functions, events, and resources, in a configuration file (serverless.yml), making it easy to version control and manage your infrastructure.
- It works with CloudFormation, allowing you to define and provision AWS resources alongside your Lambda functions.

## Installation

- Install the Serverless Framework globally using npm (Node Package Manager):
  ```bash
  npm install -g serverless
  ```
- Create a new IAM user in AWS:
  - Visit the AWS Management Console and navigate to the IAM service.
  - Create a new user with programmatic access.
  - Attach the necessary policies to the user, such as `AdministratorAccess` or specific policies for Lambda and API Gateway.
  - Save the access key ID and secret access key for the user, as you will need them to configure the Serverless Framework.

- Configure the Serverless Framework with your AWS credentials:
  ```bash
  serverless config credentials --provider aws --key <your-access-key-id> --secret <your-secret-access-key> --profile <your-profile-name>
  ```

## Deploying a function

- To deploy a function using the Serverless Framework, follow these steps:
  - Create a new Serverless service:

    ```bash
    serverless create --template aws-nodejs --path my-service
    cd my-service
    ```

    - Or go through the interactive setup:
      ```bash
      serverless
      ```

  - Edit the `serverless.yml` file to define your function, events, and resources.

    ```yaml
    service: my-service

    frameworkVersion: '3'

    provider:
      name: aws
      runtime: nodejs14.x
      region: us-east-1

    functions:
      hello:
        handler: handler.hello
    ```

  - Check the `handler.js` file with your Lambda function code:

    ```javascript
    module.exports.hello = async event => {
      return {
        statusCode: 200,
        body: JSON.stringify(
          {
            message: 'Hello, Serverless!',
          },
          null,
          2,
        ),
      };
    };
    ```

  - Deploy the service to AWS:

    ```bash
    serverless deploy function --function hello
    ```

- To invoke the function after deployment, use the following command:

  ```bash
  serverless invoke --function hello
  ```

  - You'll see the output of your Lambda function in the terminal like this:

    ```json
    {
      "statusCode": 200,
      "body": "{\"message\":\"Hello, Serverless!\"}"
    }
    ```

  - You can invoke the function with different event payloads, like `--log` to see the logs or `--data` to pass custom data to the function.

- You can verify all the lambda invocations and logs in the CloudWatch service in the AWS Management Console or by using the following command:

  ```bash
  serverless logs --function hello
  ```

- Cleaning up resources after testing is important to avoid unnecessary charges. You can remove the deployed service and its associated resources using the following command:

  ```bash
  serverless remove
  ```

## Creating AWS Lambda Functions Using any Runtime

- You can create the function using the CLI by running the `serverless create` command with the appropriate template for your desired runtime. For example, to create a Python service:

  ```bash
  serverless create --template aws-python3 --path my-python-service
  cd my-python-service
  ```

  - This will create a new Serverless service using the Python 3 template and navigate into the service directory.

- The directory tree will usually look like this:

  ```
  my-python-service/
  ├── handler.py
  ├── serverless.yml
  └── ...
  ```

- You can then edit the `serverless.yml` file to define your function, events, and resources, similar to the Node.js example.
  - Example `serverless.yml` for the Python service:

    ```yaml
    service: my-python-service

    frameworkVersion: '3'

    provider:
      name: aws
      runtime: python3.9
      region: us-east-1

    functions:
      hello:
        handler: handler.hello
    ```

- The `handler.py` file should contain your Lambda function code. For example:

  ```python
  def hello(event, context):
      return {
          "statusCode": 200,
          "body": "Hello, Serverless with Python!"
      }
  ```

- Example: Create a thumbnail generation Lambda function using Python and saving the thumbnail in S3.

  ```python
  from PIL import Image
  import io
  import boto3

  s3_client = boto3.client('s3')

  def generate_thumbnail(event, context):
      bucket = event['bucket']
      key = event['key']
      image_data = s3_client.get_object(Bucket=bucket, Key=key)['Body'].read()
      image = Image.open(io.BytesIO(image_data))
      image.thumbnail((128, 128))
      output = io.BytesIO()
      image.save(output, format='JPEG')
      output.seek(0)
      s3_client.put_object(Bucket=bucket, Key=f"thumbnails/{key}", Body=output)
      return {
          "statusCode": 200,
          "body": f"Thumbnail for {key} created successfully."
      }
  ```

  - In this example, the Lambda function `generate_thumbnail` retrieves an image from an S3 bucket, creates a thumbnail, and saves the thumbnail back to the S3 bucket under the `thumbnails/` prefix. This approach leverages AWS services for storage and processing, keeping the Lambda function stateless and focused on a single task.

## Timeouts and memory

- You can configure the timeout and memory for your Lambda function in the `serverless.yml` file under the function definition. For example:

  ```yaml
  functions:
    generate_thumbnail:
      handler: handler.generate_thumbnail
      timeout: 30 # Timeout in seconds
      memorySize: 512 # Memory in MB
  ```

  - In this example, the `generate_thumbnail` function is configured with a timeout of 30 seconds and 512 MB of memory. Adjust these values based on the expected workload and performance requirements of your Lambda function.

- You can also get the timeout and memory values from the Provider section in the `serverless.yml` file, which sets default values for all functions. For example:

  ```yaml
  provider:
    name: aws
    runtime: python3.9
    region: us-east-1
    timeout: 30 # Default timeout in seconds
    memorySize: 512 # Default memory in MB

  functions:
    generate_thumbnail:
      handler: handler.generate_thumbnail
      # Inherits timeout and memorySize from provider defaults
      # No need to specify timeout and memorySize here as it inherits from provider defaults
      # This function will use the default timeout and memorySize specified in the provider section
      # You can still override the defaults here if needed
      timeout: 60 # Override default timeout if needed
      memorySize: 1024 # Override default memory if needed
  ```

## IAM Permissions for Lambda Functions

- Lambda functions require appropriate IAM permissions to access AWS resources such as S3, DynamoDB, and SNS.
- You can define these permissions in the `serverless.yml` file under the `provider.iamRoleStatements` section. For example:

  ```yaml
  provider:
    name: aws
    runtime: python3.9
    region: us-east-1
    iamRoleStatements:
      - Effect: 'Allow'
        Action:
          - 's3:GetObject'
          - 's3:PutObject'
        Resource: 'arn:aws:s3:::your-bucket-name/*'
  ```

## Environment variables

- You can define environment variables for your Lambda functions in the `serverless.yml` file under the function definition or the provider section. For example:

  ```yaml
  provider:
    name: aws
    runtime: python3.9
    region: us-east-1
    environment:
      DEFAULT_BUCKET: your-bucket-name

  functions:
    generate_thumbnail:
      handler: handler.generate_thumbnail
      environment:
        THUMBNAIL_BUCKET: your-thumbnail-bucket
  ```

  - Environment variables can be defined at both the provider and function levels, allowing for flexible configuration of your Lambda functions.

## VPCs for Lambda Functions

- You can configure your Lambda functions to run within a VPC by specifying the VPC configuration in the `serverless.yml` file under the function definition. For example:

  ```yaml
  functions:
    generate_thumbnail:
      handler: handler.generate_thumbnail
      vpc:
        securityGroupIds:
          - sg-0123456789abcdef0
        subnetIds:
          - subnet-0123456789abcdef0
          - subnet-abcdef0123456789
  ```

  - Lambda functions running within a VPC require appropriate security group and subnet configurations to access resources securely.