# -*- coding: utf-8 -*-
from flask import Flask, jsonify, abort, make_response,render_template,session,request,redirect


import pandas as pd
import numpy as np
import random

from geopy.distance import geodesic
import pandas as pd
import itertools

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

# Flaskクラスのインスタンスを作成
# __name__は現在のファイルのモジュール名
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'

#app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024


@app.route("/",methods = ['GET','POST'])
def index():
    csv = pd.read_csv('sannomiya_hokosha_data.csv',encoding='cp932')
    csv =csv[csv['日付']=="2020/2/1"]
    
    # uploadボタンが押された場合
    if request.method == "POST":
        if request.form['send'] == 'select_location':
            
            select_location = request.form['name']
            time = random.randint(2,23)

            result_select_location = select_location+"の"+str(time)+":00です。"


            now_population = csv[csv["時刻"]==str(time)+":00"].fillna(0)

            spots = csv['測定箇所名称'].unique()

            spot_pairs = []
            for conb in itertools.combinations(spots, 2):
                spot_pairs.append(list(conb)) #タプルをリスト型に変換

            num = list(itertools.combinations(list(range(1,len(spots)+1)), 2))

            distances = []
            for spot1,spot2 in spot_pairs:
                s1 = csv[csv["測定箇所名称"]==spot1].iloc[0,2:4]
                s2 = csv[csv["測定箇所名称"]==spot2].iloc[0,2:4]
                distances.append(int(geodesic(s1, s2).km))

            N,M = len(spots),len(distances)
            edge = np.array([[pair[0],pair[1],d] for pair,d in zip(num,distances)]).T
            graph = csr_matrix((edge[2], (edge[:2] - 1)), (N, N))

            distance_mat, processors = dijkstra(graph, return_predecessors = True)


            spots_index = list(range(0,len(spots)+1))
            not_use = np.array(list(range(1,N+1)))
            route = []


            tmp = []
            for n in range(0,len(spots_index)):
                dist = processors[n]
                b = spots_index[np.abs(dist).argmin()]
                
                # 通ってないなら通る
                if b in not_use:
                    route.append(b)
                    not_use = np.delete(not_use, np.where(not_use == b))
                # 通ってるならn次の値
                else:
                    ind = np.sort(np.abs(dist))[1]
                    try:
                        b = spots_index[np.where(dist == ind )[0][0]]
                        route.append(b)
                        not_use = np.delete(not_use, np.where(not_use == b))
                    except:
                        route.append(b)
                        break

            spots_route = [spots[i] for i in route]

            best_route = "最適な経路は【 "+" → ".join(spots_route)+" 】です。"

            # 2時間前からの変動
            times = [str(time-2)+':00',str(time-1)+':00',str(time)+':00']
            feed = np.array([])
            for time in times:
                feed = np.append(feed,[csv[csv['時刻']==time]['歩行者数'].values])
            timefeed = pd.DataFrame(feed.reshape((3,-1)),index=times,columns=spots).T.fillna(method='ffill')

            return render_template('index.html',locations=['三宮'],
                                    result_select_location=result_select_location,
                                    best_route = best_route,
                                    table=csv.to_html(header=True,classes="table is-fullwidth is-scrollable"),
                                    now_population=now_population[['日時','測定箇所名称','歩行者数']].to_html(header=True,index=None,classes="table"),
                                    timefeed_message = "人流の経過は以下の通りです。",
                                    timefeed=timefeed.to_html(header=True,classes="table"))
        
    
    
    else:
      result = ""
      return render_template('index.html',locations=['三宮'])


@app.route('/get_toggled_status') 
def toggled_status():
    session['current_status'] = request.args.get('status')
    return 'with caption mode : ON' if session['current_status'] == 'with caption mode : OFF' else 'with caption mode : OFF'

if __name__ == '__main__':
    app.run()
