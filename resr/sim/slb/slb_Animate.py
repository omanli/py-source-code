# Animate classes.py

"""
This program demonstrates the various animation classes available in salabim.
"""

'''
C:\Miniconda3\envs\opt\Lib\site-packages\salabim
C:\Miniconda3\envs\opt\Lib\site-packages\salabim\salabim.py
ln3919 class Environment
ln5094 class Environment.animate()
ln6187 def salabim_logo()
'''

'''
gog: TclError can't invoke destroy command application has been destroyed
https://stackoverflow.com/questions/35686580/tclerror-cant-invoke-destroy-command-application-has-been-destroyed
https://stackoverflow.com/questions/21645716/cannot-invoke-button-command-application-has-been-destroyed
'''

import salabim as sim

T="""\
Multi Line Text
-----------------
Lorem ipsum dolor sit amet, consectetur
adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud
exercitation ullamco laboris nisi ut
aliquip ex ea commodo consequat. Duis aute
irure dolor in reprehenderit in voluptate
velit esse cillum dolore eu fugiat nulla
pariatur.
Excepteur sint occaecat cupidatat non
proident, sunt in culpa qui officia
deserunt mollit anim id est laborum.
"""

env = sim.Environment(trace=False)
env.animate(True)
env.modelname("Demo Animation Class")
env.background_color("20%gray")

sim.AnimatePolygon(spec=(100, 100, 300, 100, 200, 190), text="A\nPolygon")
sim.AnimateLine(spec=(100, 200, 300, 300), text="A Line")
sim.AnimateRectangle(spec=(100, 10, 300, 30), text="A Rectangle")
sim.AnimateCircle(radius=60, x=100, y=400, text="A Circle")
sim.AnimateCircle(radius=60, radius1=30, x=300, y=400, text="An Ellipse")
sim.AnimatePoints(spec=(100, 500, 150, 550, 180, 570, 250, 500, 300, 500), text="Some\nPoints")
sim.AnimateText(text="This is a one-line text", x=100, y=600)
sim.AnimateText(text=T, x=500, y=100)
sim.AnimateImage("px/slb_pipe.jpg", x=500, y=400)

env.run(100)
