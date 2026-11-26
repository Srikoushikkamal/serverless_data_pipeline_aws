# Serverless Data Pipeline on AWS

My MSc dissertation project (Big Data Management & Analytics, Griffith College, 2026).

An event-driven pipeline that takes raw files from the Olist Brazilian e-commerce dataset, dropped into S3, and
turns them into tables ready for querying, with no manual steps.

## How it works

```mermaid
flowchart LR
    A[Raw files land in S3] --> B[EventBridge sees the new file]
    B --> C[Lambda starts the Glue job]
    C --> D[Glue job cleans the data, PySpark]
    D --> H[Glue Crawler updates the Data Catalog]
    H --> E[Query-ready Parquet tables in S3]
    E --> F[Athena: SQL on the results]
    C -. logs .-> G[CloudWatch]
    D -. logs .-> G
```

1. **S3** holds the raw files and the cleaned output.
2. **EventBridge** reacts as soon as a new file arrives.
3. **Lambda** checks the event and starts the Glue job.
4. **Glue** (PySpark) cleans the data, removes duplicates and writes Parquet tables; a **Glue Crawler** registers
   them in the Data Catalog.
5. **Athena** runs SQL on the result.
6. **IAM** roles give each service only the access it needs.
7. **CloudWatch** logs were where I traced failures back to the cause.

## Result

The output was checked against the source before calling it done: **75,310 orders across 7 tables, with no
duplicates.**

## Status

The code, setup and Athena queries are being added to this repository.
