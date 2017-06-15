from decimal import *

SPLIT_ACES = 2

SPADE = 0

# Specific rules
OBO = False
OBBO = False
BB1 = False
ENHC = True

HIT_SOFT17 = False
EARLY_SURRENDER = True
REDOUBLE = True

NO_ACTION = -1
STAND = 0
HIT = 1
DOUBLE = 2
SPLIT = 3
SPLIT_FREE = 4
SURRENDER = 5

dp = {}

basic_strategy_hard = [[{} for i in range(22)] for i in range(11)]
basic_strategy_soft = [[{} for i in range(22)] for i in range(11)]
basic_strategy_split = [[{} for i in range(11)] for i in range(11)]
basic_strategy_double = [[{} for i in range(22)] for i in range(11)]
basic_strategy_double_soft = [[{} for i in range(22)] for i in range(11)]

class Hand(object):
    def __init__(self, card, splits_remaining = 1, was_split = False):
        self.score = (card-1)%10 + 1
        self.soft = card == 1
        self.score += 10 * self.soft
        self.busted = False
        self.doubled = 0
        self.n_cards = 1
        self.can_split = False
        self.splits_remaining = splits_remaining
        self.surrendered = False
        self.was_split = was_split if card != 1 else SPLIT_ACES if was_split else False

    def copy(self):
        h = Hand(0)
        h.score, h.soft, h.busted, h.doubled, h.n_cards, h.can_split, h.splits_remaining, h.surrendered, h.was_split = self.serialize() 
        return h

    def can_stand(self):
        # if, after splitting you have one card, you must hit to get two.
        if self.busted or self.score == 21 or self.n_cards < 2:
            return False
        return True

    def can_hit(self):
        return self.score != 21 and not self.busted and not self.doubled and (self.was_split != SPLIT_ACES or self.n_cards != 2)

    def hit(self, card):
        assert(int(card) == card)
        card = int(card)
        self = self.copy()
        if ((card-1)%10 + 1 == self.score or (card == 1 and self.score == 11)) and self.n_cards == 1 and self.splits_remaining > 0:
            self.can_split = True
        else:
            self.can_split = False
        self.score += (card-1)%10+1
        if card == 1 and not self.soft:
            self.score += 10
            self.soft = True
        self.n_cards = min(7, self.n_cards+1)
        if self.score > 21:
            if self.soft:
                self.score -= 10
                self.soft = False
            else:
                self.busted = True
        return self

    def can_double(self):
        # Must have at least 2 cards. 1 card is possible after splitting.
        return ((self.n_cards == 2 and self.doubled == 0) or (self.n_cards == 3 and self.doubled == 1 and REDOUBLE)) and self.was_split != SPLIT_ACES

    def double(self, card):
        assert(int(card) == card)
        self = self.copy()
        self.can_split = False
        card = int(card)
        self = self.copy()
        self.n_cards += 1
        self.score += (card-1)%10+1
        if card == 1 and self.score <= 11:
            self.score += 10
            self.soft = True
        if self.score > 21 and self.soft:
            self.soft = False
            self.score -= 10
        if self.score > 21:
            self.busted = True
        self.doubled += 1
        return self

    def surrender(self):
        self = self.copy()
        self.surrendered = True
        return self

    def can_surrender(self, dealer_card):
        if self.n_cards == 2 and self.was_split == False and dealer_card != 1:
            return True
        return False

    def has_surrendered(self):
        return self.surrendered

    def get_score(self):
        return self.score

    def is_busted(self):
        return self.busted

    def split(self):
        assert(self.score % 2 == 0)
        hand = self.score / 2
        if self.soft:
            hand = 1
        return (Hand(hand, self.splits_remaining - 1, True), Hand(hand, self.splits_remaining-1, True))

    def is_blackjack(self):
        if self.n_cards == 2 and not self.was_split and self.score == 21:
            return True
        return False

    def get_stake(self):
        return [(1.)*(1), (1.)*(2), 3.][self.doubled]

    def serialize(self):
        return (self.score, self.soft, self.busted, self.doubled, self.n_cards, self.can_split, self.splits_remaining, self.surrendered, self.was_split)

    def get_hash(self):
        return self.serialize()
        if self.busted:
            return (False,)

        h = (self.score, self.doubled)
        if self.doubled:
            h += (self.surrendered,)
        else:
            h += (self.n_cards,)
            if self.score != 21:
                h += (self.soft,)
            if self.n_cards == 2:
                h += (self.surrendered,)
            if self.n_cards == 2 and not self.surrendered and self.score != 21:
                h += (self.can_split, self.splits_remaining, self.was_split)

        return h

    def __str__(self):
        return repr(self.serialize())

cards = zip(range(1, 10), [1./13]*9) + [(10, 4./13)]

"""
cards[1] = cards[1][0], cards[0][1] - 1./52/4
cards[3] = cards[3][0], cards[3][1] - 2./52/4
for i in [0, 2, 4, 5, 6, 7, 8, 9]:
    cards[i] = cards[i][0], cards[i][1] + 3./52/4/8
   """ 
ranks = list(cards)

def showdown(dealer_card, hands, dp):
    if dealer_card not in dp:
        # Note that only the first hand can be the original bet.
        # calculate dealer totals and their probabilities
        soft = dealer_card == 1
        tot = dealer_card if dealer_card != 1 else 11
        probs = [[0] * 22, [0] * 22]
        probs[soft][tot] = (1.)*(1)
        card_n = 1
        while True:
            card_n += 1
            updates = 0
            newprobs = [[0] * 22, [0] * 22]
            # Bust probs
            newprobs[0][0] = probs[0][0] # Bust index is 0, 0. Hack.
            newprobs[1][0] = probs[1][0] # Dealer blackjack index is 1, 0. Hack.
            # Hit probs
            for tot in range(2, 18):
                for soft in [0, 1]:
                    if tot != 17 or (soft and HIT_SOFT17):
                        if probs[soft][tot]: updates += 1
                        for value, likelihood in ranks:
                            newtot = value + tot
                            newsoft = soft
                            if not newsoft and value == 1:
                                newsoft = True
                                newtot += 10
                            if newtot > 21 and newsoft:
                                newtot -= 10
                                newsoft = False
                            if newtot > 21:
                                newprobs[0][0] += likelihood * probs[soft][tot]
                            elif newtot == 21 and card_n == 2:
                                newprobs[1][0] += likelihood * probs[soft][tot]
                            else:
                                newprobs[newsoft][newtot] += likelihood * probs[soft][tot]
            # stand
            for tot in range(17, 22):
                for soft in [0, 1]:
                    if tot == 17 and soft and HIT_SOFT17:
                        continue
                    newprobs[soft][tot] += probs[soft][tot]
            probs = newprobs
            if updates == 0:
                break
        dp[dealer_card] = probs
        check = sum(probs[0]) + sum(probs[1]) 
        if abs(check-1) > 1e-5:
            print check
            print probs
            print dealer_card, map(str, hands)
            raw_input()
    probs = dp[dealer_card]
    dealer_bust_p = probs[0][0]
    dealer_blackjack_p = probs[1][0]
    
    #print dealer_bust_p, dealer_blackjack_p
    #print probs[0][17:]
    #print probs[1][17:]
    #raw_input()

    totev = 0

    # Resolve dealer blackjack
    live_bets = 0
    live_hands = 0
    blackjack_hands = 0
    busted_bets = 0
    surrendered_bets = 0
    for i in hands:
        if i.has_surrendered():
            surrendered_bets += 0.5
        elif i.is_blackjack():
            blackjack_hands += 1
        elif not i.is_busted:
            live_hands += 1
            live_bets += i.get_stake()
        else:
            busted_bets += i.get_stake()
    totev += surrendered_bets * dealer_blackjack_p
    totev += blackjack_hands * dealer_blackjack_p
    if OBO: # Note: no such thing.
        if hands[0].get_score() == 21:
            totev += (live_bets) * dealer_blackjack_p
        else:
            totev += (live_bets-1) * dealer_blackjack_p
    elif OBBO:
        totev += (live_bets - live_hands) * dealer_blackjack_p
    elif BB1:
        totev += max(0, live_bets - busted_bets - 1) * dealer_blackjack_p
    elif ENHC:
        totev += 0
    
    # Resolve dealer bust
    for i in hands:
        if not i.is_busted():
            if i.has_surrendered():
                totev += i.get_stake() * 0.5 * dealer_bust_p
                if i.get_stake() != 1:
                    raw_input("kek")
            elif i.is_blackjack():
                totev += i.get_stake() * 2.5 * dealer_bust_p
            else:
                totev += i.get_stake() * 2 * dealer_bust_p

    
    # Resolve all others
    sum_p = dealer_bust_p + dealer_blackjack_p
    for i in range(17, 22):
        p = probs[0][i] + probs[1][i]
        sum_p += p
        for j in hands:
            if j.has_surrendered():
                totev += j.get_stake() * 0.5 * p
            elif j.is_busted():
                totev += 0
            elif j.is_blackjack():
                totev += j.get_stake() * 2.5 * p
            else:
                if j.get_score() == i:
                    totev += j.get_stake() * p
                elif j.get_score() > i:
                    totev += j.get_stake() * 2 * p
    
    if abs(sum_p-1) > 0.001:
        print sum_p, dealer_card, hands
        raw_input()
    return totev
        
                        

def get_edge(dealer_card, hands, hand_i, mydp = None):
    #print dealer_card, map(str, hands), hand_i
    global dp
    if mydp == None:
        mydp = dp
    key = (dealer_card, tuple(map(lambda a: a.get_hash(), hands)), hand_i)

    if key not in dp:
        if hand_i == len(hands):
            dp[key] = (showdown(dealer_card, hands, mydp), NO_ACTION)
        else:
            # resolve busts
            if hands[hand_i].is_busted():
                best = (get_edge(dealer_card, hands, hand_i + 1, mydp)[0], NO_ACTION)
            else:
                best = (-1e20, None)
                # try stand
                if hands[hand_i].can_stand():
                    best = max(best, (get_edge(dealer_card, hands, hand_i + 1, mydp)[0], STAND))
                # try hit
                if hands[hand_i].can_hit():
                    tot_ev = (1.)*(0)
                    for i, likelihood in cards:
                        newhand = hands[hand_i].hit(i)
                        ev = get_edge(dealer_card, hands[:hand_i] + [newhand] + hands[hand_i+1:], hand_i, mydp)[0]
                        tot_ev += likelihood * ev
                    if hands[hand_i].score == 5 and dealer_card == 5 and hands[hand_i].doubled==0:
                        print tot_ev, HIT
                    best = max(best, (tot_ev, HIT))
                # try double
                if hands[hand_i].can_double():
                    tot_ev = (1.)*(0)
                    for i, likelihood in cards:
                        newhand = hands[hand_i].double(i)
                        ev = -1 + get_edge(dealer_card, hands[:hand_i] + [newhand] + hands[hand_i+1:], hand_i, mydp)[0]
                        tot_ev += likelihood * ev
                    if hands[hand_i].score == 5 and dealer_card == 5 and hands[hand_i].doubled == 0:
                        print tot_ev, DOUBLE
                        raw_input()
                    best = max(best, (tot_ev, DOUBLE))
                # try split
                if hands[hand_i].can_split:
                    original, split = hands[hand_i].split()
                    ev = -1 + get_edge(dealer_card, hands[:hand_i] + [original] + hands[hand_i+1:], hand_i, mydp)[0]
                    ev += get_edge(dealer_card, hands[:hand_i] + [split] + hands[hand_i+1:], hand_i, mydp)[0]
                    #ev = -1 + get_edge(dealer_card, hands[:hand_i] + [original, split] + hands[hand_i+1:], hand_i, mydp)[0]
                    best = max(best, (ev, SPLIT))
                # try stand
                best = max(best, (get_edge(dealer_card, hands, hand_i + 1, mydp)[0], STAND))
                # try surrender
                if hands[hand_i].can_surrender(dealer_card):
                    newhand = hands[hand_i].surrender()
                    ev = get_edge(dealer_card, hands[:hand_i] + [newhand] + hands[hand_i+1:], hand_i + 1, mydp)[0]
                    best = max(best, (ev, SURRENDER))

                s = []
                if hands[hand_i].can_hit() or hands[hand_i].can_double():
                    if hands[hand_i].doubled == 1:
                        if hands[hand_i].soft:
                            s.append(basic_strategy_double_soft[dealer_card][hands[hand_i].get_score()])
                        else:
                            s.append(basic_strategy_double[dealer_card][hands[hand_i].get_score()])
                    else:
                        if hands[hand_i].soft:
                            s.append(basic_strategy_soft[dealer_card][hands[hand_i].get_score()])
                        if hands[hand_i].can_split:
                            s.append(basic_strategy_split[dealer_card][hands[hand_i].get_score()/2 if not hands[hand_i].soft else 1])
                        if not hands[hand_i].soft and best[1] != SPLIT and best[1] != SPLIT_FREE:
                            s.append(basic_strategy_hard[dealer_card][hands[hand_i].get_score()])
                    for i in s:
                        i[best[1]] = i.get(best[1], 0) + 1

            dp[key] = best
    return dp[key]

def print_chart(chart, name, rng):
    print name, "________________"
    for i in ["____"] + range(2, 11) + ["A"]:
        print i, "\t",
    print
    for i in rng:
        print i, "\t",
        for j in range(2, 11) + [1]:
            print ",".join(map(lambda a: ['s','h','d','p','P','r'][a] + str(chart[j][i][a]),chart[j][i].keys())), "\t",
        print
    print

if __name__ == "__main__":
    print "computing best plays and displaying borderline cases"
    totev = (1.)*(0)
    for hole, p1 in ranks:
        for c1, l1 in cards:
            for c2, l2 in cards:
                ev = get_edge(hole, [Hand(c1).hit(c2)], 0)
                totev += ev[0] * p1 * l1 * l2
                if c1/10 == c2/10 == 0:
                    print hole, (c1-1)%10+1 + (c2-1)%10+1 + (10 if c1 == 1 or c2 == 1 else 0), c1, c2, ["stand", "hit", "double", "split", "splat", "surrender"][ev[1]], ev[0], c1/10, c2/10
        print "Done for hole card", hole
    print "Done. Total ev:", totev

    print_chart(basic_strategy_hard, "Hard", range(2, 21))
    print_chart(basic_strategy_soft, "Soft", range(11, 21))
    print_chart(basic_strategy_split, "Splits", range(2, 11) + [1])
    print_chart(basic_strategy_double, "Redouble", range(2, 21))
    print_chart(basic_strategy_double_soft, "Redouble soft", range(2, 21))

    cardA = int(raw_input("first player card:"))
    h = Hand(cardA)
    while True:
        card = int(raw_input("next card:"))
        if card == 0:
            break
        h = h.hit(card)
    cardC = int(raw_input("dealer card:"))
    print get_edge(cardC, [h], 0)
