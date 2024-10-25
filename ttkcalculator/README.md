# Simple TKInter Calculator
T.B.D.

## Features
T.B.D.

## Installation

Make sure you have Python 3.12 or newer installed on your system. Please note
that the commands in the next chapters use `python` but your system may require
you to type `python3`.

### For Users
- Choose your "installation" folder and open it in a terminal / cmd / powershell
- Clone the GitHub repository
    ```shell
    git clone https://github.com/slacker-by-design/python_etudes
    ```
    If you don't have git installed, go back to the 
    [python_etudes](https://github.com/slacker-by-design/python_etudes) 
    GitHub repository page and download it as a 
    [zip](https://github.com/slacker-by-design/python_etudes/archive/refs/heads/main.zip)
    archive file. Then extract its contents to an installation folder of your choice.
- Run the calculator
    ```shell
    cd python_etudes/ttkcalculator
    python -m ttkcalculator
    ```

### For Developers
- Choose your "installation" folder and clone the GitHub repository into it
- Create a Python virtual environment
    ```shell
    cd ttkcalculator
    python -m venv venv
    ```
- Activate the virtual environment
    - Linux & macOS
      ```shell
      source venv/bin/activate    
      ```
    - Windows Powershell
      ```shell
      .\venv\Scripts\Activate.ps1
      ```
    - Windows CMD
        ```shell
        venv\scripts\activate.bat
        ```
- Install the `ttkcalculator` package as editable
    ```shell
    python -m pip install -e .
    ```

#### Running Tests
- Make sure the `pytest` package is installed in your virtual environment
    The command
    ```shell
    python -m pip list
    ```
    should show a list of installed packages including `ttkcalculator` and `pytest`.
    In case `pytest` is missing, install it by typing
    ```shell
    python -m pip install .[test]
    ```
- Run the tests
    ```shell
    python -m pytest
    ```

## Documentation
T.B.D.

## License
[MIT License](../LICENSE)
