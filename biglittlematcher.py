from ortools.sat.python import cp_model
import graphviz
from collections import defaultdict
from IPython.display import display
from typing import List, Dict
import time


class BigLittleMatcher:
    def __init__(self, bigs: Dict, littles: Dict, big_prefs: Dict, little_prefs: Dict):
        self.bigs = bigs
        self.littles = littles
        self.big_prefs = big_prefs
        self.little_prefs = little_prefs
        self.model = cp_model.CpModel()
        self.x = {}
        self.scores = {}
        self.max_rank_b = len(self.littles)
        self.max_rank_l = len(self.bigs)
        self.solver = cp_model.CpSolver()

    def solve(self):
        start_time = time.time()
        status = self.solver.Solve(self.model)
        if status != cp_model.OPTIMAL:
            raise ValueError('Not possible!')
        matches = [(b, l) for (b, l), var in self.x.items() if self.solver.Value(var)]
        end_time = time.time()
        return matches, self.solver.ObjectiveValue(), end_time - start_time

    def pretty_print(self):
        print(self.solver.ResponseStats())
        score_achieved = self.solver.ObjectiveValue()
        print(f"Total preference score: {score_achieved:.0f}")
        COLORS = ['aqua', 'coral', 'darkgreen', 'gold', 'darkolivegreen1',
                    'deeppink', 'crimson', 'darkorchid', 'bisque', 'yellow']
        G = graphviz.Graph()
        for (b, l), var in self.x.items():
            if self.solver.Value(var):
                # Use default penwidth of 1 if scores dict doesn't exist or doesn't have the pair
                penwidth = str(self.scores.get((b, l), 1)) if hasattr(self, 'scores') else "1"
                G.edge(f'{b}', f'{l}', penwidth=penwidth)
                G.node(f'{b}', color=COLORS[hash(b) % len(COLORS)])
                G.node(f'{l}', color=COLORS[hash(l) % len(COLORS)])
        display(G)

    def build_model(self):
        """
        Build model for classic Stable Marriage problem.
        
        This function:
        1. Creates binary variables for all possible matches between bigs and littles
        2. Adds constraints to ensure everyone is matched exactly once
        3. Adds stability constraints to ensure no blocking pairs exist:
           - For each potential pair (b,l) that's not matched, either:
             a) b must be matched with someone they prefer to l, or
             b) l must be matched with someone they prefer to b
        """
        for b in self.bigs:
            for l in self.littles:
                self.x[(b, l)] = self.model.NewBoolVar(f"x_{b}_{l}")

        for b in self.bigs:
            self.model.Add(sum(self.x[(b, l)] for l in self.littles) == 1)
        
        for l in self.littles:
            self.model.Add(sum(self.x[(b, l)] for b in self.bigs) == 1)

        for b in self.bigs:
            for l in self.littles:
                not_matched = self.model.NewBoolVar(f"not_matched_{b}_{l}")
                self.model.Add(self.x[(b, l)] == 0).OnlyEnforceIf(not_matched)
                self.model.Add(self.x[(b, l)] == 1).OnlyEnforceIf(not_matched.Not())
                
                b_with_better = self.model.NewBoolVar(f"b{b}_with_better_{l}")
                preferred_littles = [
                    l_prime for l_prime in self.littles 
                    if self.big_prefs[b].index(l_prime) < self.big_prefs[b].index(l)
                ]
                if preferred_littles:
                    self.model.Add(sum(self.x[(b, l_prime)] for l_prime in preferred_littles) >= 1).OnlyEnforceIf(b_with_better)
                    self.model.Add(sum(self.x[(b, l_prime)] for l_prime in preferred_littles) == 0).OnlyEnforceIf(b_with_better.Not())
                else:
                    self.model.Add(b_with_better == 0)
                
                l_with_better = self.model.NewBoolVar(f"l{l}_with_better_{b}")
                preferred_bigs = [
                    b_prime for b_prime in self.bigs 
                    if self.little_prefs[l].index(b_prime) < self.little_prefs[l].index(b)
                ]
                if preferred_bigs:
                    self.model.Add(sum(self.x[(b_prime, l)] for b_prime in preferred_bigs) >= 1).OnlyEnforceIf(l_with_better)
                    self.model.Add(sum(self.x[(b_prime, l)] for b_prime in preferred_bigs) == 0).OnlyEnforceIf(l_with_better.Not())
                else:
                    self.model.Add(l_with_better == 0)
                
                self.model.AddBoolOr([not_matched.Not(), b_with_better, l_with_better])

        self.model.Maximize(0)

    def build_model_smt(self):
        """
        Build a Stable Marriage model with Ties (SMT).
        
        For preferences, we use:
        - big_prefs[b][l] = rank of little l for big b (lower is better)
        - little_prefs[l][b] = rank of big b for little l (lower is better)
        - This allows for ties (multiple people with same rank)
        
        This function:
        1. Creates binary variables for all possible matches
        2. Adds constraints to ensure each participant is matched exactly once
        3. Adds stability constraints that account for ties:
           - For each potential pair (b,l) that's not matched, either:
             a) b must be matched with someone they rank equally or better than l, or
             b) l must be matched with someone they rank equally or better than b
        """
        for b in self.bigs:
            for l in self.littles:
                self.x[(b, l)] = self.model.NewBoolVar(f"x_{b}_{l}")
        
        for b in self.bigs:
            self.model.Add(sum(self.x[(b, l)] for l in self.littles) == 1)
        for l in self.littles:
            self.model.Add(sum(self.x[(b, l)] for b in self.bigs) == 1)
        
        for b in self.bigs:
            for l in self.littles:
                b_rank_of_l = self.big_prefs[b][l]
                l_rank_of_b = self.little_prefs[l][b]
                
                not_matched = self.model.NewBoolVar(f"not_matched_{b}_{l}")
                self.model.Add(self.x[(b, l)] == 0).OnlyEnforceIf(not_matched)
                self.model.Add(self.x[(b, l)] == 1).OnlyEnforceIf(not_matched.Not())
                
                b_with_better_or_equal = self.model.NewBoolVar(f"b{b}_with_geq_{l}")
                preferred_littles = [
                    l_prime for l_prime in self.littles 
                    if self.big_prefs[b][l_prime] <= b_rank_of_l
                ]
                self.model.Add(sum(self.x[(b, l_prime)] for l_prime in preferred_littles) >= 1).OnlyEnforceIf(b_with_better_or_equal)
                self.model.Add(sum(self.x[(b, l_prime)] for l_prime in preferred_littles) == 0).OnlyEnforceIf(b_with_better_or_equal.Not())
                
                l_with_better_or_equal = self.model.NewBoolVar(f"l{l}_with_geq_{b}")
                preferred_bigs = [
                    b_prime for b_prime in self.bigs 
                    if self.little_prefs[l][b_prime] <= l_rank_of_b
                ]
                self.model.Add(sum(self.x[(b_prime, l)] for b_prime in preferred_bigs) >= 1).OnlyEnforceIf(l_with_better_or_equal)
                self.model.Add(sum(self.x[(b_prime, l)] for b_prime in preferred_bigs) == 0).OnlyEnforceIf(l_with_better_or_equal.Not())
                
                self.model.AddBoolOr([not_matched.Not(), b_with_better_or_equal, l_with_better_or_equal])
        
        self.model.Maximize(0)

    def build_model_smti(self):
        """
        Build a Stable Marriage model with Ties and Incomplete lists (SMTI).
        
        For preferences, instead of lists, we use:
        - big_prefs[b][l] = rank of little l for big b (lower is better)
        - little_prefs[l][b] = rank of big b for little l (lower is better)
        - Missing entries indicate unranked participants
        
        This function:
        1. Creates binary variables for all possible matches
        2. Adds constraints to ensure each participant is matched at most once
        3. Only considers stability for pairs where both participants rank each other
        4. Adds stability constraints with ties:
           - For each potential pair (b,l) that's not matched, either:
             a) b must be matched with someone they rank equally or better than l, or
             b) l must be matched with someone they rank equally or better than b
        """
        for b in self.bigs:
            for l in self.littles:
                self.x[(b, l)] = self.model.NewBoolVar(f"x_{b}_{l}")
        
        for b in self.bigs:
            self.model.Add(sum(self.x[(b, l)] for l in self.littles) <= 1)
        for l in self.littles:
            self.model.Add(sum(self.x[(b, l)] for b in self.bigs) <= 1)
        
        for b in self.bigs:
            for l in self.littles:
                b_rank_of_l = self.big_prefs.get(b, {}).get(l, self.max_rank_b)
                l_rank_of_b = self.little_prefs.get(l, {}).get(b, self.max_rank_l)
                
                if b_rank_of_l == self.max_rank_b or l_rank_of_b == self.max_rank_l:
                    continue
                    
                not_matched = self.model.NewBoolVar(f"not_matched_{b}_{l}")
                self.model.Add(self.x[(b, l)] == 0).OnlyEnforceIf(not_matched)
                self.model.Add(self.x[(b, l)] == 1).OnlyEnforceIf(not_matched.Not())
                
                b_with_better_or_equal = self.model.NewBoolVar(f"b{b}_with_geq_{l}")
                preferred_littles = [
                    l_prime for l_prime in self.littles 
                    if self.big_prefs.get(b, {}).get(l_prime, self.max_rank_b) <= b_rank_of_l
                ]
                self.model.Add(sum(self.x[(b, l_prime)] for l_prime in preferred_littles) >= 1).OnlyEnforceIf(b_with_better_or_equal)
                self.model.Add(sum(self.x[(b, l_prime)] for l_prime in preferred_littles) == 0).OnlyEnforceIf(b_with_better_or_equal.Not())
                
                l_with_better_or_equal = self.model.NewBoolVar(f"l{l}_with_geq_{b}")
                preferred_bigs = [
                    b_prime for b_prime in self.bigs 
                    if self.little_prefs.get(l, {}).get(b_prime, self.max_rank_l) <= l_rank_of_b
                ]
                self.model.Add(sum(self.x[(b_prime, l)] for b_prime in preferred_bigs) >= 1).OnlyEnforceIf(l_with_better_or_equal)
                self.model.Add(sum(self.x[(b_prime, l)] for b_prime in preferred_bigs) == 0).OnlyEnforceIf(l_with_better_or_equal.Not())
                
                self.model.AddBoolOr([not_matched.Not(), b_with_better_or_equal, l_with_better_or_equal])
        
        self.model.Maximize(0)

    def build_model_optimize(self, preference_weight: float = 0.5, enforce_exactly_one: bool = False):
        #x[(b, l)] is 1 if big b is matched with little l
        for b in self.bigs:
            for l in self.littles:
                self.x[(b, l)] = self.model.NewBoolVar(f"x_{b}_{l}")
        
        for l in self.littles:
            vars_l = [self.x[(b, l)] for b in self.bigs]
            # each little must be matched to exactly one big
            if enforce_exactly_one:
                self.model.Add(sum(vars_l) == 1)
            # there are twins
            else:
                self.model.Add(sum(vars_l) >= 1)
                self.model.Add(sum(vars_l) <= self.littles[l].get('max', 1))

        for b in self.bigs:
            vars_b = [self.x[(b, l)] for l in self.littles]
            # if exact matching
            if enforce_exactly_one:
                self.model.Add(sum(vars_b) == 1)
            # each big must be matched to at least one little
            # and no more than their max
            else:
                self.model.Add(sum(vars_b) >= 1)
                self.model.Add(sum(vars_b) <= self.bigs[b].get('max', 1))

        for b in self.bigs:
            for l in self.littles:
                # lower rank means higher preference
                # assigns max_rank to unranked people
                rank_b = self.big_prefs.get(b, []).index(l) if l in self.big_prefs.get(b, []) else self.max_rank_b
                rank_l = self.little_prefs.get(l, []).index(b) if b in self.little_prefs.get(l, []) else self.max_rank_l

                score = (
                    preference_weight * (self.max_rank_b - rank_b)
                    + (1 - preference_weight) * (self.max_rank_l - rank_l)
                )
                self.scores[(b, l)] = score

        self.model.Maximize(sum(self.scores[(b, l)] * self.x[(b, l)] for (b, l) in self.x))

    def check_instabilities(self, matches):
        if not matches:
            return []
            
        # Check the type of preference structure we're using
        first_big = list(self.big_prefs.keys())[0]
        if isinstance(self.big_prefs[first_big], list):
            return self._check_instabilities_list_prefs(matches)
        else:
            return self._check_instabilities_dict_prefs(matches)
    
    def _check_instabilities_list_prefs(self, matches):
        """Check for instabilities in list-based preference structure (standard SMP)"""
        instabilities = []
        big_to_little = {b: l for b, l in matches}
        little_to_big = {l: b for b, l in matches}
        
        for b in self.big_prefs:
            for l in self.big_prefs[b]:
                # Skip if this is their match
                if big_to_little.get(b) == l:
                    continue
                    
                b_matched_l = big_to_little.get(b)
                l_matched_b = little_to_big.get(l)
                
                # Both must be matched to check for instability
                if not b_matched_l or not l_matched_b:
                    continue
                
                # Check preferences
                b_prefers_l = self.big_prefs[b].index(l) < self.big_prefs[b].index(b_matched_l)
                l_prefers_b = self.little_prefs[l].index(b) < self.little_prefs[l].index(l_matched_b)
                
                if b_prefers_l and l_prefers_b:
                    instabilities.append((b, l))
        
        return instabilities
    
    def _check_instabilities_dict_prefs(self, matches):
        """Check for instabilities in dictionary-based preference structure (SMT/SMTI)"""
        instabilities = []
        big_to_little = {b: l for b, l in matches}
        little_to_big = {l: b for b, l in matches}
        
        for b, l in self._get_all_potential_pairs(big_to_little, little_to_big):
            if self._is_instability(b, l, big_to_little, little_to_big):
                instabilities.append((b, l))
                
        return instabilities
    
    def _get_all_potential_pairs(self, big_to_little, little_to_big):
        """Generate potential blocking pairs to check"""
        pairs = []
        for b in self.big_prefs:
            if b not in big_to_little:
                continue
                
            for l in self.little_prefs:
                if l not in little_to_big or l == big_to_little[b]:
                    continue
                    
                pairs.append((b, l))
        return pairs
    
    def _is_instability(self, b, l, big_to_little, little_to_big):
        """Check if (b,l) is a blocking pair based on their current matches"""
        b_matched_l = big_to_little.get(b)
        l_matched_b = little_to_big.get(l)
        
        # Get ranks (infinity if not ranked)
        b_matched_rank = self.big_prefs.get(b, {}).get(b_matched_l, float('inf'))
        l_matched_rank = self.little_prefs.get(l, {}).get(l_matched_b, float('inf'))
        
        b_rank_of_l = self.big_prefs.get(b, {}).get(l, float('inf'))
        l_rank_of_b = self.little_prefs.get(l, {}).get(b, float('inf'))
        
        # They form a blocking pair if both prefer each other to current match
        return b_rank_of_l < b_matched_rank and l_rank_of_b < l_matched_rank
