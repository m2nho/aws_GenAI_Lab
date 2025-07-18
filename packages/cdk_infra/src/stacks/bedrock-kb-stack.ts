/*
* Copyright Amazon.com and its affiliates; all rights reserved.
* SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
* Licensed under the Amazon Software License  https://aws.amazon.com/asl/
*/

import * as path from "path";
import { bedrock } from "@cdklabs/generative-ai-cdk-constructs";
import { Stack, StackProps, RemovalPolicy, Duration } from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import { Construct } from "constructs";
import { ParserStrategyUtil } from "../utils/parser-strategy-util";

interface BedrockKnowledgeBaseStackProps extends StackProps {
  ACCESS_LOG_BUCKET: s3.Bucket;
}

export class BedrockKnowledgeBaseStack extends Stack {
  public readonly AGENT_KB: bedrock.IKnowledgeBase;

  constructor(
    scope: Construct,
    id: string,
    props: BedrockKnowledgeBaseStackProps,
  ) {
    super(scope, id, props);

    const agentKnowledgeBaseDataBucket = new s3.Bucket(
      this,
      "AgentKnowledgeBaseDataBucket",
      {
        enforceSSL: true,
        versioned: true,
        publicReadAccess: false,
        blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
        encryption: s3.BucketEncryption.S3_MANAGED,
        removalPolicy: RemovalPolicy.DESTROY,
        autoDeleteObjects: true,
        serverAccessLogsBucket: props.ACCESS_LOG_BUCKET,
        serverAccessLogsPrefix: "AgentKnowledgeBaseDataBucketLogs/",
        lifecycleRules: [
          {
            id: "ArchiveOldVersions",
            enabled: true,
            noncurrentVersionTransitions: [
              {
                storageClass: s3.StorageClass.GLACIER,
                transitionAfter: Duration.days(30),
              },
            ],
            noncurrentVersionExpiration: Duration.days(90),
          },
        ],
      },
    );

    // Upload sample PDF and metadata file
    new s3deploy.BucketDeployment(this, "DeployProductsSampleTable", {
      sources: [
        s3deploy.Source.asset(
          path.join(__dirname, "..", "assets", "knowledgebase"),
        ),
      ],
      destinationBucket: agentKnowledgeBaseDataBucket,
    });

    // * Amazon Bedrock
    this.AGENT_KB = new bedrock.VectorKnowledgeBase(this, "AgentKnowledgeBase", {
      embeddingsModel: bedrock.BedrockFoundationModel.TITAN_EMBED_TEXT_V2_1024,
      instruction:
        "Use this knowledge base for answering general questions related to the company name services and offerings " +
        "It contains text of FAQ documents like how to change password, how to cancel subscription.",
    });

    const parserStrategyCode = this.node.tryGetContext("parser:strategy");
    let parsingStrategy: bedrock.ParsingStategy | undefined;
    
    if (parserStrategyCode && ParserStrategyUtil.isValid(parserStrategyCode)) {
      parsingStrategy = ParserStrategyUtil.createStrategy(parserStrategyCode);
    }

    new bedrock.S3DataSource(this, "S3DataSource", {
      bucket: agentKnowledgeBaseDataBucket,
      knowledgeBase: this.AGENT_KB,
      chunkingStrategy: bedrock.ChunkingStrategy.fixedSize({
        maxTokens: 500,
        overlapPercentage: 20,
      }),
      dataSourceName: "AgentKnowledgeBaseDataSource",
      ...(parsingStrategy && { parsingStrategy }),
    });
  }
}
