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
        self.parent = None
        self.tree = None
    def play(self,duration,layer=0):
        report = "  "*layer
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
            report += str(layer)+"  "+str(pitchToReport)+"  "+str(len(self.children))
            print(report)
            for i in range(len(self.children)):
                self.children[i].play(duration/float(len(self.children)),layer+1)
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
    def addChild(self,child):
        self.children.append(child)
        child.tree = self.tree
        child.parent = self
        self.tree.population += 1
        self.population += 1
        if not (self.parent == None):
            self.parent.updatePopulation(1)
    def getChild(self,child):
        if ((child < 0) or (child >= len(self.children))):
            return None
        return self.children[child]
    def getRandomChild(self):
        if (len(self.children) == 0):
            return None
        return self.getChild(random.randint(0,len(self.children)-1))
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
    def subdivide(self,childCount):
        pitchUnit = (float(self.pitch)/float(childCount))**self.tree.getMagicNumber(math.pi)
        median = float(childCount-1)/2.0
        direction = float(random.choice([-1,1]))
        for i in range(childCount):
            pitchNew = float(i)-median
            pitchNew *= pitchUnit*direction
            pitchNew += float(self.pitch)
            self.addChild(Leaf(int(pitchNew)))
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
    def getMagicNumber(self,seed):
        span = 1.0-(1.0/seed)
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
            self.getRandomLeaf().subdivide(random.randint(2,4))
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
