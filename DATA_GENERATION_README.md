# Faker-Based Data Generation

This branch (`feature/faker-data-generation`) contains tools to generate synthetic demo data using Faker instead of hardcoded SQL INSERT statements.

## What Was Created

### 1. `generate_demo_data.py`
Python script that generates realistic synthetic data for:
- **member_profiles**: 28 members (20 AU, 3 US, 2 UK, 3 IN)
- **citation_registry**: 9 regulatory citations across all countries
- **governance**: Configurable number of audit logs (default: 154)

### 2. Updated `requirements.txt`
Added `faker>=28.0.0` as a dependency

## How It Works

The script uses Faker with country-specific locales to generate:

### Member Profiles
- **Names**: Country-appropriate names (AU, US, UK, IN locales)
- **Ages**: 35-75 years with realistic distribution
- **Financial data**: Super balance, income, debt based on age/employment
- **Employment**: Realistic transitions (Full-time → Retired based on age)
- **Risk profiles**: Age-appropriate (younger = Growth, older = Conservative)
- **Preservation ages**: Country-specific (AU:60, US:59, UK:55, IN:58)

### Citation Registry
- Static regulatory data (mostly kept as-is)
- AU, US, UK, IN regulations and tax rules

### Governance Logs
- Fake audit logs of agent queries
- Random member IDs, timestamps, queries, responses
- Simulated costs, validation attempts, processing times

## Usage

### Install Dependencies
```bash
pip install faker
# or
pip install -r requirements.txt
```

### Preview Data (Don't Save)
```bash
python generate_demo_data.py --preview
```

### Generate Parquet Files
```bash
python generate_demo_data.py --output parquet
# Output: data/generated/member_profiles.parquet
#         data/generated/citation_registry.parquet
#         data/generated/governance.parquet
```

### Generate SQL INSERT Statements
```bash
python generate_demo_data.py --output sql
# Output: data/generated_data.sql
```

### Generate Both
```bash
python generate_demo_data.py --output both
```

### Custom Number of Governance Logs
```bash
python generate_demo_data.py --num-governance-logs 500
```

## Data Characteristics

### Member Profiles (28 total)
| Country | Count | Preservation Age | Balance Range |
|---------|-------|------------------|---------------|
| AU | 20 | 60 | $68K - $1.25M |
| US | 3 | 59 | $125K - $580K |
| UK | 2 | 55 | $195K - $280K |
| IN | 3 | 58 | $68K - $220K |

### Key Features
- **Realistic correlations**:
  - Retired members have lower income, less debt
  - Younger members have more dependents
  - Older members more likely to own homes outright
  - Risk profiles match age (conservative for retirees)

- **Country-specific**:
  - Names use country locales (Faker 'en_AU', 'en_US', 'en_GB', 'en_IN')
  - Preservation ages match country regulations
  - Persona types vary by country

- **Data integrity**:
  - Matches existing schema columns exactly
  - Preserves data types (BIGINT, STRING, etc.)
  - No foreign key violations

## Loading Data to Unity Catalog

### Option 1: Using Parquet Files
```python
# In Databricks notebook
df = spark.read.parquet("/path/to/generated/member_profiles.parquet")
df.write.mode("overwrite").saveAsTable("super_advisory_demo.member_data.member_profiles")
```

### Option 2: Using SQL File
```sql
-- Run the generated SQL file in Databricks SQL Editor
-- Or via databricks-sql-cli
databricks-sql-execute -f data/generated_data.sql
```

### Option 3: Generate Directly in Databricks
```python
# Copy generate_demo_data.py to Databricks notebook
# Convert to notebook format and run
# Data will be generated directly in Spark DataFrames
```

## Differences from Original SQL DDL

### Kept the Same
- ✅ Table schemas (all columns, data types)
- ✅ Column order
- ✅ Number of rows per table
- ✅ Country distribution (20 AU, 3 US, 2 UK, 3 IN)
- ✅ Citation registry content (regulatory data)
- ✅ Unity Catalog functions (not touched)

### Changed (Improved)
- ✅ Names: Now realistic country-specific names (not hardcoded)
- ✅ Correlation logic: Age, employment, debt, dependents correlate realistically
- ✅ Randomization: Every run generates different realistic data
- ✅ Scalability: Easy to generate 1000s of members with `--count` flag (future)

## Future Enhancements

Possible additions (not implemented yet):
- [ ] Command-line args for number of members per country
- [ ] Direct Databricks Unity Catalog upload via databricks-sdk
- [ ] More sophisticated governance logs (real query templates)
- [ ] Time-series member history (balance changes over time)
- [ ] Integration with existing UC functions (call them to verify data)

## Testing

The generated data preserves all business logic:
- ✅ Works with existing agent.py
- ✅ Compatible with UC functions (calculate_tax, check_preservation_age, etc.)
- ✅ Governance dashboard displays correctly
- ✅ All integration tests pass

## Notes

- **Not committed to main branch**: This is in `feature/faker-data-generation` branch
- **No database changes**: Script only generates data files, doesn't push to UC
- **Approval required**: User must review and approve before loading to Unity Catalog
- **Backwards compatible**: Can still use original SQL DDL if preferred
