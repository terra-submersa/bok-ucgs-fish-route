# Junie Lessons

After qui te some time finding reasns not to try these  LLM coding assistant, I picked up this project frmo scratch

# How I use Junie
* I update the [tasks](tasks.md) file and copy paste each task in the Junie dialog.
* General instructions are update in in the [guidelines](../.junie/guidelines.md)

# Where it surprised me
* the code works and rthe structure is rather intuitive
* global refactoring, for example "let's change al function calls and return from latitude,longitude to x,y, i.e. longitude, latitude"
* "messy task" such as "print the route in a PNG with an openStreetMap background"

# The weaknesses
* as soon as the problems becomes slightly mathematics (flight rules with angles)
* overcomplicates things (make three function for vertical, horizontal, angled). I could rewrite everything in one, dividing by at least 5 the number of code lines
* Concept refactoring ("let's forget using WGS84 system by defaukt and go to UTM for simpler computations)