'''
Unravelling "Unravelling BDM's group decision model"

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
        self.offers = [] # Incoming challenges


    def calculate_utilities(self, alter):
        '''
        Calculate several utilities wrt a given alter
        '''
        dx = self.model.xmax - self.model.xmin
        mu = self.model.mu

        Us = 2 - 4*(0.5 - 0.5*abs((self.x - alter.x)/(dx)))**self.r
        Uf = 2 - 4*(0.5 + 0.5*abs((self.x - alter.x)/(dx)))**self.r
        Ub = 2 - 4*(0.5 - 0.25*((abs(self.x - mu)+abs(self.x-alter.x))/dx))**self.r
        Uw = 2 - 4*(0.5 + 0.25*((abs(self.x - mu)+abs(self.x-alter.x))/dx))**self.r
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
            if agent is self: continue
            d = abs(agent.x - alter.x) - abs(agent.x - self.x)
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
        s = alter.s
        EU = s * (p * utils["Us"] + (1-p)*utils["Uf"]) + (1-s)*utils["Us"]
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

    def send_offers(self):
        '''
        Send 'offers' of confrontation to different actors.
        '''
        for actor in self.model.Actors:
            if actor.name in self.expected_utilities:
                if self.expected_utilities[actor.name] > 0:
                    # Send a challenge!
                    offer = {"Sender": self.name,
                            "x": self.x, # Target position
                            "EU": self.expected_utilities[actor.name]
                            }
                    actor.offers.append(offer)

    def choose_offer(self):
        '''
        Choose the offer to accept, and change position accordingly.
        '''
        if len(self.offers) == 0: return

        max_util = max([offer["EU"] for offer in self.offers])
        self.offers = [offer for offer in self.offers if offer["EU"] == max_util]
        offer = min(self.offers, key=lambda x: abs(self.x-x["x"]))

        # Resolve offer
        Uj = offer["EU"]
        Ui = self.expected_utilities[offer["Sender"]]
        if Ui > 0 and Ui < Uj:
            # There was a conflict, and this actor lost
            print self.name + " loses confrontation to " + offer["Sender"]
            self.x = offer["x"]
            # If the actor won the conflict, action will be taken on the other end
        elif Ui < 0 and abs(Ui) < Uj:
            # Compromise
            print self.name + " compromises with " + offer["Sender"]
            self.x += (offer["x"] - self.x) * abs(Ui/Uj)
        elif Ui < 0 and abs(Ui) > Uj:
            # Capituate
            print self.name + " capituates to " + offer["Sender"]
            self.x = offer["x"]

        self.offers = [] # Reset offers





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
        Find the current Condorcet winner
        TODO: Make it the actual Condorcet winner though
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

    def find_mean(self):
        '''
        Find the current mean voter position
        '''
        t = 0 # Running weighted total
        w = 0 # Running total weight
        for actor in self.Actors:
            w += actor.s * actor.c
            t += actor.s * actor.c * actor.x
        return t/w


    def calculate_basic_utilities(self):
        for actor in self.Actors:
            for alter in self.Actors:
                if actor is not alter:
                    actor.calculate_utilities(alter)

    def calculate_win_probabilities(self):
        for actor in self.Actors:
            for alter in self.Actors:
                if actor is not alter:
                    actor.calculate_prob(alter)
    
    def calculate_expected_utilities(self):
        for actor in self.Actors:
            for alter in self.Actors:
                if actor is not alter:
                    actor.calculate_expected_utility(alter)

    def calculate_r(self):
        for actor in self.Actors:
            actor.calculate_r()


    def make_offers(self):
        '''
        Each actor sends offers / challenges to others
        '''
        for actor in self.Actors:
            actor.send_offers()

    def resolve_offers(self):
        for actor in self.Actors:
            actor.choose_offer()

    def determine_offers(self):
        '''
        Figure out which octant each dyad is in
        '''

        for i, actor1 in enumerate(self.Actors):
            for actor2 in self.Actors[i+1:]:
                Ui = actor1.expected_utilities[actor2.name]
                Uj = actor2.expected_utilities[actor1.name]
                if Ui > 0:
                    # Actor1 challenges
                    if Uj > 0:
                        # Conflict: Actor2 challenges as well.
                        if Ui > Uj:
                            #Confrontation, Actor 1 wins
                            result = "Conflict, " + actor1.name + " wins."
                        else:
                            result = "Conflict, " + actor2.name + " wins."
                    else:
                        if abs(Uj) < Ui:
                            result = "Compromise, " + actor1.name + " wins."
                        else:
                            result = "Compel, " + actor1.name + "wins"
                elif Uj > 0:
                    if abs(Ui) < Uj:
                        result = "Compromise, " + actor2.name + " wins."
                    else:
                        result = "Complel, " + actor2.name + " wins."
                else:
                    result = "Status Quo"
                print actor1.name, actor2.name, result

    def run_model(self):
        '''
        One step of the model.
        '''
        # 2. Let ri = 1
        for actor in self.Actors:
            actor.r = 1

        #3. Compute median position mu
        self.mu = self.find_mean()

        #4. Calculate basic utilities
        self.calculate_basic_utilities()

        #5. Basic win popularities
        self.calculate_win_probabilities()

        #7. Calculate expected utilities
        self.calculate_expected_utilities()

        # 8, 9 Calculate R and r
        self.calculate_r()

        # 10. Now use the new r to repeat all the steps above
        self.mu = self.find_mean()
        
        self.calculate_basic_utilities()
        self.calculate_win_probabilities()
        self.calculate_expected_utilities()

        # Send and choose offers
        self.make_offers()
        self.resolve_offers()






