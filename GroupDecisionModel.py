'''
Unravelling "Unravelling BDM's group decision model"

Because discrete, algorithmic game theory works better as code, you guys.

Without loss of generality, assume that x ina [0, 1].
'''

from __future__ import division
from collections import defaultdict
import numpy as np


class Actor(object):
    '''
    A BDM actor.
    '''

    def __init__(self, name, model, x, c, s):
        '''
        Define a new actor.

        Args:
            name: Come on.
            model: The containing model object
            x: Preferred policy outcome
            c: Capability / power
            s: Salience
        '''
        self.name = name
        self.x = x
        self.c = c
        self.s = s
        self.r = 1

        self.basic_utilities = defaultdict(lambda: 
            {"Us": 0,
            "Uf": 0,
            "Ub": 0,
            "Uw": 0,
            "Usq": 0 })


    def calculate_utilities(self, alter):
        '''
        Calculate several utilities wrt a given alter
        '''
        dx = self.model.xmax - self.model.xmin
        mu = self.model.mu

        Us = 2 - 4*(0.5 - 0.5*abs((self.x - alter.x)/(dx)))**self.r
        Uf = 2 - 4*(0.5 + 0.5*abs((self.x - alter.x)/(dx)))**self.r
        Ub = 2 - 4*(0.5 - 0.25*(abs(self.x - mu)+abs(self.x-alter.x))/dx)**self.r
        Uw = 2 - 4*(0.5 + 0.25*(abs(self.x - mu)+abs(self.x-alter.x))/dx)**self.r
        Usq = 2 - 4*0.5**self.r

        self.basic_utilities[alter.name] = {"Us": Us,
                                            "Uf": Uf,
                                            "Ub": Ub,
                                            "Uw": Uw,
                                            "Usq": Usq}

class Model(object):
    '''
    A model container
    '''

    def __init__(self, Actors, xmax, xmin):
        '''
        Initiate a model with a list of Actor objects
        '''

        self.Actors = Actors
        self.xmax = xmax
        self.xmin = xmin
        self.dx = xmax - xmin
        self.mu = 0 # Current median position

    def vote(self, verbose=True):
        '''
        Find the current median voter
        '''
        pairwise_contests = {}
        for j in self.Actors:
            for k in self.Actors:
                votes = 0
                for i in self.Actors:
                    votes += i.c*i.s*((abs(i.x - k.x) - abs(i.x - j.x))/(self.dx))
                pairwise_contests[(j.x, k.x)] = votes
        
        if verbose:
            for key, val in pairwise_contests.items():
                print key, val
        return max(pairwise_contests, key=lambda x: pairwise_contests[x])[0]



