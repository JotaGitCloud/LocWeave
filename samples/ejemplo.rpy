define e = Character("Eileen")

label start:
    scene bg room
    e "Hello, [player]! Welcome to the village."
    "The wind is cold tonight."
    menu:
        "Go to the forest":
            jump forest
        "Stay at the inn":
            jump inn
