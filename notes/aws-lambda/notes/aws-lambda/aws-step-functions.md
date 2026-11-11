# AWS Step Functions

Step functions allow you to build visual workflows for orchestrating AWS services and managing complex application logic.

## Advantages

- Build and deploy complex workflows with ease using the Workflow Studio to drag and drop steps visually.
- Express complex business logic as low-code, event-driven workflows without writing extensive code.
- Integrate seamlessly with other AWS services, enabling automation and orchestration across your cloud infrastructure.
- Scalable and reliable, allowing you to handle large volumes of tasks and events without worrying about infrastructure management.
- Provides built-in error handling, retry mechanisms, rollback capabilities, and state management, reducing the complexity of building resilient applications.

## State Types

Step Functions support several state types that define the behavior of each step in a workflow:

- **Pass:** Pushes input to output
- **Task:** Represents a single unit of work, such as invoking a Lambda function or performing an activity.
- **Choice:** Adds branching logic to the workflow based on conditions.
- **Parallel:** Allows multiple branches of execution to run concurrently.
- **Wait:** Introduces a delay before proceeding to the next state.
- **Fail:** Stops the execution and marks it as failed.
- **Succeed:** Stops the execution and marks it as successful.

## Pricing

AWS Step Functions pricing is based on the number of state transitions in your workflows. Each time a workflow moves from one state to another, it counts as a state transition. The cost is calculated per million state transitions, with additional charges for using certain features like Express Workflows.