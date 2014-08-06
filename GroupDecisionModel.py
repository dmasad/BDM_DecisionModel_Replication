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

        self.basic_utilities = {}
        self.probs = {}
        self.expected_utilities = {}


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
    def calculate_prob(self, alter):
        '''
        Calculate probability of winning against an alter.
        '''
        # There won't be a contest against an alter with the same preference
        if self.x == alter.x:
            self.probs[alter.name] = 0
            return

        top = 0
        bottom = 0
        for agent in self.model.Actors:
            d = (abs(agent.x - alter.x) - abs(agent.x - self.x))
            if d > 0:
                top += agent.c * agent.s * d
            bottom += agent.c * agent.s * abs(d)
        self.probs[alter.name] = top/bottom

    def calculate_expected_utility(self, alter):
        '''
        Expected utility against a given alter
        '''
        # Local variables for ease of typing:
        p = self.probs[alter.name]
        utils = self.basic_utilities[alter.name]
        Q = self.model.Q
        T = self.model.T

        EU = alter.s * (p * utils["Us"] + (1-p)*utils["Uf"]) + (1-alter.s)*utils["Us"]
        EU -= Q*utils["Usq"] - (1-Q)*(T*utils["Ub"] + (1-T)*utils["Uw"])
        self.expected_utilities[alter.name] = EU

    def calculate_r(self):
        '''
        Calculate the risk exponent
        '''

        # Each other agent's expected utility of challenging this agent
        attack_utils = [alter.expected_utilities[self.name] 
            for alter in self.model.Actors if alter is not self]

        security_levels = []
        for actor in self.model.Actors:
            security = sum([alter.expected_utilities[actor.name] 
                    for alter in self.model.Actors if alter is not actor])
            security_levels.append(security)

        max_security = max(security_levels)
        min_security = min(security_levels)
        R = (2 * sum(attack_utils) - max_security - min_security) / (max_security - min_security)
        self.r = (1 - R/3)/(1+R/3)




class Model(object):
    '''
    A model container
    '''

    def __init__(self, Actors, xmax, xmin, Q=1.0, T=1.0):
        '''
        Initiate a model with a list of Actor objects
        '''

        self.Actors = Actors
        self.xmax = xmax
        self.xmin = xmin
        self.dx = xmax - xmin
        self.mu = 0 # Current median position
        self.Q =  Q
        self.T = T

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



