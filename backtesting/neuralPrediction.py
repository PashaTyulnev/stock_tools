import pandas as pd
import functions
import csv
# Import keras libraries
from keras.models import Sequential
from keras.layers import Dense
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px


def predictNextDay(csvPath, considerLastValuesAmount=0, lastValuesToLearnAmount=10):
    stockDataFrame = pd.read_csv(csvPath, sep='\t')

    stockDataFrame = stockDataFrame.rename(columns={
        '<DATE>': 'date',
        '<TIME>': 'time',
        '<OPEN>': 'open',
        '<HIGH>': 'high',
        '<LOW>': 'low',
        '<CLOSE>': 'close',
        '<TICKVOL>': 'tickvol',
        '<VOL>': 'vol',
        '<SPREAD>': 'spread'
    })

    features = ['close']

    allDays = stockDataFrame[features]
    if considerLastValuesAmount != 0:
        considerLastValuesAmount = len(allDays)

    allDays = allDays.tail(considerLastValuesAmount)

    # How much previous days/minutes should be considered
    previousDaysAmount = lastValuesToLearnAmount

    columns = ['currentPrice']
    for previousDay in range(previousDaysAmount):
        columns.append("prev_" + str(previousDay + 1))

    data = pd.DataFrame(columns=columns)

    # Build new DataFrame for learning
    counter = 0
    for index, day in allDays.iterrows():
        currentPrice = day['close']
        currentDate = index

        # begin creation of dataframe after x days
        if counter >= previousDaysAmount:
            newRow = {'currentPrice': currentPrice}

            # Check if previous days exists
            for previousDay in range(previousDaysAmount):
                previousDay = previousDay + 1
                # Convert the integer indexer to a list
                indexer = int(counter - previousDay)

                # Use the `take` method with the list indexer
                previousDayPrice = allDays.iloc[indexer].close
                newRow.update({'prev_' + str(previousDay): previousDayPrice})

            newRow = pd.json_normalize(newRow)

            data = pd.concat([data, newRow])
        counter = counter + 1

    columns.remove('currentPrice')

    sizeOfData = data.shape[0]

    amountDataForTesting = int(sizeOfData / 4)
    amountDataForLearning = sizeOfData - amountDataForTesting

    # Data to learn
    trainingData = data[columns].head(amountDataForLearning)

    # Data to test learn results
    predictionData = data[columns].tail(amountDataForTesting)

    # prediction target
    trainingResults = data.head(amountDataForLearning).currentPrice

    # All data for check learn results
    testResultsData = data.tail(amountDataForTesting)

    # Create the neural network model
    model = Sequential()
    model.add(Dense(units=64, activation='relu', input_dim=previousDaysAmount))
    model.add(Dense(units=32, activation='relu'))
    model.add(Dense(units=1))

    # Compile the model
    model.compile(loss='mean_absolute_error', optimizer='adam', metrics=['mae'])

    X_train = np.asarray(trainingData).astype(np.float32)
    y_train = np.asarray(trainingResults).astype(np.float32)

    # Fit the model to the training data
    model.fit(X_train, y_train, epochs=100, batch_size=lastValuesToLearnAmount, verbose=0)

    # Make predictions on the test data
    # testResultsData = np.asarray(testResultsData).astype(np.float32)

    testResultsDataCopy = testResultsData
    testResultsData = np.asarray(testResultsData[columns]).astype(np.float32)

    prediction = model.predict(testResultsData)

    # Calculate the percentage of correct predictions
    percentage = functions.getPercentageOfRightDirection(testResultsDataCopy, prediction)

    print("Tried on last: " + str(considerLastValuesAmount) + " Values")


# DB Path
dbPath = "../data/INTL_DAY.csv"

# predictNextDay(dbPath, 200, 20)
predictNextDay(dbPath, 2000, 90)


