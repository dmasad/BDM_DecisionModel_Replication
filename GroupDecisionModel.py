'''
Unravelling "Unravelling BDM's group decision model"
===========================================================================

This code attempts to replicate the model described by Sholz, Calbert and Smith
(2011) [http://jtp.sagepub.com/content/23/4/510], which in turn is a replication
of Bruce Bueno De Mesquita's group decision / expected utility model.   

The code consists of an Actor class, which stores actor-level variables and 
calculation methods, and a Model class to store the actors and streamline the 
model execution.

Some, but not all, the variable names correspond to their names in the paper.

Much of the model deals with pairwise interactions; in the following code, 
'alter' generally refers to the actor's counterpart in such an interaction, 
often designated with a subscript j in the paper.
'''

from __future__ import division


class Actor(object):
    '''
    A BDM actor.

    Actor attributes:
        name: The actor's name; should be unique
        x: Preferred outcome
        c: Capability / power
        s: Salience of the issue in question
        r: Risk exponent. Recalculated every round.

    Relational information (dictionaries, keyed on alter name):
        basic_utilities: The actor's utilities if it wins, loses, etc. against
                        this alter.
        probs: Probability of winning a conflict with the given actor.
        expected_utilities: The expected utility of challenging this actor.

        offers: A list of incoming offers (which are really challenges). Reset 
                each round.
    '''

    def __init__(self, name, model, x, c, s):
        '''
        Define a new actor.

        Args:
            name: Actor name.
            model: The containing model object. 
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
        Calculate and set the base utilities wrt a given alter.

        (See Section 3 of the paper)

        Args:
            alter: The counterpart Actor object.
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

        (See Section 4 of the paper)

        Args:
            alter: The counterpart Actor object.

        Note: The paper seems to  imply that the top of the Pi,j fraction is 
        included only when it is greater than 0 (as in the commented-out code). 
        However, that did not seem to produce correct results. The cited BDM
        paper suggests something closer to the form executing below, though it
        didn't (I think) contain the lower-bound. 
        '''
        # There won't be a contest against an alter with the same preference
        if self.x == alter.x:
            self.probs[alter.name] = 0
            return

        top = 0
        bottom = 0
        for agent in self.model.Actors:
            #if agent is self: continue
            d = abs(agent.x - alter.x) - abs(agent.x - self.x)
            top += agent.c * agent.s * d
            #if d > 0:
            #    top += agent.c * agent.s * d
            bottom += agent.c * agent.s * abs(d)
        top = max(top, 0)
        self.probs[alter.name] = top/bottom

    def calculate_expected_utility(self, alter):
        '''
        Expected utility against a given alter. 
        (See Section 2.2 of the paper)

        Args:
            alter: The counterpart Actor object.

        Also uses the Q and T values set in the model object.
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
        Calculate the risk exponent, after calculating E[U]s with r=1.
        (See Section 5 of the paper)
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
        (See Section 6 of the paper)

        The actor only challenges / sends an offer when the expected utility 
        of challenging another actor > 0.
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
        (See Section 6 of the paper)

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
    A model container and calculation object. 

    Stores the actors and model-level constants, and facilitates the main model
    loop.

    Attributes:
        xmax: The maximum policy position / outcome preferred by any actor.
        xmin: The minimum policy position / outcome preferred by any actor.
        Q: Fixed probability assigned by all actors of alters changing position 
            absent a challenge.
        T: All actors' fixed probability assigned to alters changing position
            *improving* things for the actor.
        mu: Current mean position of all actors.

    Actor storage:
        Actors: List of all actors contained in the model.
        actors: Name-keyed dictionary of the same Actor objects.
    '''

    def __init__(self, Actors, xmax, xmin, Q=1.0, T=1.0):
        '''
        Initiate a model with a list of Actor objects
        '''

        self.Actors = Actors
        for actor in self.Actors:
            actor.model = self
        self.xmax = xmax
        self.xmin = xmin
        self.dx = xmax - xmin
        self.mu = 0 # Current median position
        self.Q =  Q
        self.T = T

        self.actor = {actor.name: actor for actor in self.Actors}

    def vote(self, verbose=False):
        '''
        Find the current Condorcet winner / median voting position.
        (See Section 3.2 of the paper)
        
        Args:
            verbose: If true, print out all the pairwise contests.
        Returns:
            The Condorcet winner of the pairwise contests.

        TODO: Verify that this method results in the actual Condorcet winner.
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
        Find the current mean voter position.
        (NOT explicitly defined in the paper)

        Returns:
            Mean voter position. Does NOT necessarily correspond to a position 
            held by any particular actor.
        '''
        t = 0 # Running weighted total
        w = 0 # Running total weight
        for actor in self.Actors:
            w += actor.s * actor.c
            t += actor.s * actor.c * actor.x
        return t/w


    def calculate_basic_utilities(self):
        '''
        Calculate each actor's basic utilities.
        (Corresponds to Step 4 of the Appendix)
        '''
        for actor in self.Actors:
            for alter in self.Actors:
                if actor is not alter:
                    actor.calculate_utilities(alter)

    def calculate_win_probabilities(self):
        '''
        Calculate each actor's win probabilities against all others.
        (Corresponds to Step 5 of the Appendix)
        '''
        for actor in self.Actors:
            for alter in self.Actors:
                if actor is not alter:
                    actor.calculate_prob(alter)
    
    def calculate_expected_utilities(self):
        '''
        Calculate each actor's expected utility against all others.
        (Corresponds to Step 7 of the Appendix)
        '''
        for actor in self.Actors:
            for alter in self.Actors:
                if actor is not alter:
                    actor.calculate_expected_utility(alter)

    def calculate_r(self):
        '''
        Calculate each actor's risk coefficient.
        (Corresponds to Steps 8, 9 of the Appendix)
        '''
        for actor in self.Actors:
            actor.calculate_r()


    def make_offers(self):
        '''
        Each actor sends offers / challenges to others.
        (Part of Step 11 of the Appendix)
        '''
        for actor in self.Actors:
            actor.send_offers()

    def resolve_offers(self):
        '''
        Each actor selects which offer to accede to.
        (Second part of Step 11 of the Appendix)
        '''
        for actor in self.Actors:
            actor.choose_offer()


    def run_model(self):
        '''
        Run one whole step through the model procedure.
        (Corresponds to steps 2-11 in the appendix)
        '''
        # 2. Let ri = 1
        for actor in self.Actors:
            actor.r = 1

        #3. Compute median position mu
        self.mu = self.find_mean()
        #self.mu = self.vote(False)

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

    def draw_quadrants(self, focus, ax, scale=1):
        '''
        Draws a BDM-style quadrant chart from the perspective of a given actor.

        Args:
            focus: The name of the actor to put on the X axis.
            ax: Matplotlib subplot object to draw to.
            scale: Scale the axes from (-scale, scale)

        '''
        # Put the spines through the origin
        ax.spines['left'].set_position('zero')
        ax.spines['right'].set_color('none')
        ax.spines['bottom'].set_position('zero')
        ax.spines['top'].set_color('none')
        #ax.spines['left'].set_smart_bounds(True)
        #ax.spines['bottom'].set_smart_bounds(True)
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        ax.set_xlim(-scale,scale)
        ax.set_ylim(-scale,scale)

        actor = self.actor[focus]
        for alter in self.Actors:
            if actor is alter: continue
            x = actor.expected_utilities[alter.name]
            y = alter.expected_utilities[actor.name]
            ax.text(x,y, alter.name)
        return ax







