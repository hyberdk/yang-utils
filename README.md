# Misc tools and scripts for working with yang models
This repo is just a random collection of tools and scripts that I use to work with yang models

note: that most of these are "spaghetti code"

## validating and finding argumenting models
This script is something that I (quickly) slapped together to to make ydk-gen working.
I had a bunch of issues validating the Cisco-IOS-XE-native.yang model and understanding how
it all worked together.. 

Basically it does the following:

1. loads all the models in the "model_path" path into a libyang collection
2. loads the "model_name" and validates that.
3. find all the models in the "model_path" that implements an Yang argument (extends a model)
4. find all the "dead-end" containers in the "model_name"
   * dead-end container is an empty container without leafs, leaflists etc.
   * usually you would think a dead-end container would not implement the "presence"..
   eg. if the presence is set, then it would not be dead-end, but sometimes it actually does have that set and still there is a model that arguments it.
5. Then maps all the "argumenting" models into dead-end containers so we can find "upstream"
models that we want to include in the yang-model-set to get a complete model.
6. finally prints some stats..

edit the model_path and model_name and just run it ;-)