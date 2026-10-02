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

## Benefits

- **Simplified Local Development**: Developers can test and debug serverless applications locally, reducing the need for frequent deployments to AWS.
- **Streamlined Deployment**: SAM CLI automates the packaging and deployment process, making it easier to manage serverless applications.
- **Consistent Environment**: By emulating the AWS Lambda environment locally, SAM CLI ensures that applications behave consistently between local development and production.
- **CI/CD Integration**: SAM CLI can be integrated into CI/CD pipelines, enabling automated testing and deployment of serverless applications.
- **Resource Management**: SAM CLI manages the underlying AWS resources defined in the SAM template, reducing the complexity of manual resource management.

## Creating and Running SAM Applications

To create and run a serverless application using the AWS SAM CLI, follow these steps:

1. **Initialize a New SAM Application**:

   ```bash
   sam init
   ```

   Follow the prompts to choose a template, runtime, and project name for example:

   ```bash
   sam init --runtime python3.13 --name hello-world-lambda
   ```

   - Or use the interactive prompts provided by `sam init` to select the runtime, template, and project name:

   ```bash
   sam init

   # Follow the interactive prompts to configure your SAM application:
   # - Template source: 1 – AWS Quick Start Templates
   # - Template: 1 – Hello World Example
   # - Use the most popular runtime and package type? (python3.x and zip): N. Then pick python3.13 so it matches your local Python, which sam build needs.
   # - Package type: Zip
   # - X-Ray tracing / CloudWatch Application Insights / JSON structured logging: N for all three. They add cost or complexity you don't need yet.
   # - Project name: hello-world
   ```

2. **Build the Application**:

   ```bash
   sam build
   ```

   This command processes your SAM template and prepares your application for deployment.

3. **Run the Application Locally**:

   ```bash
   sam local invoke
   ```

   This command invokes your Lambda function locally using the event defined in the `events` folder of your SAM application.
   - You can choose the function and event explicitly with `sam local invoke <your-lambda-function-name> -e <event-file.json>`, where `<event-file.json>` is a JSON file containing the event data to pass to your Lambda function.
   - To test through HTTP instead, start a local API Gateway:

     ```bash
     sam local start-api
     ```

     This lets you send HTTP requests to the local endpoint (e.g. `http://127.0.0.1:3000/hello`). If you make changes to your Lambda function code, stop `sam local start-api`, run `sam build` again and restart it to see the changes.

   - Everything in this step runs on your machine (in Docker), nothing is deployed to AWS.

4. **Deploy the Application to AWS**:

   ```bash
   sam deploy --guided --profile <your-aws-profile>
   ```

   Follow the prompts to configure your deployment settings and deploy your application to AWS.

5. **Test the Deployed Application**:

   After deploying, get the API URL from the stack outputs (`HelloWorldApi`) and call it:

   ```bash
   sam list stack-outputs --stack-name <your-stack-name>
   curl https://<api-id>.execute-api.<region>.amazonaws.com/Prod/hello/
   ```

   Or invoke the function in AWS directly, without going through API Gateway:

   ```bash
   sam remote invoke <your-lambda-function-name> --stack-name <your-stack-name>
   ```

6. **Verify the Deployment**:
   ```bash
   sam list resources
   ```
   This command lists the AWS resources created by your SAM application, allowing you to verify that the deployment was successful.

## Cleaning Up

To delete the resources created by your SAM application and avoid incurring charges, run the following command:

```bash
sam delete
```

Follow the prompts to confirm the deletion of your application and its associated resources.

Or you can delete just the stack with:

```bash
aws cloudformation delete-stack --stack-name <your-stack-name> --profile <your-aws-profile>
aws cloudformation wait stack-delete-complete --stack-name <your-stack-name> --profile <your-aws-profile> # optional, waits until it finishes
```

### `sam delete` vs `aws cloudformation delete-stack`

`sam delete` is a wrapper around `delete-stack` that also cleans up the files SAM uploaded:

|                                                                                     | `aws cloudformation delete-stack`              | `sam delete`                   |
| ----------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------ |
| Deletes the stack (function, role, API…)                                            | ✅                                             | ✅                             |
| Deletes your uploaded code and template in SAM's S3 bucket (`<stack-name>/` folder) | ❌ They stay and cost a tiny amount of storage | ✅ After asking you to confirm |
| Reads stack name, profile and region from `samconfig.toml`                          | ❌ You pass them yourself                      | ✅                             |
| Waits until the deletion finishes                                                   | ❌ Returns immediately                         | ✅                             |
| Asks for confirmation                                                               | ❌                                             | ✅                             |

What **neither** command deletes:

- **SAM's shared bucket stack, `aws-sam-cli-managed-default`.** This is intentional: every SAM project in the region reuses it. An empty S3 bucket costs nothing.
- **The function's CloudWatch log group, `/aws/lambda/<stack-name>-<FunctionName>-…`.** Lambda creates it the first time the function runs, so it isn't part of the stack. Remove it manually if you want:

  ```bash
  aws logs describe-log-groups --log-group-name-prefix /aws/lambda/<stack-name> --query "logGroups[].logGroupName"
  aws logs delete-log-group --log-group-name <name-from-above>
  ```

For SAM projects, `sam delete` is the better choice. `delete-stack` is still worth knowing because it works for any CloudFormation stack, including ones not created with SAM.
