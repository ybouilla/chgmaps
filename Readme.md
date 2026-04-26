
# Exercise Chargemaps

## 📦  Project Overview

This project simulates a full data lifecycle pipeline:

- Synthetic data generation (license subscriptions)
- Data validation
- Data transformation (Python + SQL)
- Storage in SQLite database
- Incremental pipeline processing
- Full Docker-based orchestration
- Automated testing suite (pytest)


## 0. Installation 

**Requirements**:
- Linux OS 
- Windows with WSL2 (Windows Subsystem Linux) activated
- Docker

### Using uv as a package manager
*Nota*: [uv](https://github.com/astral-sh/uv) has been selected here for its known efficiency. Other python package manager should be working but have not been tested.

First install uv. Then you can install requirements by running:
**On Linux**:
```
source .venv/bin/activate
uv pip install -r requirements.txt
```

Run the following script: 
```shell
uv run python -m app.main_data_generation
```
Use `uv run python -m app.main_data_generation --help` for more details.

## 1. Data Generation
## Parameters
Parameters are defined in the script `main_data_generation.py`

### a. Number of Licenses

Since the license ids range from 1 to 100, there are a maximum of 100 licenses.
For customer ids, there should be less customers than the number of licenses available. 

### b. Number of licenses per clients
As asked, a paretto distribution is used to model number of licenses per clients. `alpha` has been selected in a way the majority of clients have one or 2 licenses, but a few of them hold way more licenses.

### c. Creation date

To generate creation date; we used a probability to create a date belonging to first quarter of the year. Also we include the fact the date doesnot appear on a weekend (assuming its mainly companies which subscribe).

### d. Changes in the licenses.

To simulate the fact most clients don't change their subscriptions, but only a small portion do, i used a Paretto like distribution, to selectt which clients will have a lot of modifications.
It has been asked to generate over than 10,000 modifications. 

### e. **Relationship between type and prices:**

Since we have 3 kinds of type (SIM, PASS, SUPERVISION), for simplification sake I proposed to map for each type a price:
 - PASS: 100
 - SIM: 1000
 - SUPERVISION: 5000

###  f.type modelling

I used a Markov Chain to represent the transition dynamics. I defined a 6-state system represented by a single 6×6 transition matrix, where each row defines the probabilities of transitioning between states.

🧩 Conceptual model

This system behaves like:

* A 3-state operational process (core system)
* Embedded in a 6-state Markov chain
With transient “renewal” events acting as instant switches


### g. Renewable:
💡 Key idea
Renewal states do not change the observed state, but they represent meaningful internal transitions in the underlying stochastic process.
Here we assume that when licenses are created, all licenses are renewbale (activated) by default. Then, using the Markov chain, we modelise some states as renewable or not renewable, so the license can be deactivated and then reactivated or changed to another subscription (still staying inactive).

### h. **Possible improvments:**
I am keeping things simple here; but we may consider lower price for customers who has several licenses (like discounts): the more customers has license, the more they get some discount from the inital price. Also the longer they have subscribed, the more discount they can get. 

Ideas for even more realistic data:
- discount on number of years customers have been subscribing (renew=True)
- discount on number of license customers are currently subscribing (renew=True)

We can also consider that some licenses could be shared amongst clients. 


## 2.1 Validation step

### Validation script

To run validation script; enter in a terminal

```shell
uv run python -m app.validate_csv
```
Output logs are located in the `app/csv` folder.

## 2.2 Transformation step

### Transformation with python/pandas
To run transformation, enter in a terminal
`uv run python -m app.transformation`

The script requieres both csv files `initial_licenses.csv`and `license_changes.csv` in `csv`folder
It outputs `transformed.csv` in the `csv` folder.

### Storage in SQL database:
For database usage, we are going to use SQlite as a sql database in the docker image. The idea is to keep docker image as small as possible.

SQL queries are stored in `app/sql` folder.
Process:
- `create.sql` is used to create the database
- The python script `app/add_database.py` can be used to load data generated from the csv files inside databases.
- `req.sql` is used to mimick the behaviour of transformation.py but whithin the docker file. 

### Transformation with SQL request
Please see answer in the file named : `app/sql/req.sql`
**Regarding question about database architecture.**
First, regarding the database creation, it could be nice to inculde a foreign key referring to initial_licenses 's `id`. 
Second; the transformation script is overly large and complex. It could be improved by splitting it into modular steps and using intermediate tables/views instead of relying heavily on Common Table Expressions (CTEs).

## 3. Industrialisation and testing steps : Docker and Tests

### Industrialisation through Docker

**Please visit docker installation beforehand:
- [docker installation for linux](https://docs.docker.com/engine/install/)
- [docker installation for windows and wsl2](https://docs.docker.com/desktop/features/wsl/)

To use the pipeline within docker, run this command: 
First build, using 
```shell
docker build -t pipeline .
```
Second, run docker using 
```shell
docker run -v $(pwd)/app/mnt:/app/app/csv -it pipeline 
```

Data and logs can be accessed using mounted folder: `app/mnt`
An entrypoint file has been made in order to execute the different element of the pipeline, ie:
- sql database (made using SQlite)
- data generation
- data validation
- data storage in database
- data transformation (python)
- data transformation (SQL)


### Tests (pytest)
To run the test, kindly execute from a terminal:
`uv run pytest -v app/tests`

To launch test suit through docker; one can use:
```shell
docker run -e MODE=test -it pipeline 
```
**Test structure**:
Several tests are provided:
- **unit tests**: `test_validate.py` and `test_transformation.py`
- **integration tests**: `test_pipeline.py` executing the whole pipeline
- **consistency tests**: `test_data_consistency.py`checks if generated data are consistent, data integrity checks


### Question CI/CD:
In order to execute CI using a tool like Github action:
1. Continuous Integration (CI)
* Define the OS environment (e.g., Ubuntu)
* Install dependencies using uv
* Run code quality checks (linting, formatting, optional type checking)
* Run and check the documentation generation
* Execute unit, integration,  consistency and end2end tests 
* Validate the full pipeline execution using Docker to ensure reproducibility
* define the workflows configuration file, ie which actions trigger when CI runs (each push request, when pushing on master branch, when releasing)

2. Continuous Delivery / Deployment (CD)
* Build a Docker image of the pipeline
* Deploy or execute the pipeline 

## 4. Pipeline

### 4.1 Conception questions

Regarding data that has been already processed: I would implement an incremental pipeline using a checkpoint (high-water mark / date of new incoming batch of data), typically based on a timestamp like updated_at or an ingestion time.

To handle late-arriving data, I would use a lookback window: each run would reprocess data from last_processed_timestamp - window, ensuring that delayed records are still captured.,  so I am sure I won't miss any data, even if I have to re process  data records that I have already processed. I could define a watermark or delay threshold to indicate when data is considered complete (which can better scale to continuous data processing)


I would persist this state in a durable store such as a database table. That way, I can keep track of incoming data, and see which data has been processed and which has been newly added.

Since this causes some reprocessing, I would make the pipeline idempotent by using upserts or deduplication based on a primary key.

This approach ensures I don’t miss late data while keeping the pipeline efficient and recoverable.


### 4.2 Incremental pipeline using python

For simplicity sake; i will save states in a csv file `states/state.csv`, but this would be not suitable for production.
To run the incremental pipeline, enter:
`run uv run python -m app.incremental_pipeline `

In the code, pipeline 's lookback is set using `LOOKBACK_MINUTES`. Since we want to process striclty only new incoming data, I will set `LOOKBACK_MINUTES=0` (ie deactivated), but this is risky especially if data arrive late.  one should set it to a small window (eg 30 minutes).
A lookback window is used: `last_processed_date - window`

There is an option to run backfill pipeline:
```shell
uv run python -m app.incremental_pipeline --mode backfill
```
Backfill strategy should be run from time to time, to ensure there are no very late batches of data (see 4.3 Edge case management).

For further information, type to display help message:
```shell
uv run python -m app.incremental_pipeline --help
```


### 4.3 Edge cases management
1. Late data arrival
I made a script that reproduce an incremental pipeline, with the following characteristics:
* Incremental pipeline: fast, includes a rolling reprocessing window to absorb late data
* Backfill pipeline: ensures correctness, catches very late data like 5-day late data, fixes missed updates

Hence, one can run the incremental pipeline every hours, and execute the backfill pipeline when needed (eg when data arrive late).

2. Pipeline failure
In case data pipeline fails, one should restart the pipeline given where it has failed.
Pipelines should be restartable through idempotent operations, checkpointing, and atomic writes; logging and monitoring (e.g., Grafana) helps detect failures. 
Batching also helps to isolate  and pinpoint issue. 


3. Backfill:
For this issue, one would backfill the last 30 days by  using data coming from a *source of truth*, and replaying the pipeline. This source of truth can be a data lake. 
One should consider re-processing partition by partition using an idempotent pipeline, and overwrite or merge the affected partitions in the data processed storage (eg database). One could also validate the results with data quality checks and monitor the pipeline during execution.
Here batching would help if computing ressources are limited.


### 4.4 Open Questions
For this pipeline to be used in production, I would use kafka, DBT and apache airflow as the core components. 
We assume the pipeline should be run every hour. But since there are no indications on the data volume, let's assume it is massive.
- Kafka (Depends on data volume and on the computing ressources available) : dispatches data from producers to  consumers, enables buffering, and making pipeline more scalable. 
- a data warehouse, for staging, and for analytics.
- DBT for the transformation invovling SQL queries. It also provides a way for incremental processing and for testing data integrity.
- Airflow for the orchestration layer: DAG enables scheduling and retries.
- a Grafana for monitoring metrics, logs and pipeline execution.
- AI agents (eg using Langchain): helps identify issues; useful to suggest pipeline retries or to trigger corrective actions, based on logs coming from the above tools, and metrics. It may help especially if human ressources are limited, but it should include human in the loop, as a safeguard. Note that we may remove those agents if we have heavy computing ressource limitations. 

The pipeline would look like (if computing ressources are available)
data source -> kafka -> data warehouse -> DBT <- airflow (orchestrating dbt) <-> BI + grafana + ai agents
