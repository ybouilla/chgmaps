
# Exercise Chargemaps
## 0. Installation 

**Requirements**:
- Linux OS 
- Windows with WSL2 (Windows Subsystem Linux) activated

### Using uv as a package manager
*Nota*: Uv has been selected here for its known efficiency. Other python package manager should be working but have not been tested.

First install uv. Then you can install requirements by running:
**On Linux**:
```
source .venv/bin/activate
uv pip install -r requirements.txt
```

Run the following script: `uv run python -m app.main_data_generation`
Use `uv run python -m app.main_data_generation --help` for more details.

## Parameters
Parameters are defined in the script `main_data_generation.py`

### Number of licenses per clients
As asked, a paretto distribution is used to model number of licenses per clients.

### Changes in the licenses.

To simulate the fact most clients don't change their subscriptions, but only a small portion do, i used a Paretto like distribution.

### **relationship between type and prices:**

Since we have 3 kinds of type (SIM, PASS, SUPERVISION), I proposed to map for each type a price:
 - PASS: 100
 - SIM: 1000
 - SUPERVISION: 5000

###  type modelling

I used a Markov Chain to represent the transition dynamics. I defined a 6 transition matrix where each row represents probabilities of moving between states.

🧩 Conceptual model

This system behaves like:

* A 3-state operational process (core system)
* Embedded in a 6-state Markov chain
With transient “renewal” events acting as instant resets
💡 Key idea

Renewal states do not change the observed business state, but they represent meaningful internal transitions in the underlying stochastic process.

### Renewable:

Here we assume that when licenses are created, all licenses are renewbale (activated) by default.

### **Possible improvments:**
I am keeping things simple here; but we may consider lower price for customers who has several licenses (like discounts): the more customers has license, the more they get some discount from the inital price. Also the longer they have subscribed, the more discount they can get. 

Ideas for even more realistic data:
- discount on nb of years customers have been subscribing (renew=True)
- discount on number of license customers are currently subscribing (renew=True)

## 1. Data Generation
## 2.1 Validation step

### Validation script

To run validation script; enter in a terminal

`uv run python app/validation.py`.
Output logs are located in the `app/csv` folder.

## 2.2 Transformation step

### Transformation with python/pandas
To run transformation, enter in a terminal
`uv run python app/transformation.py`

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
Second; The script made to perform transform is too big: one could consider create all the intermediate table 
where i had to use CTE. 

## 3. Industrialisation and testing steps : Docker and Test

### Industrialisation through Docker

**Please visit docker installation beforehand:
- [docker installation for linux]()
- [docker installation for windows and wsl2]()

To use the pipeline within docker, run this command: 
First build, using `docker build -t pipeline .`
Second, run docker using `docker run -v $(pwd)/app/mnt:/app/app/csv -it pipeline `

Data and logs can be accessed using mounted folder: `app\mnt`
An entrypoint file has been made in order to execute the different element of the pipeline, ie:
- sql database (made using SQlite)
- data generation
- data validation
- data storage in database
- data transformation (python)
- data transformation (SQL)


### Tests (pytest)
To run the test, kindly execute from a terminal:
`uv run pytest app/tests`

To test through docker; one can use:
```shell
export MODE=test
docker run -v $(pwd)/app/mnt:/app/app/csv -it pipeline 
```
**Test structure**:
Several tests are provided:
- **unit tests**: `test_validate.py` and `test_transformation.py`
- **integration tests**: `test_pipeline.py` executing the whole pipeline
- **consistency tests**: `test_data_consistency.py`checks if generated data are consistent, data integrity checks


### Question CI/CD:

In order to execute CI using a tool like Github action:
1. define OS to run on the pipeline (eg ubuntu)
2. load the packages needed
3. run all the tests
4. test the pipeline through docker
5. test the documentation
5. define the workflows file, ie which actions trigger when CI runs (each push request, when pushing on master branch, when releasing)

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
`run uv run app/incremental_pipeline.py `

In the code, pipeline 's lookback is set using `LOOKBACK_MINUTES`. Since we want to process striclty only new incoming data, I will set `LOOKBACK_MINUTES=0` (ie deactivated), but this is risky especially if data arrive late.  one should set it to a small window (eg 30 minutes).

There is an option to run backfill pipeline:
`uv run app/incremental_pipeline.py --mode backfill`
Backfill strategy should be run from time to time, to ensure there are no very late batches of data (see 4.3 Edge case management).

For further information, type to display help message:
`uv run app/incremental_pipeline.py --help`


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
