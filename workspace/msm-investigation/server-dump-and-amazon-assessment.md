# MSM historical server archive: 2012 SQL dump and Amazon cloud dependencies

Investigation date: November 3, 2026 (Eastern).

Archive: https://archive.org/details/monster-game-server
Verified original ZIP SHA-1: `df086c9ca4581733f73f2e8aaea1408382232e4d`.

## Why the word "dump" matters

The original ZIP contains `my_singing_monsters_clean_20120810.sql`. The evidence comes from reading the SQL file, not trusting its filename.

Static scan identified the following conventional MySQL dump structure:

- Header includes `MySQL dump`.
- Header includes a MySQL server version field: **5.5.20**.
- 30 table-structure sections and 30 table-data sections.
- A completion marker recording **2012-08-10 22:58:59** (no verifiable timezone).
- Header does **not** identify phpMyAdmin or Adminer.
- The file includes real schema and non-personal seed records (see `server-2012-game-seed.json`), not just empty table definitions.
- The SQL also defines user-related tables, but this research excludes their data and does not expose personal records.

MySQL's own documentation describes `mysqldump` as producing SQL-format backups: https://dev.mysql.com/doc/refman/26.7/en/mysqldump-sql-format.html

**Interpretation:** The SQL is strongly consistent with a preserved early MSM database export. It is not proof that this dump contains live production-player data; the word `clean` in the filename might indicate a cleaned seed or development database, and timestamps can be modified.

A database export with detailed breeding, monster, island and quest records is different from simple asset extraction. It provides stronger evidence of a server-side development materials collection, but the original author and sharing provenance remain unverified.

## Where Amazon is found

The original archive includes:

- `external/lib/aws-java-sdk-1.5.0.jar`
- `external/lib/elasticache-java-cluster-client-1.0.61.0.jar`
- Source classes `SqsWrapper`, `SnsWrapper`, `SNSWorker`, `CloudWatchReporter`, `EC2Metadata`, and `CacheWrapper`, plus references in other source files.

Safe static scan of first-party Java files found AWS-related usages categorized as:
- **SQS** messaging
- **SNS** notifications
- **CloudWatch** metrics
- **EC2** instance metadata
- **S3** cloud storage
- **ElastiCache/Memcached** caching

Importantly, searching the two SQL files found **zero literal occurrences** of `Amazon` or `AWS`. AWS is in the Java backend and its dependencies, not in the 2012 SQL dump.

The versions' published dates are independently documented:
- AWS SDK for Java 1.5.0: **July 8, 2013**. Source: https://mvnrepository.com/artifact/com.amazonaws/aws-java-sdk/1.5.0
- Amazon ElastiCache Cluster Client 1.0.61.0: **February 6, 2014**. Source: https://mvnrepository.com/artifact/com.amazonaws/elasticache-java-cluster-client/versions

The **complete source package thus cannot be an untouched August 2012 assembly**. It contains libraries introduced after that date. This does not disprove that the SQL export itself originated in 2012; it suggests the archive combines older data and newer backend code/dependencies.

## Interpretation and limits

Evidence supports multiple historical layers:

1. An internally timestamped SQL dump from August 2012.
2. Cloud/dependency components published in 2013–2014 or later.
3. ZIP file member timestamps in July 2020 and ZIP directory timestamps in May 2021.
4. Internet Archive publication October 2023.

This is consistent with a developer maintaining an old seed database through later backend versions, but the exact chain of custody remains unknown. Neither the original Git host nor the identity of the party who first published the source has been proven.

The Amazon dependencies do not imply Amazon authored the game or uploaded the source. They simply show AWS infrastructure integration.

## Reproducibility

- Non-executing scanner: `server_dump_aws_evidence.py`
- Machine-readable, non-sensitive results: `server-dump-aws-evidence.json`
- Related archive file inventories: `server-full-file-index.csv`, `server-full-file-audit.json`
- Original 2012 seed analysis: `server-2012-game-seed.json`

No archived source bodies, ZIP/JARs, live endpoints, credentials or personal player records were republished in this report.
