# project guidelines
## Build/configuration
* your are using yaml configuration

## Testing
* your are using a TDD approach
* You are using pytest
* Use parameterized tests whenever relevant

## Additional Information
* you are using classes to structure the code
* Flask command line is the default entry point. Do not generate API entry points.
* do not make function above 20 lines. Generate intermediary functions when it make sense.
* refactor the code to use these functions

## Specific projject instructions
* when you deal with coordinates, stick to the x,y standard. (longitude, latitude)
* When you return just a pair of value for coordinates, or pass to a function, use a Tuple[float, float] 