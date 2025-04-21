class GaleShapley:
    
    def __init__(self, proposers_prefs, receivers_prefs):
        self.proposers_prefs = proposers_prefs
        self.receivers_prefs = receivers_prefs
        
        self.proposers = list(proposers_prefs.keys())
        self.receivers = list(receivers_prefs.keys())
        
        # Precomputing these rankings will help us make the actually matching process faster
        self.receivers_rankings = {}
        for receiver, prefs in self.receivers_prefs.items():
            self.receivers_rankings[receiver] = {
                proposer: rank for rank, proposer in enumerate(prefs)
            }
    
    def match(self):
        free_proposers = self.proposers.copy()
        
        current_matches = {}
        
        # This keeps track of who each proposer is currently proposing to
        next_proposals = {proposer: 0 for proposer in self.proposers}
        
        while free_proposers:
            proposer = free_proposers.pop(0)
            
            if next_proposals[proposer] >= len(self.proposers_prefs[proposer]):
                continue
            
            receiver = self.proposers_prefs[proposer][next_proposals[proposer]]
            next_proposals[proposer] += 1
            
            if receiver not in current_matches:
                current_matches[receiver] = proposer
            else:
                current_proposer = current_matches[receiver]
                
                if (self.receivers_rankings[receiver][proposer] < 
                    self.receivers_rankings[receiver][current_proposer]):
                    current_matches[receiver] = proposer
                    free_proposers.append(current_proposer)
                else:
                    free_proposers.append(proposer)
        
        return [(proposer, receiver) for receiver, proposer in current_matches.items()]

