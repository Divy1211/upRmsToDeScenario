# UP RMS To DE Scenario Conversion Tool
1. This python script allows you to take an RMS from AoC UserPatch/voobly/wololo kingdoms and use the effect_amount, guard_state, effect_percent used in that RMS to generate a scenario for AoE2DE which has the same effects as the RMS!

2. Note: DE's Update on 25/1/2021 re-introduces effect_amount and effect_percent in RMS!

# Prerequisites, Installation

1. You must have [python3.8+](https://www.python.org/downloads/) installed.
2. After you have installed python, open cmd/terminal and run the following commands:
  `pip install AoE2ScenarioParser`
  `pip install bidict`
Once you've done this, you're good to go!

# How to use the tool?

1. Download the repository to a local folder.
2. Place the RMS file in the same folder as the files from the repository
3. Go into the `py script` folder and right click the `up rms to de scenario.py` and open it with python (you can also run it from cmd, or any other way)
4. Enter the map name when prompted, then wait for the tool to finish writing all the scenarios!
5. Once its done, 8 Scenarios for 1-8 players will be generated in the same folder that contained the RMS file.

 A few notes:
 
 1. These scenarios **only** have the triggers that code for the effect_amount, effect_percent and guard_state commands, and the map has to be generated manually.
 2. Workings of some of the userpatch effects are not understood, if you are using an effect that gives you an error but it works on user patch, then you can notify me at Alian713#0069 on Discord
 3. ALL userpatch commands written in the specified RMS file will be read and converted into triggers, even if they are commented or inside if else or random blocks! Ignoring effects in comments and properly converting commands written inside if else or random blocks will be implemented in a future version!
