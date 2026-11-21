# Step Functions

Practice for the [AWS Step Functions](../../../../notes/aws-lambda/notes/aws-lambda/aws-step-functions.md) note. It's an order workflow built around the note's Task state example.

```
ValidateOrder (Task → Lambda) ──Catch States.ALL──▶ ErrorHandler (Fail: TaskFailed)
        │
        ▼
NeedsReview? (Choice: total > 100)
   ├── yes ▶ ManualReview (Pass) ▶ end
   └── no  ▶ AutoApprove  (Pass) ▶ end
```

- The definition (ASL) is in [`template.yaml`](order-workflow/template.yaml), as the `DefinitionString` of a plain `AWS::StepFunctions::StateMachine`. `!Sub` fills in `${ValidateOrderFunction.Arn}`.
  - With SAM's `AWS::Serverless::StateMachine` you'd usually keep the ASL in its own file (`DefinitionUri`) and fill in ARNs with `DefinitionSubstitutions`. The AWS Emulator doesn't support those ([emulator gaps](../../../../notes/aws-emulator/notes/aws-emulator/docker-setup.md#testing-the-practice-projects)). The plain resource with `!Sub` works the same on the emulator and on real AWS.
- **Retry** lists only Lambda's transient errors (`Lambda.ServiceException`, `Lambda.AWSLambdaException`, `Lambda.SdkClientException`, `Lambda.TooManyRequestsException`). An invalid order raises `InvalidOrderError`. Retrying it would fail the same way, so it goes straight to **Catch**.
- **Catch** uses `ResultPath: "$.error"`, so `ErrorHandler` still sees the original order plus the error.
- The **Pass** states write the decision into the state (`ResultPath: "$.decision"`) instead of replacing it.
- **Permissions**: Step Functions assumes `OrderStateMachineRole` (trusted principal `states.amazonaws.com`), which allows `lambda:InvokeFunction` on this one function. Without that permission every run fails with `Lambda.AWSLambdaException ... not authorized`, on real AWS and on the emulator alike.

## Run It

```bash
cd order-workflow
sam build
sam deploy --guided                                  # real AWS
aws stepfunctions start-execution --state-machine-arn <OrderStateMachine output> \
  --input file://events/small-order.json
```

Or run it against the local emulator, with the other practice projects: `docker compose run --rm practice-tests` from the repo root.

## Tests

- `tests/unit`: the Lambda handler, plus checks on the definition in the template: every `Next`, `Default` and `Catch` target exists, and business errors aren't retried.
- `tests/integration`: runs real executions for an auto-approved order, an order that needs review, and an invalid order. The invalid order must end in `ErrorHandler` without any retries.
