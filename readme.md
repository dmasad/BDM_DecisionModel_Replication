# Replicating the replication of BDM's Expected Utility Model

Code for my attempt to translate the [Scholz, Calbert & Smith (2011)](http://jtp.sagepub.com/content/23/4/510) replication of Bruce Bueno De Mesquita's Expected Utility model into Python. The replication process is described more thoroughly in [this blog post](). Note that the current code DOES NOT fully reproduce the results in Scholz et al., so use at your own risk. Please point out any mistakes that you find!

**GroupDecisionModel.py** contains the model code. It should be fairly well documented.

**ExampleActors.csv** contains the sample data from the paper.

**Testing.ipynb** actuallys runs the model with the sample input data, and generates a few charts for comparison with those shown in the paper.

**Scratchpad.ipynb** is an IPython Notebook I used for various experiments. You should probably just ignore it.