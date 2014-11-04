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
        Allocate capacity- and salience-weighted votes to x_j over x_k.
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

    def u_sq(self):
        '''
        Subjective utility of the status quo
        '''
        return 2 - 4 * (0.5**self.r)

    def expected_utility(self, actor, alter):
        '''
        Subjective expected utility of actor challenging alter.

        Currently ignores the T part of the equation altogether.
        '''
        p = self.probability(actor, alter)
        Us = self.u_success(actor, alter)
        Uf = self.u_failure(actor, alter)
        Usq = self.u_sq()
        s = alter.s

        return s*(p*Us + (1-p)*Uf) + (1-s)*Us - self.model.Q * Usq

    def probability(self, actor, alter):
        '''
        Probability of actor successfully challenging alter.

        Follows the Scholz et al. methodology.
        '''
        if actor.x == alter.x:
            return 0

        # Sum the magnitudes of all possible votes:
        all_positions = self.model.get_positions()
        all_votes = 0
        for an_actor in self.model.actors:
            for x_j in all_positions:
                for x_k in all_positions:
                    all_votes += abs(an_actor.vote(x_j, x_k))

        # Sum votes for the position of actor vs alter:
        votes = 0
        for an_actor in self.model.actors:
            v = an_actor.vote(actor.x, alter.x)
            if v > 0:
                votes += v

        return votes / all_votes

    # ---------------------------------------------------------

    def calculate_r(self):
        '''
        Calculate the risk exponent.
        '''
        self.r = 1

        # Each agent's expected utility from challengin this agent.
        attack_utils = [self.expected_utility(alter, self) 
                            for alter in self.model.actors if alter is not self]

        security_levels = []
        for actor in self.model.actors:
            security = sum([self.expected_utility(alter, actor) 
                for alter in self.model.actors if alter is not actor])
            security_levels.append(security)

        max_security = max(security_levels)
        min_security = min(security_levels)

        R = (2 * sum(attack_utils) - max_security - min_security) 
        R /= (max_security - min_security)

        self.r = (1 -  R / 3.0) / (1 + R / 3.0)

    def send_offers(self):
        '''
        Send 'offers' of confrontation to different actors
        '''
        for alter in self.model.actors:
            if self.x == alter.x: continue
            if alter.expected_utility(self, alter) > 0:
                Uj = alter.expected_utility(self, alter)
                Ui = alter.expected_utility(alter, self)
                offer_type = False
                # Figure out types:
                if Uj > Ui > 0:
                    offer_type = "Challenge"
                elif Ui > Uj > 0:
                    # Will be handled on the other side
                    pass
                elif Ui < 0 and Uj > abs(Ui):
                    offer_type = "Compromise"
                elif Ui < 0 and Uj < abs(Ui):
                    offer_type = "Capitulate"
                else:
                    print self.name, alter.name
                    raise Exception("Shouldn't be here!")

                if offer_type:
                    # Send the challenge
                    offer = {"Sender": self.name,
                            "x": self.x,
                            "Ui": Ui,
                            "Uj": Uj,
                            "type": offer_type}
                    alter.offers.append(offer)

    def choose_offer(self):
        '''
        Choose an offer to accept, and change position accordingly.
        '''

        offer_types = [offer["type"] for offer in self.offers]
        best_offer = False
        if "Challenge" in offer_types:
            offers = [o for o in self.offers if o["type"] == "Challenge"]
            best_offer = min(offers, key=lambda o: abs(o["x"] - self.x))
        elif "Compromise" in offer_types:
            offers = [o for o in self.offers if o["type"] == "Compromise"]
            best_offer = min(offers, 
                key=lambda o: ( (o["Ui"]*self.x + o["Uj"]*o["x"])
                    / (abs(o["Ui"]) + abs(o["Uj"])) ))
        elif "Capitulate" in offer_types:
            offers = [o for o in self.offers if o["type"] == "Capitulate"]
            best_offer = min(offers, key=lambda o: abs(o["x"] - self.x))

        if best_offer:
            if best_offer["type"] == "Challenge":
                self.x = best_offer["x"]
                if self.model.verbose:
                    print self.name + " loses challenge to " + best_offer["Sender"]
                    print "\tNew position: " + str(self.x)
            elif best_offer["type"] == "Compromise":
                Ui = best_offer["Ui"]
                Uj = best_offer["Uj"]
                self.x += (best_offer["x"] - self.x) * abs(Ui / Uj)
                if self.model.verbose:
                    print self.name + " compromises with " + best_offer["Sender"]
                    print "\tNew position: " + str(self.x)
            elif best_offer["type"] == "Capitulate":
                self.x = best_offer["x"]
                if self.model.verbose:
                    print self.name + " capitulates to " + best_offer["Sender"]
                    print "\tNew position: " + str(self.x)

    # Some utility methods
    def __repr__(self):
        return self.name + str({"x": self.x, "c": self.c, "s": self.s, 
                                    "r": self.r})

    def __str__(self):
        return self.__repr__()


class Model(object):

    def __init__(self, actors, Q=1.0, verbose=True):
        '''
        Initiate a new model with pre-created actors.
        '''
        self.Q = Q
        self.verbose = verbose
        self.actors = actors
        self.actors_by_name = {}
        for actor in self.actors:
            actor.model = self
            self.actors_by_name[actor.name] = actor

        positions = self.get_positions()
        self.position_range = max(positions) - min(positions)

        self.median_positions = []
        self.mean_positions = []

    def get_positions(self):
        '''
        Returns a list of every position currently held.
        '''
        return [actor.x for actor in self.actors]

    def median_position(self):
        '''
        Find median position.
        '''
        positions = self.get_positions()
        median = positions[0]
        for position in positions[1:]:
            votes = 0
            for actor in self.actors:
                votes += actor.vote(position, median)
            if votes > 0:
                median = position
        return median

    def mean_position(self):
        top = 0
        bottom = 0
        for actor in self.actors:
            d = actor.s * actor.c
            bottom += d
            top += d * actor.x
        return top / bottom

    def update_risk_tolerance(self):
        for actor in self.actors:
            actor.calculate_r()

    def send_all_offers(self):
        for actor in self.actors:
            actor.send_offers()

    def evaluate_offers(self):
        for actor in self.actors:
            actor.choose_offer()        

    def next_step(self):
        '''
        Run one step of the model.
        '''
        self.update_risk_tolerance()
        self.send_all_offers()
        self.evaluate_offers()

    def run_model(self, n):
        '''
        Run the model for n rounds.
        '''
        median = self.median_position()
        mean = self.mean_position()

        self.median_positions.append(median)
        self.mean_positions.append(mean)
        if self.verbose:
            print "\tMedian: " + str(median)
            print "\tMean: " + str(mean)
        
        for i in range(1, n+1):
            if self.verbose:
                print "\nROUND " + str(i)
            self.next_step()

            for actor in self.actors:
                actor.r = 1
                actor.offers = []

            median = self.median_position()
            mean = self.mean_position()
            self.median_positions.append(median)
            self.mean_positions.append(mean)
            
            if self.verbose:
                print "\n\tMedian: " + str(median)
                print "\tMean: " + str(mean)
            
    
    @staticmethod
    def from_dataframe(df, col_mapping={}, Q=1.0, verbose=True):
        '''
        Load actor data from a Pandas dataframe and instantiate a model.
        '''
        name_col = col_mapping["name"] if "name" in col_mapping else "name"
        x_col = col_mapping["x"] if "x" in col_mapping else "x"
        s_col = col_mapping["s"] if "s" in col_mapping else "s"
        c_col = col_mapping["c"] if "c" in col_mapping else "c"

        actors = []
        for row in df.iterrows():
            row = row[1]
            actor = Actor(row[name_col], row[x_col], row[c_col], row[s_col])
            actors.append(actor)
        model = Model(actors, Q, verbose)
        for actor in model.actors:
            actor.model = model
        return model



    def __str__(self):
        out = ""
        for actor in self.actors:
            out += str(actor) + "\n"
        return out

    def __getitem__(self, index):
        return self.actors_by_name[index]



        


    
