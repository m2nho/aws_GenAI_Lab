# PACE Generative AI Developer Workshop

This workshop provides a CDK scaffolding for rapid prototyping of AI-powered applications using Amazon Bedrock Knowledge Bases and Agents.

The full-stack template includes pre-built infrastructure, sample implementations, and customizable components that you can use to quickly build and validate your own AI solutions.


### Development Environment

| Tool              | Version  | Installation Guide                                                                                                    | Note                                                                                         |
|-------------------|----------|-----------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| AWS CLI           | Latest   | [Download](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)                             |                                                                                              |
| AWS CDK           | Latest   | [Github](https://github.com/aws/aws-cdk?tab=readme-ov-file#at-a-glance)                                               |                                                                                              |
| Docker            | -        | [Download](https://www.docker.com/products/docker-desktop/)                                                           | Alternative: [Rancher Desktop](https://docs.rancherdesktop.io/getting-started/installation/) |
| Node.js           | ≥20.18.1 | [Download](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)                                         |                                                                                              |
| PNPM              | 9.15.0   | [Download](https://pnpm.io/)                                                                                          | Package Manager                                                                              |
| Python            | ≥3.12    | [Download](https://www.python.org/downloads/)                                                                         | For OpenAPI schema                                                                           |
| GraphViz          | -        | [Download](https://graphviz.org/download/)                                                                            | For CDK diagrams                                                                             |
| API Testing Tools | -        | Any REST API testing tool such as [Postman](https://www.postman.com/downloads/) or [Bruno](https://www.usebruno.com/) | For API test                                                                                 |


## Getting Started

```bash
pnpm install
```

Then

```bash
pnpm docs:init
```

Open http://localhost:4321 and follow the Getting Started Guide.