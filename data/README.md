# Data Tier

The data tier is implemented using Amazon RDS MySQL.

This directory stores the version-controlled database assets used by the JNS Task Management Platform.

## Structure

- `schema/` - database schema and index scripts
- `procedures/` - MySQL stored procedures
- `seed/` - lookup and initial data scripts

The live database is hosted in AWS RDS in the ap-southeast-6 (New Zealand) region.
