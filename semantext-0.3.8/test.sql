WITH "5e1447eb-7348-4178-bcbf-6561ce3d4406" AS (
  SELECT DISTINCT
    "datalake"."remix"."dim_snif"."snif_id" AS "snif_id",
    "datalake"."remix"."dim_snif"."snif_name" AS "snif_name",
    "datalake"."remix"."dim_snif"."ir" AS "ir"
  FROM "datalake"."remix"."dim_snif"
  WHERE
    "datalake"."remix"."dim_snif"."ir" = CAST('Jerusalem' AS VARCHAR)
), "c23c0a27-7bcb-4b5d-8256-17f12001cfbc" AS (
  SELECT
    AVG("datalake"."remix"."sales_fact"."amount") AS "sales_fact_amount",
    SUM("datalake"."remix"."sales_fact"."price") AS "sales_fact_price",
    "5e1447eb-7348-4178-bcbf-6561ce3d4406"."snif_id" AS "snif_id"
  FROM "datalake"."remix"."sales_fact"
  INNER JOIN "5e1447eb-7348-4178-bcbf-6561ce3d4406"
    ON "5e1447eb-7348-4178-bcbf-6561ce3d4406"."snif_id" = "datalake"."remix"."sales_fact"."snif_id"
  WHERE
    "datalake"."remix"."sales_fact"."taarich" = CAST('2023-01-01' AS TIMESTAMP)
  GROUP BY
    "5e1447eb-7348-4178-bcbf-6561ce3d4406"."snif_id"
), "4e514936-2c3c-4e00-a7f8-1e2c1c64a98d" AS (
  SELECT
    AVG("datalake"."remix"."shalom_fact"."amount") AS "shalom_fact_amount",
    "5e1447eb-7348-4178-bcbf-6561ce3d4406"."ir" AS "ir"
  FROM "datalake"."remix"."shalom_fact"
  INNER JOIN "5e1447eb-7348-4178-bcbf-6561ce3d4406"
    ON "5e1447eb-7348-4178-bcbf-6561ce3d4406"."ir" = "datalake"."remix"."shalom_fact"."ir"
  GROUP BY
    "5e1447eb-7348-4178-bcbf-6561ce3d4406"."ir"
)
SELECT
  "5e1447eb-7348-4178-bcbf-6561ce3d4406"."snif_id" AS "snif_id",
  "5e1447eb-7348-4178-bcbf-6561ce3d4406"."snif_name" AS "snif_name",
  "c23c0a27-7bcb-4b5d-8256-17f12001cfbc"."sales_fact_amount",
  "c23c0a27-7bcb-4b5d-8256-17f12001cfbc"."sales_fact_price",
  "4e514936-2c3c-4e00-a7f8-1e2c1c64a98d"."shalom_fact_amount"
FROM "5e1447eb-7348-4178-bcbf-6561ce3d4406"
LEFT JOIN "c23c0a27-7bcb-4b5d-8256-17f12001cfbc"
  ON "c23c0a27-7bcb-4b5d-8256-17f12001cfbc"."snif_id" = "5e1447eb-7348-4178-bcbf-6561ce3d4406"."snif_id"
LEFT JOIN "4e514936-2c3c-4e00-a7f8-1e2c1c64a98d"
  ON "4e514936-2c3c-4e00-a7f8-1e2c1c64a98d"."ir" = "5e1447eb-7348-4178-bcbf-6561ce3d4406"."ir"