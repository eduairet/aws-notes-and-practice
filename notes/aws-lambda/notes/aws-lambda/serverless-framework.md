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
