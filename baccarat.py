
banker_draw = [
        range(10),
        range(10),
        range(10),
        [0, 1, 2, 3, 4, 5, 6, 7, 9],
        [2, 3, 4, 5, 6, 7],
        [4, 5, 6, 7],
        [6, 7],
        [],
        [],
        []
]

def odds(dist):
    totalprob = 0
    tie, player, banker = 0, 0, 0
    prob = 1.
    for p1 in range(0, 10):
        if dist[p1] == 0: continue
        prob *= dist[p1] / sum(dist)
        dist[p1] -= 1
        for p2 in range(0, 10):
            if dist[p2] == 0: continue
            prob *= dist[p2] / sum(dist)
            dist[p2] -= 1
            for b1 in range(0, 10):
                if dist[b1] == 0: continue
                prob *= dist[b1] / sum(dist)
                dist[b1] -= 1
                for b2 in range(0, 10):
                    if dist[b2] == 0: continue
                    prob *= dist[b2] / sum(dist)
                    dist[b2] -= 1
                    p = (p1+p2)%10
                    b = (b1+b2)%10
                    
                    if p < 6 and b < 8:
                        # player draw
                        
                        for p3 in range(0, 10):
                            if dist[p3] == 0: continue
                            prob *= dist[p3] / sum(dist)
                            dist[p3] -= 1
                            P = (p+p3)%10

                            if p3 in banker_draw[b]:
                                for b3 in range(0, 10):
                                    if dist[b3] == 0: continue
                                    prob *= dist[b3] / sum(dist)
                                    dist[b3] -= 1
                                    
                                    B = (b+b3)%10
                                    if P > B: player += prob
                                    elif B > P: banker += prob
                                    else: tie += prob
                                    totalprob += prob

                                    dist[b3] += 1
                                    if sum(dist) == 0:
                                        print dist
                                    if dist[b3] == 0:
                                        print b3, dist
                                    prob /= dist[b3] / sum(dist)
                            else:
                                if P > b: player += prob
                                elif b > P: banker += prob
                                else: tie += prob
                                totalprob += prob

                            dist[p3] += 1
                            prob /= dist[p3] / sum(dist)

                    elif b < 6 and p < 8:
                        # banker draw only
                        for b3 in range(0, 10):
                            if dist[b3] == 0: continue
                            prob *= dist[b3] / sum(dist)
                            dist[b3] -= 1
                            
                            B = (b+b3)%10
                            if p > B: player += prob
                            elif B > p: banker += prob
                            else: tie += prob
                            totalprob += prob

                            dist[b3] += 1
                            prob /= dist[b3] / sum(dist)
                    else:
                        if p > b: player += prob
                        elif b > p: banker += prob
                        else: tie += prob
                        totalprob += prob
                    

                    dist[b2] += 1
                    prob /= dist[b2] / sum(dist)
                dist[b1] += 1
                prob /= dist[b1] / sum(dist)
            dist[p2] += 1
            prob /= dist[p2] / sum(dist)
        dist[p1] += 1
        prob /= dist[p1] / sum(dist)
    return (player, banker, tie)

if __name__=="__main__":
    import random
    print odds([400.] + [100.]*9)
    
    profit = 0
    cut = 8
    for i in range(100):
        thisshoe = 0
        dist = [16*6.] + [4*6.] * 9
        for j in range(52*6 - cut):
            key = random.randint(1, sum(dist))
            for num in range(10):
                key -= dist[num]
                if key <= 0:
                    dist[num] -= 1
                    break
            if j % 4 == 0 and j > 52*5:
                p, b, t = odds(dist)
                print p, b, t
                thisshoe += max(0, p * 2 + t * 1 - 1)
                thisshoe += max(0, b * 2 - b * 0.05 + t * 1 - 1)
                thisshoe += max(0, t * 9 - 1)
        print thisshoe
        profit += thisshoe
    print profit
    
                
