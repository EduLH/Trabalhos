import csv
import operator
import numpy as np
import matplotlib.pyplot as plt
import time

path = "/home/eduardo.honorato/Área de Trabalho/tab1.csv"
file = open(path, newline='')
reader = csv.reader(file)

header = next(reader)
data = []
SortData = []
kids = []
X = []
for row in reader:
    data.append([row[0], int(row[2])])

start = time.time()
sort = insertion(data, key = operator.itemgetter(1))
end = time.time()
print(end - start)
for i in range(0, len(sort) - 1):
    SortData.append([sort[i][1], i])

#print (SortData)
ReturnPath = "/home/eduardo.honorato/Área de Trabalho/New.csv"
file = open(ReturnPath, 'w')
writer = csv.writer(file)
for i in range(len(SortData) - 1):
    kids.append(SortData[i][0])
    X.append(SortData[i][1])
    #writer.writerow([gnomos, X])
#print(kids)
#print(X)
plt.plot(X, kids)
plt.show()
