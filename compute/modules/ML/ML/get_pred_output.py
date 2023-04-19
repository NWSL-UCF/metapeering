import pandas as pd
import sys
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
import joblib
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from gatherFeatures import gather, generateCustomerCones, generateNetsData, getNetsWithUSCoverage
from collections import defaultdict
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import confusion_matrix


def cleanData(df):

    X = df[['policy_ratio', 'traffic_ratio_diff', 'traffic_diff',
       'policy_contracts', 'policy_general', 'policy_locations',
       'common_pop_count', 'prefixes4', 'prefixes6', 'pop_count_diff',
       'non_common_pops', 'pop_affinity', 'rank_diff', 'cone_overlap',
       'total_diff', 'customer_diff', 'peer_diff', 'provider_diff',
       'ASN_count_diff', 'num_prefixes_diff', 'num_addresses_diff']].copy()  #independent columns
    y = df['peering'].copy()    #target column i.e peering
    types = df['type'].copy()    #AS Relation Types
    pairs = df['pair'].copy()    #ASN Pair

    X["cone_size_diff"] = df[["ASN_count_diff", "num_prefixes_diff", "num_addresses_diff"]].mean(axis=1)
    X["connectivity_diff"] = df[["provider_diff", "peer_diff", "customer_diff"]].mean(axis=1)

    X = X.drop(["policy_locations", "policy_ratio", "policy_contracts"], axis=1)

    X = X.drop(["prefixes4", "prefixes6"], axis=1)
    X = X.drop(["total_diff"], axis=1)
    X = X.drop(["provider_diff", "peer_diff", "customer_diff"], axis=1)
    X = X.drop(["ASN_count_diff", "num_prefixes_diff", "num_addresses_diff"], axis=1)
    X = X.drop(["non_common_pops","pop_count_diff", "common_pop_count"], axis=1)


    return X, y, types, pairs, pd.concat([X, y], axis=1)

# Save the training model into file
def dumpTrain(year):

    dfTrain = gather(year)
    dfTrain = dfTrain.fillna(0)

    X_train, y_train, types_train, pairs_train, df_ = cleanData(dfTrain)

    clf1 = RandomForestClassifier()
    sel = SelectFromModel(clf1)
    clf1.fit(X_train,y_train)
    sel.fit(X_train,y_train)

    joblib.dump(clf1, 'train.pkl')


def updatePred(year):

    dfTest = gather(year)
    dfTest = dfTest.fillna(0)
    X_test, y_test, types_test, pairs_test, df_ = cleanData(dfTest)

    # load training data to fit model to testing data.
    loader = joblib.load('train.pkl')
    y_pred = (loader.predict_proba(X_test))[:,1]

    nr = []
    th = np.arange(0,1,0.01)

    for t in th:
        y = [0 if yp<t else 1 for yp in y_pred]
        conf_matrix = confusion_matrix(y_test, y, labels=[1,0])
        nr.append(conf_matrix[0][1] + conf_matrix[1][0])

    opTh = th[nr.index(min(nr))]
    y_pred = np.array([0 if yp<opTh else 1 for yp in y_pred])

    output = pd.DataFrame(y_pred, columns = ['Pred'])
    lookup_table = pd.concat([pairs_test, output], axis=1)
    lookup_table.to_csv('out.csv')

# TODO:
# Script to call updatePred at a determined time: weekly, biweekly, monthly, etc. for updated output.
# updatePred(2021)
