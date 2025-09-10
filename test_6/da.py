#%%
import os
# os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-21-openjdk'
# os.environ['PYSPARK_SUBMIT_ARGS'] = '--master local[3] pyspark-shell'
os.environ["PYARROW_IGNORE_TIMEZONE"] = "1"
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql import functions as sf
from pyspark.sql import Window

#%%
spark = (
    SparkSession
    .builder
    .master('local')
    .config('spark.executor.memory', '5gb')
    .config("spark.cores.max", "6")
    .config("spark.sql.ansi.enabled", "false")
    .getOrCreate()
)

#%%[markdown]
# # couriers_orders
#%%[markdown]
# У компании по доставке еды есть БД в которой содержится таблица заказов пеших курьеров couriers_orders.parquet. 
#%%
filename = 'couriers_orders.parquet'
path = str(Path.cwd() / filename)
sdf = spark.read.parquet(path)
#%%
sdf.show()
#%%
sdf.printSchema()
#%%[markdown]
# ## Вопрос №1.1:
# В конце каждого месяца компания выдает премию для своих курьеров, средняя скорость доставки за прошедший месяц которых больше средней скорости среди всех курьеров. Сколько курьеров получили премию за июнь 2021 года.
#%%
date_range = ('2021-06-01', '2021-06-30')

def calc_general_mean(df):
    """Calculates mean into a 'general_mean' global variable. Has no side effect on original DataFrame.

    Args:
        df: PySpark DataFrame

    Returns:
        df: PySpark DataFrame
    """
    global general_mean

    target_column = 'ind_mean_speed'
    general_mean = (
        df
        .agg(
            sf.mean(target_column).alias('general_mean')
        )
        .collect()
        [0]
        ['general_mean']
    )
    return df

# Result
(
    sdf
    .withColumn(
        'travel_speed',
         sf.col('distance') / sf.col('travel_time')
    )
    .filter(
        sf.col('date').between(*date_range)
    )
    .groupby('courier_id')
    .agg(
        sf.mean(sf.col('travel_speed')).alias('ind_mean_speed')
    )
    .transform(calc_general_mean)
    .filter(
        sf.col('ind_mean_speed') >= general_mean
    )
    .agg(sf.count('courier_id'))
    .show()
)

# temp = (
#     sdf
#     .withColumn(
#         'travel_speed',
#          sf.col('distance') / sf.col('travel_time')
#     )
#     .filter(
#         sf.col('date').between(*date_range)
#     )
#     .groupby('courier_id')
#     .agg(
#         sf.mean(sf.col('travel_speed')).alias('mean_speed')
#     )
# )

# general_mean_speed = (
#     temp
#     .agg(
#         sf.mean('mean_speed').alias('general_mean_speed')
#     )
#     .collect()
#     [0]
#     ['general_mean_speed']
# )

# # Result
# (
#     temp
#     .filter(
#         sf.col('mean_speed') >= general_mean_speed
#     )
#     .agg(sf.count('courier_id'))
# ).show()
#%%[markdown]
# ### Result: 6
#%%[markdown]
# ## Вопрос №1.2 (используйте данные из предыдущего вопроса №1.1):
# Компания хочет понять, насколько равномерно курьеры работают в течение месяца. Для этого нужно найти ID курьера с наибольшей разницей между максимальной и минимальной средней дневной скоростью в июне 2021 года.
#%%
(
    sdf
    .withColumn(
        'travel_speed',
         sf.col('distance') / sf.col('travel_time')
    )
    .filter(
        sf.col('date').between(*date_range)
    )
    .groupby('courier_id', sf.day('date'))
    .agg(
        sf.mean('travel_speed').alias('day_mean_speed')
    )
    .groupby('courier_id')
    .agg(
       sf.min('day_mean_speed').alias('min_day_mean_speed'),
       sf.max('day_mean_speed').alias('max_day_mean_speed')
    )
    .withColumn(
        'diff',
         sf.col('max_day_mean_speed') - sf.col('min_day_mean_speed')
    )
    .sort(sf.desc('diff'))
).show()
#%%[markdown]
# ### Result: 4
#%%[markdown]
# # purchases
#%%[markdown]
# У нас есть данные о покупках клиентов purchases.parquet. Проанализируйте интервалы времени между последовательными покупками для каждого клиента в наборе данных о покупках - напишите код для вычисления разницы в днях между текущей покупкой и предыдущей покупкой каждого клиента. Отобразите результат в новом столбце days_between_purchases.
#%%
filename = 'purchases.parquet'
path = str(Path.cwd() / filename)
sdf = spark.read.parquet(path)
#%%
sdf.show()
#%%
sdf.printSchema()
# %%
w = Window.partitionBy('customer_id').orderBy('purchase_date')
(
    sdf
    .withColumn('previous_purchase_date', sf.lag('purchase_date').over(w))
    .withColumn('days_between_purchases', sf.date_diff(sf.col('purchase_date'), sf.col('previous_purchase_date')))
    .show()
)
#%%[markdown]
# ## Вопрос №2.1:
# Какое количество NaN в столбце days_between_purchases?
w = Window.partitionBy('customer_id').orderBy('purchase_date')
(
    sdf
    .withColumn('previous_purchase_date', sf.lag('purchase_date').over(w))
    .withColumn('days_between_purchases', sf.date_diff(sf.col('purchase_date'), sf.col('previous_purchase_date')))
    .filter(sf.col('days_between_purchases').isNull())
    .count()
)
#%%[markdown]
# ### Result: 50
#%%[markdown]
# ## Вопрос №2.2 (используйте данные из предыдущего вопроса №2.1):
# У какого количества уникальных клиентов разница между текущей покупкой и предыдущей покупкой равна 20-ти дням?
w = Window.partitionBy('customer_id').orderBy('purchase_date')
(
    sdf
    .withColumn('previous_purchase_date', sf.lag('purchase_date').over(w))
    .withColumn('days_between_purchases', sf.date_diff(sf.col('purchase_date'), sf.col('previous_purchase_date')))
    .filter(sf.col('days_between_purchases') == 20)
    .select(sf.col('customer_id'))
    .distinct()
    .count()
)
#%%[markdown]
# ### Result: 10

