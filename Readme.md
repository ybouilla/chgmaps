
# Exercise Chargemaps
## Installation 

### Using uv as a package manager
First install uv. Then you can install requirements by running:
`uv pip install -r requirements.txt`

relationship between type and prices:

I am keeing things simple here; but we may consider lower price for customers who has several licenses (like discounts): the more customers has license, the more he get some discount from the inital price


## Data Generation
Run the following script: `uv run main_data_generation.py`

## Parameters
Parameters are defined in the script `main_data_generation.py`
### modification:

modification can happen at every time

### type modelling

Define transition dynamics

We define a

6 transition matrix where each row represents probabilities of moving between states.

🧩 Conceptual model

This system behaves like:

* A 3-state operational process (core system)
* Embedded in a 6-state Markov chain
With transient “renewal” events acting as instant resets
💡 Key idea

Renewal states do not change the observed business state, but they represent meaningful internal transitions in the underlying stochastic process.

### Renewable:

Here we assume that when licenses are created, all licenses are renewbale (activated) by default.

Ideas for even more realistic data:
- discount on nb of years customers have been subscribing (renew=True)
- discount on number of license customers are currently subscribing (renew=True)

## Validation step

### Validation script

To run validation script; enter on a shell

`uv run validation.py`