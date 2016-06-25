from sqlalchemy import create_engine, Column, MetaData, Table, Index
from sqlalchemy import Integer, String, Text, Float, Boolean, BigInteger, Numeric, SmallInteger, DateTime
import time
import requests
from requests_futures.sessions import FuturesSession
import requests_futures
from concurrent.futures import as_completed
import datetime
import csv
import time
import sys
import re
import pandas
import numpy
import redis


import logging
logging.basicConfig(filename='logs/aggloader.log',level=logging.WARN,format='%(asctime)s %(levelname)s %(message)s')



def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate


    
    
def processData(result,orderwriter,ordersetid):
    
    try:
        m=re.search('/(\d+)/',result.url)
        regionid=m.group(1)
        resp=result.result()
        logging.info('Process {} {} {}'.format(resp.status_code,result.url,result.retry))
        if resp.status_code==200:
            orders=resp.json()
            logging.info('{} orders on page {}'.format(len(orders['items']),result.url))
            for order in orders['items']:
                orderwriter.writerow([order['id'],
                                    order['type'],
                                    order['issued'],
                                    order['buy'],
                                    order['volume'],
                                    order['volumeEntered'],
                                    order['minVolume'],
                                    order['price'],
                                    order['stationID'],
                                    order['range'],
                                    order['duration'],
                                    regionid,
                                    ordersetid]
                                )
            logging.info('{}: next page {}'.format(result.url,orders.get('next',{}).get('href',None)))
            return {'retry':0,'url':orders.get('next',{}).get('href',None)}
        else:
            logging.error("Non 200 status. {} returned {}".format(resp.url,resp.status_code))
            return {'retry':result.retry+1,'url':result.url}
    except requests.exceptions.ConnectionError as e:
        logging.error(e)
        return {'retry':result.retry+1,'url':result.url}
    
    
    
    


@RateLimited(150)
def getData(requestsConnection,url,retry):
    future=requestsConnection.get(url)
    future.url=url
    future.retry=retry
    return future


if __name__ == "__main__":
    engine = create_engine('postgresql+psycopg2://marketdata:marketdatapass@localhost/marketdata', echo=False)
    metadata = MetaData()
    connection = engine.connect()
    

    reqs_num_workers = 20
    session = FuturesSession(max_workers=reqs_num_workers)
    session.headers.update({'UserAgent':'Fuzzwork All Region Download'});
    orderTable = Table('orders',metadata,
                            Column('id',Integer,primary_key=True, autoincrement=True),
                            Column('orderID',BigInteger, primary_key=False,autoincrement=False),
                            Column('typeID',Integer),
                            Column('issued',DateTime),
                            Column('buy',Boolean),
                            Column('volume',BigInteger),
                            Column('volumeEntered',BigInteger),
                            Column('minVolume',BigInteger),
                            Column('price',Numeric(scale=4,precision=19)),
                            Column('stationID',Integer),
                            Column('range',String(12)),
                            Column('duration',Integer),
                            Column('region',Integer),
                            Column('orderSet',BigInteger)
                            )
                            
    Index("orders_1",orderTable.c.typeID)
    Index("orders_2",orderTable.c.typeID,orderTable.c.buy)
    Index("orders_5",orderTable.c.region,orderTable.c.typeID,orderTable.c.buy)
    Index("orders_6",orderTable.c.region)


    orderSet=Table('orderset',metadata,
                    Column('id',BigInteger,primary_key=True, autoincrement=True),
                    Column('downloaded',DateTime)
                )

    aggregates=Table('aggregateOrders',metadata,
                    Column('typeID',Integer),
                    Column('region',Integer),
                    Column('orderSet',BigInteger),
                    Column('wavgsell',Numeric(scale=2,precision=19)),
                    Column('wavgbuy',Numeric(scale=2,precision=19)),
                    Column('maxsell',Numeric(scale=2,precision=19)),
                    Column('maxbuy',Numeric(scale=2,precision=19)),
                    Column('minsell',Numeric(scale=2,precision=19)),
                    Column('minbuy',Numeric(scale=2,precision=19)),
                    Column('stddevsell',Numeric(scale=2,precision=19)),
                    Column('stddevbuy',Numeric(scale=2,precision=19)),
                    Column('mediansell',Numeric(scale=2,precision=19)),
                    Column('medianbuy',Numeric(scale=2,precision=19)),
                    Column('volumesell',BigInteger),
                    Column('volumebuy',BigInteger),
                    Column('countsell',BigInteger),
                    Column('countbuy',BigInteger),
                    Column('fivepsell',Numeric(scale=2,precision=19)),
                    Column('fivepbuy',Numeric(scale=2,precision=19)),
                )
    Index("aggregates1",aggregates.c.region,aggregates.c.typeID,aggregates.c.orderSet)


    metadata.create_all(engine,checkfirst=True)

    urls=[]

    urls.append({'url':"https://crest-tq.eveonline.com/market/10000001/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000002/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000003/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000004/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000005/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000006/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000007/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000008/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000009/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000010/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000011/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000012/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000013/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000014/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000015/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000016/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000017/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000018/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000019/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000020/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000021/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000022/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000023/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000025/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000027/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000028/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000029/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000030/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000031/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000032/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000033/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000034/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000035/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000036/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000037/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000038/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000039/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000040/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000041/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000042/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000043/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000044/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000045/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000046/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000047/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000048/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000049/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000050/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000051/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000052/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000053/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000054/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000055/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000056/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000057/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000058/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000059/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000060/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000061/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000062/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000063/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000064/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000065/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000066/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000067/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000068/orders/all/",'retry':0})
    urls.append({'url':"https://crest-tq.eveonline.com/market/10000069/orders/all/",'retry':0})

    trans = connection.begin()

    connection.execute(orderSet.insert(),downloaded=datetime.datetime.now().isoformat())

    result=connection.execute("select currval('orderset_id_seq')").fetchone()

    ordersetid=result[0]

    with open('/tmp/orderset-{}.csv'.format(ordersetid), 'wb') as csvfile:
        orderwriter = csv.writer(csvfile,quoting=csv.QUOTE_MINIMAL,delimiter="\t")
        # Loop through the urls in batches
        while len(urls)>0:
            futures=[]
            logging.warn("Loop restarting");
            for url in urls:
                logging.info('URL:{}  Retry:{}'.format(url['url'],url['retry']));
                futures.append(getData(session,url['url'],url['retry']))
            urls=[]
            for result in as_completed(futures):
                presult=processData(result,orderwriter,ordersetid)
                if presult['retry']==1:
                    urls.append(presult)
                    logging.info("adding {} to retry {}".format(presult.url,presult.retry))
                if presult['retry'] == 0 and presult['url'] is not None:
                    logging.info('{} has more pages. {}'.format(result.url,presult['retry']))
                    urls.append(presult)


    logging.warn("Loading Data File");
    connection.execute("""copy orders("orderID","typeID",issued,buy,volume,"volumeEntered","minVolume",price,"stationID",range,duration,region,"orderSet") from '/tmp/orderset-{}.csv'""".format(ordersetid))
    logging.warn("Complete load");
    trans.commit()
    


    logging.warn("Pandas populating sell");
    
    sell=pandas.read_sql_query("""select region||'|'||"typeID"||'|'||buy as what,price,sum(volume) volume from orders  where "orderSet"={} and buy=False group by region,"typeID",buy,price order by region,"typeID",price asc""".format(ordersetid),connection);
    logging.warn("Pandas populating buy");
    buy=pandas.read_sql_query("""select region||'|'||"typeID"||'|'||buy as what,price,sum(volume) volume from orders  where "orderSet"={} and buy=True group by region,"typeID",buy,price order by region,"typeID",price desc""".format(ordersetid),connection);
    logging.warn("Pandas populating aggregates");
    aggregates=pandas.read_sql_query("""select region||'|'||"typeID"||'|'||buy as what,"orderSet",region,"typeID",buy,sum(price*volume)/sum(volume) as weightedaverage,max(price) as maxval,min(price) as minval,coalesce(stddev(price),0.001) as stddev,quantile(price,0.5) as median,sum(volume) volume,count(*) numorders from orders where "orderSet"={} group by "orderSet","typeID",region,buy""".format(ordersetid),connection);
    aggregates=aggregates.set_index('what')

    logging.warn("Pandas populated");


    logging.warn("Sell Math running");
    sell['min']=sell.groupby('what')['price'].transform('min')
    sell['volume']=sell.apply(lambda x: 0 if x['price']>x['min']*100 else x['volume'],axis=1)
    sell['cumsum']=sell.groupby('what')['volume'].apply(lambda x: x.cumsum())
    sell['fivepercent']=sell.groupby('what')['volume'].transform('sum')/20
    sell['lastsum']=sell.groupby('what')['cumsum'].shift(1)
    sell.fillna(0,inplace=True)
    sell['applies']=sell.apply(lambda x: x['volume'] if x['cumsum']<=x['fivepercent'] else x['fivepercent']-x['lastsum'],axis=1)
    num = sell._get_numeric_data()
    num[num < 0] = 0
    logging.warn("Buy Math running");
    buy['max']=buy.groupby('what')['price'].transform('max')
    buy['volume']=buy.apply(lambda x: 0 if x['price']<x['max']/100 else x['volume'],axis=1)
    buy['cumsum']=buy.groupby('what')['volume'].apply(lambda x: x.cumsum())
    buy['fivepercent']=buy.groupby('what')['volume'].transform('sum')/20
    buy['lastsum']=buy.groupby('what')['cumsum'].shift(1)
    buy.fillna(0,inplace=True)
    buy['applies']=buy.apply(lambda x: x['volume'] if x['cumsum']<=x['fivepercent'] else x['fivepercent']-x['lastsum'],axis=1)
    num = buy._get_numeric_data()
    num[num < 0] = 0
    
    
    logging.warn("Aggregating");
    buyagg=buy.groupby('what').apply(lambda x: numpy.average(x.price, weights=x.applies))
    sellagg=sell.groupby('what').apply(lambda x: numpy.average(x.price, weights=x.applies))
    five=pandas.concat([buyagg, sellagg], axis=1,keys=['buy','sell']).reset_index()
    five=five.set_index('index').max(axis=1)
    five=five.rename('fivepercent')
    agg2=pandas.concat([aggregates,five],axis=1)
    
    
    logging.warn("Outputing to DB");
    agg2.to_sql('aggregates',connection,index=False,if_exists='append')
    logging.warn("Outputing to Redis");
    redisdb = redis.StrictRedis()
    pipe = redisdb.pipeline()
    count=0;
    for row in agg2.itertuples():
        pipe.set(row[0], "{}|{}|{}|{}|{}|{}|{}|{}".format(row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12]))
        count+=1
        if count>1000:
            count=0
            pipe.execute()
    pipe.execute()
    logging.warn("Complete")
