# aws-ebs-volume-optimization
Automated EBS gp2 to gp3 conversion using AWS Lambda, Step Functions, and EventBridge
## Step Function
- State machine triggers the Lambda function
- Used for orchestration and future extensibility
- Defined using Amazon States Language (ASL)
## Architecture Diagram
See `diagrams/architecture.png`
