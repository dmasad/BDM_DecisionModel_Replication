
class Actor(object):
    '''
    A BDM actor.

    Actor attributes:
        name: The actor's name; should be unique
        x: Preferred outcome
        c: Capability / power
        s: Salience of the issue in question
        r: Risk exponent. Recalculated every round.
    '''

    def __init__(self, name, x, c, s):
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

        self.probs = {}
        self.offers = [] # Incoming challenges

    def vote(self, x_j, x_k):
        '''
        Allocate capacity- and salience-weighted votes to x_j over x_k
        '''
        dx = self.model.position_range
        x_k_dist = (abs(self.x - x_k) / dx)**self.r
        x_j_dist = (abs(self.x - x_j) / dx)**self.r
        return self.c * self.s * (x_k_dist - x_j_dist)


    # Utility calculations
    # ---------------------------------------------------------
    #   These are separated in order to allow each actor to calculate their 
    #   subjective view of them. In practice, the subjectivity comes from 
    #   their different risk tolerances.

    def u_success(self, actor, alter):
        '''
        Subjective utility of a successful challenge by actor against alter.
        '''
        dx = self.model.position_range
        return 2 - 4*(0.5 - 0.5*abs((actor.x - alter.x)/(dx)))**self.r

    def u_failure(self, actor, alter):
        '''
        Subjective utility of a failed challenge by actor against alter.
        '''
        dx = self.model.position_range
        return 2 - 4*(0.5 + 0.5*abs((actor.x - alter.x)/(dx)))**self.r
    
