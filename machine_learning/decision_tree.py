# 决策树的使用
# https://zhuanlan.zhihu.com/p/45225428


from math import log


def createDataSet():
    dataSet = [[1, 1, 1, 'yes'],
               [1, 1, 0, 'no'],
               [1, 0, 1, 'no'],
               [0, 1, 0, 'no'],
               [0, 1, 1, 'yes']]
    labels = ['shape', 'work', 'character']
    return dataSet, labels


def splitDataSet(dataSet, axis, value):
    retDataSet = []
    for featVec in dataSet:
        if featVec[axis] == value:
            reducedFeatVec = featVec[:axis]
            reducedFeatVec.extend(featVec[axis + 1:])
            retDataSet.append(reducedFeatVec)
    return retDataSet


def calcShannonEnt(dataSet):
    numEntries = len(dataSet)
    labelCounts = {}
    for featVec in dataSet:
        currentLabel = featVec[-1]
        if currentLabel not in labelCounts.keys():
            labelCounts[currentLabel] = 0
        labelCounts[currentLabel] += 1
    shannonEnt = 0.0
    for key in labelCounts:
        prob = float(labelCounts[key]) / numEntries
        shannonEnt -= prob * log(prob, 2)
    return shannonEnt


def chooseBestFeatureToSplit(dataSet):
    numFeatures = len(dataSet[0]) - 1
    baseEntropy = calcShannonEnt(dataSet)
    bestInfoGain = 0.0
    bestFeature = -1
    for i in range(numFeatures):
        featList = [example[i] for example in dataSet]
        uniqueVals = set(featList)
        newEntropy = 0.0
        for value in uniqueVals:
            subDataSet = splitDataSet(dataSet, i, value)
            prob = len(subDataSet) / float(len(dataSet))
            newEntropy += prob * calcShannonEnt(subDataSet)
        infoGain = baseEntropy - newEntropy
        if (infoGain > bestInfoGain):
            bestInfoGain = infoGain
            bestFeature = i
    return bestFeature


def majorityCnt(classList):
    classCount = {}
    for vote in classList:
        if vote not in classCount.keys():
            classCount[vote] = 0
        classCount[vote] += 1
    sortedClassCount = sorted(classCount.iteritems(), key=operator.itemgetter(1),
                              reverse=True)
    return sortedClassCount[0][0]


def createTree(dataSet, labels):
    classList = [example[-1] for example in dataSet] # yes no

    # 全部是同一类
    if classList.count(classList[0]) == len(classList):
        t=classList[0]
        print('same ',t)
        return t

    if len(dataSet[0]) == 1: # 就只有一个数据
        t=majorityCnt(classList)
        print('major',t)
        return t

    bestFeat = chooseBestFeatureToSplit(dataSet)
    bestFeatLabel = labels[bestFeat]
    myTree = {bestFeatLabel: {}}

    del (labels[bestFeat])
    featValues = [example[bestFeat] for example in dataSet]
    uniqueVals = set(featValues)

    for value in uniqueVals:
        subLabels = labels[:]
        t=createTree(splitDataSet(dataSet, bestFeat, value),
                   subLabels)
        print(t)

        myTree[bestFeatLabel][value] = t

    return myTree


def main():
    myData, label = createDataSet()
    myTree = createTree(myData, label)
    print(myTree)


if __name__ == '__main__':
    main()
