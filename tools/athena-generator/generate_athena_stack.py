#!/usr/bin/env python3
"""
이 스크립트는 단일 CSV 파일에서 데이터베이스, 테이블, 컬럼 정보를 읽어 athena-stack.ts 파일을 자동으로 생성합니다.
"""

import csv
import os
import sys
from collections import defaultdict

def read_csv(file_path):
    """CSV 파일을 읽어 딕셔너리 리스트로 반환합니다."""
    if not os.path.exists(file_path):
        print(f"오류: {file_path} 파일이 존재하지 않습니다.")
        sys.exit(1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def to_pascal_case(text):
    """스네이크 케이스를 파스칼 케이스로 변환합니다."""
    components = text.split('_')
    return ''.join(x.title() for x in components)

def generate_athena_stack(data):
    """athena-stack.ts 파일 내용을 생성합니다."""
    # 데이터 분류
    databases = []
    tables = defaultdict(list)
    columns = defaultdict(list)
    
    for row in data:
        row_type = row['type']
        db_name = row['database_name']
        
        if row_type == 'database' and db_name not in databases:
            databases.append(db_name)
        elif row_type == 'table':
            table_name = row['table_name']
            if table_name not in tables[db_name]:
                tables[db_name].append(table_name)
        elif row_type == 'column':
            table_name = row['table_name']
            columns[f"{db_name}.{table_name}"].append({
                'name': row['column_name'],
                'type': row['column_type'],
                'comment': row['column_comment']
            })
    
    # 코드 생성 시작
    code = """/*
* Copyright Amazon.com and its affiliates; all rights reserved.
* SPDX-License-Identifier: LicenseRef-.amazon.com.-AmznSL-1.0
* Licensed under the Amazon Software License  https://aws.amazon.com/asl/
*/

import * as path from "path";
import { Stack, StackProps, RemovalPolicy, CfnOutput } from "aws-cdk-lib";
import * as glue from "aws-cdk-lib/aws-glue";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import { Construct } from "constructs";

interface AthenaStackProps extends StackProps {
  ACCESS_LOG_BUCKET: s3.Bucket;
}

export class AthenaStack extends Stack {
  public readonly ATHENA_OUTPUT_BUCKET: s3.Bucket;
  public readonly ATHENA_DATA_BUCKET: s3.Bucket;
"""

    # 데이터베이스 변수 선언
    for i, db_name in enumerate(databases):
        db_var_name = f"{db_name.upper().replace('_', '_')}_DATABASE"
        code += f"  public readonly {db_var_name}: glue.CfnDatabase;\n"

    code += """
  constructor(scope: Construct, id: string, props: AthenaStackProps) {
    super(scope, id, props);

    // Create S3 buckets for Athena
    this.ATHENA_DATA_BUCKET = new s3.Bucket(this, "AthenaDataBucket", {
      bucketName: `sl-data-store-${this.account}-${this.region}`,
      enforceSSL: true,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      serverAccessLogsBucket: props.ACCESS_LOG_BUCKET,
      serverAccessLogsPrefix: "athena-data-bucket-logs/",
    });

    this.ATHENA_OUTPUT_BUCKET = new s3.Bucket(this, "AthenaOutputBucket", {
      bucketName: `sl-athena-output-${this.account}-${this.region}`,
      enforceSSL: true,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      serverAccessLogsBucket: props.ACCESS_LOG_BUCKET,
      serverAccessLogsPrefix: "athena-output-bucket-logs/",
    });
"""

    # 테이블별 CSV 파일 업로드 코드 생성
    for db_name in tables:
        for table_name in tables[db_name]:
            table_pascal = to_pascal_case(table_name)
            deploy_id = f"Deploy{table_pascal}SampleTable"
            code += f"""
    // Upload a sample csv file for {table_name} table
    new s3deploy.BucketDeployment(this, "{deploy_id}", {{
      sources: [
        s3deploy.Source.asset(path.join(__dirname, "..", "..", "assets", "{db_name}", "{table_name}")),
      ],
      destinationBucket: this.ATHENA_DATA_BUCKET,
      destinationKeyPrefix: "{db_name}/{table_name}",
    }});
"""

    # 데이터베이스 생성 코드
    for i, db_name in enumerate(databases):
        db_var_name = f"{db_name.upper().replace('_', '_')}_DATABASE"
        db_id = f"{to_pascal_case(db_name)}Database"
        
        code += f"""
    // Create Athena Database
    this.{db_var_name} = new glue.CfnDatabase(this, "{db_id}", {{
      catalogId: this.account,
      databaseInput: {{
        name: "{db_name}",
      }},
    }});
"""

    # 테이블 생성 코드
    for db_name in tables:
        for table_name in tables[db_name]:
            # 테이블의 컬럼 정보 가져오기
            key = f"{db_name}.{table_name}"
            table_cols = columns.get(key, [])
            
            # 테이블 ID 생성 (파스칼 케이스)
            table_pascal = to_pascal_case(table_name)
            table_id = f"{table_pascal}Table"
            
            code += f"""
    new glue.CfnTable(this, "{table_id}", {{
      catalogId: this.account,
      databaseName: "{db_name}",
      tableInput: {{
        name: "{table_name}",
        storageDescriptor: {{
          columns: [
"""
            
            # 컬럼 정보 추가
            for i, col in enumerate(table_cols):
                col_name = col['name']
                col_type = col['type']
                col_comment = col['comment']
                
                code += f"""            {{
              name: "{col_name}",
              type: "{col_type}",
              comment: "{col_comment}",
            }}"""
                
                # 마지막 컬럼이 아니면 쉼표 추가
                if i < len(table_cols) - 1:
                    code += ","
                
                code += "\n"
            
            code += f"""          ],
          location: `s3://${{this.ATHENA_DATA_BUCKET.bucketName}}/{db_name}/{table_name}`,
          inputFormat: "org.apache.hadoop.mapred.TextInputFormat",
          outputFormat: "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
          serdeInfo: {{
            serializationLibrary: "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
            parameters: {{
              "field.delim": ",",
              "line.delim": "\\n",
            }},
          }},
        }},
        tableType: "EXTERNAL_TABLE",
        parameters: {{
          "skip.header.line.count": "1",
        }},
      }},
    }});
"""

    # 출력 코드
    code += """
    // Outputs
    new CfnOutput(this, "AthenaDataBucketName", {
      value: this.ATHENA_DATA_BUCKET.bucketName,
      description: "Athena Data Bucket Name",
    });

    new CfnOutput(this, "AthenaOutputBucketName", {
      value: this.ATHENA_OUTPUT_BUCKET.bucketName,
      description: "Athena Output Bucket Name",
    });
"""

    # 첫 번째 데이터베이스에 대한 출력 추가
    if databases:
        first_db = databases[0]
        first_db_var = f"{first_db.upper().replace('_', '_')}_DATABASE"
        first_db_pascal = to_pascal_case(first_db)
        code += f"""
    new CfnOutput(this, "{first_db_pascal}DatabaseName", {{
      value: this.{first_db_var}.ref,
      description: "{first_db_pascal} Database Name",
    }});
"""

    code += """  }
}
"""
    
    return code

def main():
    """메인 함수"""
    # CSV 파일 경로
    template_csv = "athena_template.csv"
    
    # CSV 파일 읽기
    data = read_csv(template_csv)
    
    # athena-stack.ts 파일 생성
    code = generate_athena_stack(data)
    
    # 파일 저장
    output_path = "athena-stack.ts"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"athena-stack.ts 파일이 성공적으로 생성되었습니다.")

if __name__ == "__main__":
    main()