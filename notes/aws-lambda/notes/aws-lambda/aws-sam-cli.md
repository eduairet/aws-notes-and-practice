# AWS SAM CLI

AWS SAM CLI (Serverless Application Model Command Line Interface) is a tool that helps you develop, test, and deploy serverless applications defined using AWS SAM templates. It simplifies the process of building and managing serverless applications on AWS.

## Key Features

- **Local Development and Testing**: You can run your serverless applications locally using the SAM CLI, which emulates the AWS Lambda execution environment.
- **Build and Package**: SAM CLI helps you build and package your serverless applications, preparing them for deployment to AWS.
- **Deployment**: You can deploy your serverless applications to AWS with a single command, managing the underlying resources defined in your SAM template.
- **Debugging**: SAM CLI supports local debugging of Lambda functions, making it easier to troubleshoot issues during development.
- **Integration with CI/CD**: SAM CLI can be integrated into continuous integration and continuous deployment pipelines to automate the deployment of serverless applications.

## Requirements

- VS Code (Visual Studio Code) with the AWS Toolkit extension installed.
- AWS credentials to connect to your AWS account.
- AWS CLI installed on your local machine.
  - [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
  - Verify the AWS CLI installation by running `aws --version` in your terminal.
  - Ensure that your AWS CLI is properly configured using `aws sts get-caller-identity`.
  - If the AWS CLI is not properly configured, run `aws configure` to set up your AWS credentials and default region.
- Docker installed on your local machine if you want to test Lambda functions that require a containerized environment.
- AWS SAM CLI installed on your local machine - It's like serverless framework but specifically for AWS SAM templates.
  - [AWS SAM CLI Installation Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html)
  - Verify the AWS SAM CLI installation by running `sam --version` in your terminal.
