# 台鐵自動化購票腳本
-------------

## 安裝方法

### Railway
	git clone https://github.com/pamge/railway

### [Aubio](https://github.com/aubio/aubio)
	sudo pip install https://github.com/aubio/aubio/archive/master.zip

### [Libsvm](https://github.com/cjlin1/libsvm)
	git clone https://github.com/cjlin1/libsvm
	cd libsvm/
	make
	cd python
	make
	cd ..
	cp python/*.py ../railway/
	cp libsvm.so.2 ../railway/
	vim ../railway/svm.py
	:%s, ../libsvm.so.2, ibsvm.so.2
-------------

## 使用方法

### download_data.py

==================

下載 10 筆資料至 Data/Train

	./download_data.py train

下載 100 筆資料至 Data/Test

	./download_data.py test 100

-------------

### extract_feature.py
#### 需先在 Data/Train 資料夾內編輯 answers.txt，第 n 行對應至 Data/Train/n-1.wav 的答案
#### 例如 0.wav 正確答案為 12345，則 Data/Train/answer.txt 第一行應為12345
==================

抽出 Data/Train/answers.txt 對應的音訊特徵，最後儲存為 Data/Train/Train_features.txt

	./extract_feature.py train

抽出 Data/Train/answers.txt 對應的音訊特徵，最後儲存為 Data/Train/Test_features.txt

	./extract_feature.py test

-------------

### train_feature.py

#### 透過 Data/Train/Train_features.txt 訓練出 svm_model 並儲存為 Data/svm.model

-------------

### test_feature.py

#### 載入 Data/svm.model 並對 Data/Test/Test_features.txt 進行測試並輸出辨識率

