# m3x-fuzzy-controller

Fuzzy Controller for the Myopro 2 Device that tunes the gains based on different input factors. For the M3X project.

## Setup 

To set up the controller, clone this repository and ensure that you have Python and Pip installed on your system. 

Then run `pip install -r requirements.txt` to install dependencies.

## Bluetooth Settings

If you get a SerialException related to not being able to open a port change the following line in `fuzzy_controller.py`.

```python
ser = myopro.Device('com5')
```

## Dependencies

- [M3X Data Streaming Python Library](https://github.com/cjcocokrisp/m3x-data-streaming) (INCLUDED IN REPO)
- [Fuzzylab](https://github.com/ITTcs/fuzzylab/tree/master) (Installed through pip)
- [Matlab Fuzzy Logic Toolbox](https://www.mathworks.com/products/fuzzy-logic.html) (Used to create .fis files)