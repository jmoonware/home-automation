import data

data.StartDataLogging()

from DataLogger import DataReader

dr=DataReader(settings={'data_root':'dataFeb19'})

dr.RebuildCache()

dr.Run()