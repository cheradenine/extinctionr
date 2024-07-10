Prerequisites:
Python 3.8

## Create a new directory for the project
```
mkdir xrboston # or whatever you want to call it
cd xrboston
```
## Install asdf

To get the correct version of python on a system it is highly recommned you use [asdf](https://asdf-vm.com/)
Once asdf is installed you need the python plugin:

```
asdf plugin add python
```

Now you can install python 3.8. Currently the site is running 3.8.10 but the latest 3.8 should work:

```
asdf install python 3.8.10
```
Note: this actually compiles python on your system so you will probably need all the build tools, like xcode and you may run into some required libraries. Homebrew can manage this.

If all goes well you will have a python 3.8.n on your system but to make it the python for the project you can go into the project root directory and run:

```
asdf local python 3.8.10
```
And now in that directory your path will point to that python. You can verify this via:

```
python --version
```
Should print `Python 3.8.10`

## Create a python virtual environment
This is needed to manage all of the python packages that the project requires.

python -m venv venv

## Activate the virtual environment

```
source ./venv/bin/activate

git clone <this project>
cd extinctionr

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Note: to exit the python venv use:

`deactivate`


