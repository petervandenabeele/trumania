# Trumania

## Documentation and tutorial

Trumania is a scenario-based random dataset generator library in python 3. 

The [Trumania github page](http://realimpactanalytics.github.io/trumania/) contains 
a detailed documentation of each of the concepts as well as a step-by-step explanation of 4 example scenarios. Those scenarios, and more, are present in the [tests/](tests/) folder in this repository.

The code documentation is available [here](http://realimpactanalytics.github.io/trumania/py-modindex.html).

You can also join the Trumania slack channel: [trumania.slack.com](https://trumania.slack.com)

## How to install 

Trumania is not packaged in any special way, the way it is used at the moment is simply to clone the code and install the required dependencies. This section describes how to do that.

Make sure you have python 3 and pip installed. Then make sure pipenv is installed:

```sh
# make sure you're using pip from a python 3 installation 
pip3 install --user pipenv
```


then install all python dependencies for this project: 

```sh
pipenv install --three
```

The steps below mention to prefix the commands with `pipenv run` whenever necessary in order to have access to those python dependencies. Alternatively, you can enter the corresponding virtualenv once with `pipenv shell`, in which case that prefix is no longer necessary. See [https://docs.pipenv.org](https://docs.pipenv.org) for more details about how to use pipenv to handle python dependencies. 


## Where and how to create a scenario

To create a scenario, simply create another python project that depends on trumania: 

```sh
mkdir -p /path/to/your/project
cd /path/to/your/project

# then simply add a dependency towards the location where you downloaded trumania:
pipenv install -e /path/to/trumania/
```

You can then create your scenario in python, let's call it `burbanks_and_friends_talking.py`.  In order to execute it, simply launch it from pipenv: 

```sh
pipenv run python burbanks_and_friends_talking.py  
```

## Contributing

This section provides a few pointers on how to handle the trumania codebase.

### Running Trumania unit tests locally


```sh
# make sure you are not inside another pipenv shell when running this
pipenv run py.test -s -v
```

### Python linting
Run `pipenv run flake8`. If nothing is returned, the correct styling has been applied.
