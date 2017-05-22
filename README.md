# rulesforNMT

## DCU implementation of (Hokamp and Liu, 2017)
Found at `dcu-impl` as git submodule. 
This should mean that it is cloned when this rulesforNMT repository is cloned. 
If not, try 

        git submodule update --init --recursive

They don't document their dependencies; here are those I've had to install:

        pip install theano
        
This installs numpy and scipy as well. 

### Implementation Details
Regardless of the implementation of constrained decoding that we choose, 
there's likely room to learn from DCU's implementation.

Their NMT classes implement three generation methods:

        generate()
        generate_constrained()
        continue_constrained()
        
...more to come.
