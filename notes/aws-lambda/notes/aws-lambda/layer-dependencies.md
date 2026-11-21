# Layer Dependencies

AWS Lambda layers allow you to manage and share common dependencies across multiple Lambda functions. By using layers, you can keep your deployment package small and maintain a clean separation between your function code and its dependencies.

## Creating a Layer

1. Package your dependencies into a `.zip` file.
2. Go to the AWS Lambda console and navigate to the "Layers" section.
3. Click "Create layer" and provide a name, description, and upload the `.zip` file.
4. Specify the compatible runtimes for the layer.
5. Click "Create" to finalize the layer.

## Using a Layer in a Lambda Function

1. Open your Lambda function in the AWS Lambda console.
2. In the "Layers" section, click "Add a layer".
3. Choose "Custom layers" and select the layer you created.
4. Click "Add" to attach the layer to your function.

## Practice

- [Layer Dependencies exercise](../../../../practice/aws-lambda/exercises/02-layer-dependencies/README.md): a SAM layer with a shared module and a pip dependency.
