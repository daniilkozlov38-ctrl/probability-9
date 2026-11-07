"""Independent exact-arithmetic and finite-outcome checks for lesson answers."""
from fractions import Fraction as F
from itertools import product, combinations
from math import comb
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
CHECKS = {}


def check(key, actual, expected):
    assert actual == expected, (key, actual, expected)
    CHECKS[key] = str(actual)


def probability(space, predicate):
    return F(sum(bool(predicate(outcome)) for outcome in space), len(space))


coins = list(product('ОР', repeat=2))
dice = list(product(range(1, 7), repeat=2))

check('random-events/problems/1', all(F(1, n) * n == 1 for n in range(1, 101)), True)
check('random-events/problems/2', tuple(probability(coins, lambda x, k=k: x.count('О') == k) for k in range(3)), (F(1, 4), F(1, 2), F(1, 4)))
check('random-events/problems/3', (len(dice), len(list(product(range(6), repeat=3)))), (36, 216))
check('random-events/homework/1', tuple(1-p-(F(4,5)-p) for p in [F(0), F(1,10), F(4,5)]), (F(1,5),)*3)
book = json.loads((ROOT/'tests/math-fixtures.json').read_text())
known = [F(value) for value in book['tables']['dice-probabilities']['rows'][1][1:] if value != '?']
check('random-events/homework/2', 1-sum(known), F(1,6))
check('random-events/homework/3', (len(list(product('ЗС', repeat=3))), F(1,2**3)), (8,F(1,8)))
check('random-events/homework/4', (len(list(product('ЗСК', repeat=3))), F(1,3**3)), (27,F(1,27)))

check('addition-of-probabilities/problems/1', F(3,4+8+3), F(1,5))
check('addition-of-probabilities/problems/2', F(10-6,10), F(2,5))
check('addition-of-probabilities/problems/3', (probability(coins,lambda x:'Р'in x),probability(coins,lambda x:x[0]=='О')), (F(3,4),F(1,2)))
x,y,z=F(1,10),F(3,10),F(3,5)
check('addition-of-probabilities/problems/4', (x+y,x+z,x+y+z), (F(2,5),F(7,10),F(1)))
andrey,draw,unfinished=F(3,10),F(1,5),F(1,10)
boris=1-andrey-draw-unfinished
check('addition-of-probabilities/homework/1', (andrey+draw+unfinished,boris+draw+unfinished,draw+unfinished), (F(3,5),F(7,10),F(3,10)))
check('addition-of-probabilities/homework/2', F(13,13+2+5), F(13,20))
target_rows=book['tables']['target-probabilities']['rows']
target=[F(x.replace(',','.')) for row in (target_rows[1],target_rows[3]) for x in row[1:]]
assert sum(target)==1
sets=[{1,2,3,4},{8,9,10},{4,8},{2,3,4,6,7,8,10}]
check('addition-of-probabilities/homework/3', tuple(sum(target[z-1] for z in selected) for selected in sets), (F(13,1000),F(763,1000),F(249,1000),F(161,250)))
check('addition-of-probabilities/homework/4', 1-F(83,100), F(17,100))
check('addition-of-probabilities/homework/5', tuple(probability(list(range(1,7)),f) for f in [lambda x:x%2==0,lambda x:x%3==0,lambda x:x>3,lambda x:x%7==0]), (F(1,2),F(1,3),F(1,2),F(0)))

check('equally-likely-outcomes/problems/1', F(3,10), F(3,10))
check('equally-likely-outcomes/problems/2', probability(dice,lambda x:sum(x)in(4,7)), F(1,4))
check('equally-likely-outcomes/problems/3', probability(dice,lambda x:sum(x)in(3,4,5)), F(1,4))
check('equally-likely-outcomes/problems/4', probability(list(product('ОР',repeat=3)),lambda x:x.count('О')==2), F(3,8))
check('equally-likely-outcomes/problems/5', probability(dice,lambda x:x[0]!=x[1]), F(5,6))
check('equally-likely-outcomes/problems/6', 1-F(19,100), F(81,100))
check('equally-likely-outcomes/problems/7', (F(100,108),round(float(F(100,108)),2)), (F(25,27),.93))
check('equally-likely-outcomes/problems/8', F(20-3,20), F(17,20))
check('equally-likely-outcomes/problems/9', F(50-27,50), F(23,50))
for n,expected,nonadjacent,key in [(5,F(1,2),False,10),(9,F(3,4),True,11)]:
    seats=list(combinations(range(n),2))
    result=probability(seats,lambda x: ((x[1]-x[0])in(1,n-1)) != nonadjacent)
    check(f'equally-likely-outcomes/problems/{key}',result,expected)
money=[1]*7+[2]*5+[5]*6+[10]*2
check('equally-likely-outcomes/problems/12', (sum(money),probability(money,lambda coin:sum(money)-coin<60)), (67,F(1,10)))

families=list(product('МД',repeat=2))
girls=[f for f in families if 'Д'in f]
check('conditional-probability/theory/1', (probability(families,lambda f:f==('Д','Д')),probability(girls,lambda f:f==('Д','Д'))), (F(1,4),F(1,3)))
check('conditional-probability/theory/2', (F(5,6)**2,F(5,6)*F(1,6),F(5,6)*F(4,5),F(5,6)*F(1,5)), (F(25,36),F(5,36),F(2,3),F(1,6)))
check('conditional-probability/problems/1', F(21,100)/F(3,10), F(7,10))
check('conditional-probability/problems/2', F(7,100)*F(3,5), F(21,500))
check('conditional-probability/problems/3', probability(list(product(range(6),repeat=5)),lambda x:len(set(x))==5), F(5,54))
tails=[c for c in coins if c[0]=='Р']
check('conditional-probability/homework/1', (probability(tails,lambda c:c==('Р','Р')),probability(tails,lambda c:'О'in c),probability(tails,lambda c:c==('О','О'))), (F(1,2),F(1,2),F(0)))
nine=[x for x in dice if sum(x)==9]
check('conditional-probability/homework/2', tuple(probability(nine,f) for f in [lambda x:x[0]==5,lambda x:4 in x,lambda x:x[0]<x[1],lambda x:x[1]<3]), (F(1,4),F(1,2),F(1,2),F(0)))
check('conditional-probability/homework/3', F(5,100)/F(2,5), F(1,8))
check('conditional-probability/homework/4', (probability(list(product(range(6),repeat=6)),lambda x:len(set(x))==6), probability(list(product(range(6),repeat=7)),lambda x:len(set(x))==7)), (F(5,324),F(0)))
failure=lambda n:F(2*comb(20,n),comb(40,n))
minimum=next(n for n in range(2,21) if 1-failure(n)>=F(19,20))
check('conditional-probability/homework/5', (minimum,failure(4),failure(5)), (5,F(51,481),F(68,1443)))

empty,fixed=set(),{0}
check('independent-events/theory/2', (F(len(empty&fixed),len(fixed)),len(empty)), (F(0),0))
universe=set(range(6))
check('independent-events/theory/3', all(len(universe&set(b))==len(b) and len(empty&set(b))==0 for count in range(7) for b in combinations(universe,count)),True)
a=lambda x:x[0]>3
b=lambda x:x[1]<3
check('independent-events/problems/1', (probability(dice,a),probability(dice,b),probability(dice,lambda x:a(x)and b(x))), (F(1,2),F(1,3),F(1,6)))
a=lambda x:sum(x)%3==0
b=lambda x:sum(x)%2==0
check('independent-events/problems/2', (probability(dice,a),probability(dice,b),probability(dice,lambda x:a(x)and b(x))), (F(1,3),F(1,2),F(1,6)))
check('independent-events/problems/3', F(5,100)*F(9,10)+F(95,100)*F(1,100), F(109,2000))
check('independent-events/problems/4', (1-F(6,100))**2, F(2209,2500))
check('independent-events/problems/5', (1-F(3,10))**3, F(343,1000))
check('independent-events/problems/6', 1-F(3,10)**2, F(91,100))
check('independent-events/homework/1', F(45,100)*F(3,100)+F(55,100)*F(1,100), F(19,1000))
check('independent-events/homework/2', 1-F(5,100)**2, F(399,400))
check('independent-events/homework/3', F(97,100)-F(87,100), F(1,10))
check('independent-events/homework/4', ((F(97,100)-F(87,100))/F(97,100),F(97,100)*F(13,100)), (F(10,97),F(1261,10000)))

colours=list(product('ЧСБ',repeat=2))
A={x for x in colours if x[0]=='Б'};B={x for x in colours if x[1]=='Б'}
check('addition-of-probabilities/theory/example', (A&B,len(A|B)), ({('Б','Б')},5))

# Verify identities and zero-probability boundary cases independently over all
# events of several finite probability spaces.
identity_cases=0
for weights in [(1,1,1,1),(0,1,2,3),(0,0,1,0)]:
    omega=set(range(len(weights)));total=sum(weights)
    mass=lambda event: F(sum(weights[i] for i in event),total)
    events=[set(c) for size in range(5) for c in combinations(omega,size)]
    assert mass(set())==0 and mass(omega)==1
    for A in events:
        assert mass(A)+mass(omega-A)==1
        for B in events:
            pa,pb,pab=mass(A),mass(B),mass(A&B)
            assert mass(A|B)==pa+pb-pab
            if pb>0:
                assert (pab/pb==pa)==(pab==pa*pb)
            if pab==pa*pb:
                assert mass(A&(omega-B))==pa*(1-pb)
                assert mass((omega-A)&B)==(1-pa)*pb
                assert mass((omega-A)&(omega-B))==(1-pa)*(1-pb)
            identity_cases+=1
check('independent-events/theory/1',identity_cases,768)
check('addition-of-probabilities/theory/exercise',F(0),F(0))

# Practice lesson: independent finite models and exact arithmetic.
check('problem-solving-practice/problems/1', 1-F(81,100), F(19,100))
check('problem-solving-practice/problems/2', 1-F(965,1000), F(7,200))
pairs=list(product(range(100),repeat=2))
check('problem-solving-practice/problems/3', probability(pairs,lambda p:p[0]>=6 and p[1]>=6), F(2209,2500))
check('problem-solving-practice/problems/4', probability(pairs,lambda p:p[0]<52 and p[1]<30), F(39,250))
share=(F(30,100)-F(15,100))/(F(30,100)-F(5,100))
assert F(5,100)*share+F(30,100)*(1-share)==F(15,100)
check('problem-solving-practice/problems/5', share, F(3,5))
check('problem-solving-practice/problems/6', F(5,100)*F(9,10)+F(95,100)*F(1,100), F(109,2000))
check('problem-solving-practice/homework/1', probability(list(range(100)),lambda x:89<=x<97), F(2,25))
check('problem-solving-practice/homework/2', F(82,100)-F(51,100), F(31,100))
check('problem-solving-practice/homework/3', probability(pairs,lambda p:p[0]>=30 or p[1]>=30), F(91,100))
check('problem-solving-practice/homework/4', probability(list(product(range(10),repeat=2)),lambda p:all(x%2==0 for x in p)), F(1,4))
check('problem-solving-practice/homework/5', probability(list(product(range(10),repeat=2)),lambda p:p[1]<(1 if p[0]<4 else 8)), F(13,25))
coverage=json.loads((ROOT/'data/solution-coverage.json').read_text())
assert set(CHECKS)=={item['key'] for item in coverage['items'] if item['type']=='task'}

report={'checkedTaskTargets':len(CHECKS),'finiteEventPairs':identity_cases,'results':CHECKS}
output=ROOT/'.preview/math-verification.json';output.parent.mkdir(exist_ok=True);output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(f'Passed {len(CHECKS)} task checks and {identity_cases} finite-event identity cases.')
