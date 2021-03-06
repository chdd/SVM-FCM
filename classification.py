import iofile, numpy as np, pickle, time
from sklearn import svm
# import matplotlib.pyplot as plt

startTime = time.time()

def processingData(rawData):
	data = []
	target = []
	i = 0
	for line in rawData:
		i += 1
		obj = [line['details'], line['duration'], line['page_per_time']]
		c = 1 if line['class'] == 'buy' else 0
		target.append(c)
		data.append(obj)
	return data, target

def confussionMatrix(model, testData, testTarget):
	print "== Processing Confussion Matrix =="
	Z = model.predict(testData)
	cm = {
		'tp': 0, 'fp': 0,
		'tn': 0, 'fn': 0
	}
	for ix in range(len(Z)):
		if Z[ix] == 1:
			if testTarget[ix] == Z[ix]: cm['tp'] += 1
			else: cm['fp'] += 1
		else:
			if testTarget[ix] == Z[ix]: cm['tn'] += 1
			else: cm['fn'] += 1
	print "Confussion Matrix: ",cm
	return cm

def errorRate(confMatrix):
	return float(confMatrix['fp'] + confMatrix['fn']) / float(confMatrix['fp'] + confMatrix['fn'] + confMatrix['tp'] + confMatrix['tn'])

def accuracy(confMatrix):
	return float(confMatrix['tp'] + confMatrix['tn']) / float(confMatrix['fp'] + confMatrix['fn'] + confMatrix['tp'] + confMatrix['tn'])

def sensitivity(confMatrix):
	return float(confMatrix['tp']) / float(confMatrix['tp'] + confMatrix['fn'])

def precision(confMatrix):
	return float(confMatrix['tp']) / float(confMatrix['tp'] + confMatrix['fp'])

def recall(confMatrix):
	return sensitivity(confMatrix)

def f1score(precision, recall):
	return 2 * (float(precision*recall) / (precision + recall))

def processBuyingSession(rawData, paramData, model):
	Z = model.predict(paramData)
	data =  []
	for ix in range(len(Z)):
		if Z[ix] == 1:
			data.append(rawData[ix])
			print "add to buying session: ",rawData[ix]
	print len(data)
	iofile.savePickle('buys-1.pkl', data)
	return data

def crossValidation(data, target, kernel='linear'):
	print "=== Processing 10-fold Cross Validation ==="
	k = 10
	foldLength = len(data) / k
	filename = 'svc-'+kernel
	# print data
	# a,b adalah batas awal dan akhir untuk testing data
	for ix in range(3,4):
		print "Processed Time:", (time.time() - startTime)
		print "Fold %d kernel %s" % (ix, kernel)
		a, b = ix * foldLength, (ix+1) * foldLength if ix != k-1 else len(data)
		testData, testTarget = data[a:b], target[a:b]
		trainData, trainTarget = [], []
		for i in range(5,k):
			if i != ix:
				awal, akhir = i * foldLength, (i+1) * foldLength if i != k-1 else len(data)
				trainData.extend(data[awal:akhir])
				trainTarget.extend(target[awal:akhir])
		X, y = np.array(trainData), np.array(trainTarget)

		if ix != 0:
			if kernel == 'sigmoid':
				svc = svm.SVC(kernel=kernel, C=.01, gamma=.5, coef0=0, cache_size=1000).fit(X,y)
			elif kernel == 'rbf':
				svc = svm.SVC(kernel=kernel, C=10, gamma=.5, cache_size=1000).fit(X,y)
			elif kernel == 'poly':
				svc = svm.SVC(kernel=kernel, C=.01, gamma=1, degree=3, coef0=10, cache_size=1000).fit(X,y)
			else:
				kernel = 'linear'
				svc = svm.SVC(kernel=kernel, C=.1, cache_size=1000).fit(X,y)

			iofile.savePickle('pengujian/'+filename+'-fold'+`ix`+'.pkl', svc)
		else:
			svc = iofile.readPickle('pengujian/'+filename+'-fold'+`ix`+'.pkl')

		savePengujian(ix, svc, trainData, trainTarget, testData, testTarget, filename)


def savePengujian(ix, svc, trData, trTarget, tData, tTarget, filename):
	confMatrix = confussionMatrix(svc, tData, tTarget)
	erRate = errorRate(confMatrix)
	acc = accuracy(confMatrix)
	sens = sensitivity(confMatrix) #sensitivity atau recall
	prec = precision(confMatrix)
	f1 = f1score(prec, sens)

	print "Fold:", ix
	print "Error Rate: ", erRate
	print "Accuracy: ", acc
	print "Sensitivity/Recall: ", sens
	print "Precision: ", prec
	print "F1 Score:", f1

	if iofile.isFileExist('pengujian/'+filename+'.csv'):
		dataUji = iofile.readDictFromCSV('pengujian/'+filename+'.csv')
	else:
		dataUji = []

	pengujian_keys = ['fold', 'err', 'acc', 'sens', 'precision', 'f1']
	pengujian_values = [ix, erRate, acc, sens, prec, f1]
	obj = dict(zip(pengujian_keys, pengujian_values))
	dataUji.append(obj)

	iofile.saveDictToCSV('pengujian/'+filename+'.csv', pengujian_keys, dataUji)
	fileheader = ['details', 'duration', 'page_per_time']
	iofile.saveListToCSV('pengujian/training-'+filename+'-fold'+`ix`+'.csv', fileheader, trData)
	iofile.saveListToCSV('pengujian/testing-'+filename+'-fold'+`ix`+'.csv', fileheader, tData)

def processingUjiFold(data, target, kernel):
	k = 10
	foldLength = len(data) / k
	listUji = []
	for ix in range(10):
		print "Processed Time:", (time.time() - startTime)
		print "Fold %d kernel %s" % (ix, kernel)

		a, b = ix * foldLength, (ix+1) * foldLength if ix != k-1 else len(data)
		testData, testTarget = data[a:b], target[a:b]
		svc = iofile.readPickle('pengujian/svc-'+kernel+'-fold'+`ix`+'.pkl')
		
		confMatrix = confussionMatrix(svc, testData, testTarget)
		erRate = errorRate(confMatrix)
		acc = accuracy(confMatrix)
		sens = sensitivity(confMatrix) #sensitivity atau recall
		prec = precision(confMatrix)
		f1 = f1score(prec, sens)

		print "Fold:", ix
		print "Error Rate: ", erRate
		print "Accuracy: ", acc
		print "Sensitivity/Recall: ", sens
		print "Precision: ", prec
		print "F1 Score:", f1

		pengujian_keys = ['fold', 'err', 'acc', 'sens', 'precision', 'f1']
		pengujian_values = [ix, erRate, acc, sens, prec, f1]
		obj = dict(zip(pengujian_keys, pengujian_values))
		listUji.append(obj)

	iofile.saveDictToCSV('pengujian/svc-'+kernel+'.csv', pengujian_keys, listUji)

rawData = iofile.readPickle('clicks-combine-2.pkl')
print "Time process:", (time.time() - startTime)
data, target = processingData(rawData)

a = iofile.readPickle('pengujian/svc-sigmoid-fold0.pkl')

# processingUjiFold(data, target, 'poly')


# print "Time process:", (time.time() - startTime)
crossValidation(data, target, 'poly')

# processBuyingSession(rawData, data, svc)