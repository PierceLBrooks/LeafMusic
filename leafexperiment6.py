import sys
import math
import bisect
import pygame
import pygame.midi
import random
from time import sleep

class Leaf(object):
    def __init__(self,pitch):
        self.pitch = pitch
        self.children = []
        self.population = 0
        self.layer = 0
        self.order = 0
        self.pattern = None
        self.parent = None
        self.tree = None
    def play(self,duration):
        report = "  "*self.layer
        pitch = self.pitch+self.tree.pitch
        pitchToReport = pitch
        volume = self.tree.volume
        volumeToReport = volume
        if (len(self.children) == 0):
            report += str(pitchToReport)+"  "+str(volumeToReport)
            print(report)
            self.tree.pitchLast = pitch
            self.tree.midi.note_on(pitch,volume)
            sleep(duration)
            self.tree.midi.note_off(pitch,volume)
        else:
            report += str(self.layer)+"  "+str(pitchToReport)+"  "+str(len(self.children))
            print(report)
            total = float(self.getLeafPopulation())
            for i in range(len(self.children)):
                self.children[i].play((duration*(total-self.children[i].getLeafPopulation()))/total)
    def getLeafPopulation(self):
        if (len(self.children) == 0):
            return 1
        leafPopulation = 0
        for i in range(len(self.children)):
            leafPopulation += self.children[i].getLeafPopulation()
        return leafPopulation
    def updatePopulation(self,populationChange):
        self.population += populationChange
        if not (self.parent == None):
            self.parent.updatePopulation(populationChange)
    def getCopy(self,parent):
        copy = parent.addChild(Leaf(self.pitch),len(parent.children))
        for i in range(len(self.children)):
            self.children[i].getCopy(copy)
    def addChild(self,child,index):
        self.children.append(child)
        child.tree = self.tree
        child.parent = self
        child.layer = self.layer+1
        child.order = index
        self.tree.population += 1
        self.population += 1
        if not (self.parent == None):
            self.parent.updatePopulation(1)
        return child
    def getRandomChild(self):
        if (len(self.children) == 0):
            return None
        return self.children[random.randint(0,len(self.children)-1)]
    def getWeightedRandomChild(self):
        if (len(self.children) == 0):
            return None
        if (len(self.children) == self.population):
            return self.getRandomChild()
        weight = 0.0
        weights = []
        leftovers = []
        for i in range(len(self.children)):
            if (self.children[i].population == 0):
                leftovers.append(i)
                continue
            weights.append((float(self.children[i].population)/float(self.population),i))
            weight += weights[len(weights)-1][0]
        if not (len(leftovers) == 0):
            unit = 1.0-weight
            unit /= float(len(leftovers))
            for i in range(len(leftovers)):
                weights.append((weight+(unit*float(i+1)),leftovers[i]))
        for i in range(len(weights)-1,-1,-1):
            index = random.randint(0,i)
            temp = weights[index]
            weights[index] = weights[i]
            weights[i] = temp
        weight = 0.0
        childrenWeightMap = {}
        for i in range(len(weights)):
            weight += 1.0/weights[i][0]
            childrenWeightMap[weight] = weights[i][1]
        childrenWeightMapKeys = sorted(list(childrenWeightMap.keys()),key=float)
        index = bisect.bisect_right(childrenWeightMapKeys,random.uniform(0.0,weight))
        if (index < 0):
            index = 0
        if (index >= len(childrenWeightMapKeys)):
            index = len(childrenWeightMapKeys)-1
        key = childrenWeightMapKeys[index]
        child = childrenWeightMap[key]
        return self.children[child]
    def subdivide(self):
        if not (self.parent == None):
            if not (self.parent.pattern == None):
                for i in range(len(self.parent.pattern)):
                    if not (i == self.order):
                        if (self.parent.pattern[i] == self.parent.pattern[self.order]):
                            if not (len(self.parent.children[i].children) == 0):
                                for j in range(len(self.parent.children[i].children)):
                                    self.parent.children[i].children[j].getCopy(self)
                                print("WOAH",self.layer,self.order)
                                return None
        childCount = 2
        for i in range(self.layer+1):
            if (random.uniform(0.0,1.0) < (math.e**float(-i-1))**float(self.layer)):
                childCount += 1
            else:
                break
        if (childCount > 2):
            self.pattern = []
            for i in range(childCount):
                self.pattern.append(random.randint(0,childCount-1))
        print(self.layer,childCount,self.pattern)
        pitchUnit = (float(self.pitch)/float(childCount))**self.tree.getMagicNumber(math.pi,True)
        median = float(childCount-1)/2.0
        direction = float(random.choice([-1,1]))
        #scale = 1.0/math.pi
        #scale = random.uniform(scale,math.pi**scale)
        for i in range(childCount):
            pitchNew = float(i)-median
            pitchNew *= pitchUnit*direction#*scale
            pitchNew += float(self.pitch)
            self.addChild(Leaf(int(pitchNew)),i)
class Tree(object):
    def __init__(self,root,instrument,volume,midi):
        self.root = root
        root.tree = self
        self.instrument = instrument
        self.volume = volume
        self.midi = midi
        self.population = 1
        self.pitch = 0
        self.pitchLast = 0
    def getMagicNumber(self,seed,spread):
        span = 1.0-(1.0/seed)
        if not (spread):
            return span
        span = (span-(1.0-span))**span
        span *= 0.5
        return random.uniform(0.5-span,0.5+span)
    def getLeafPopulation(self):
        return self.root.getLeafPopulation()
    def getRandomLeaf(self):
        leaf = None
        leafNext = self.root
        while not (leafNext == None):
            leaf = leafNext
            leafNext = leaf.getWeightedRandomChild()
        return leaf
    def play(self,duration):
        print("Here we go...")
        self.midi.set_instrument(self.instrument)
        self.root.play(duration)
    def generate(self,populationTarget):
        leafPopulation = self.root.getLeafPopulation()
        difference = abs(self.population-leafPopulation)
        while (difference < populationTarget):
            print(self.population,leafPopulation,difference,float(self.population)**(1.0/float(leafPopulation)))
            self.getRandomLeaf().subdivide()
            leafPopulation = self.root.getLeafPopulation()
            difference = abs(self.population-leafPopulation)
if (__name__ == "__main__"):
    if (len(sys.argv) > 1):
        seed = int(sys.argv[1])
        print("Seed:",sys.argv[1],seed)
        random.seed(seed)
    pitchBase = 10
    pitchRange = 6
    instrument = 46
    volume = 127
    port = 0
    descendents = 1
    population = 48
    duration = float(population)/1.5
    #duration = 1.0
    pause = 1.0
    pitchRoot = random.randint(pitchRange/2,pitchRange)*10
    pygame.init()
    pygame.midi.init()
    for i in range(pygame.midi.get_count()):
        print(pygame.midi.get_device_info(i))
    midi = pygame.midi.Output(port,1)
    for i in range(descendents+1):
        tree = Tree(Leaf(pitchRoot),instrument,volume,midi)
        tree.generate(population)
        tree.play(duration)
        pitchRoot = tree.pitchLast
    sleep(pause)
    midi.close()
    pygame.midi.quit()
