# %% [markdown]
# # Задание 0
# Определить вероятность выпадения цифры 8 на десятом броске 9-гранного кубика. Ответ укажите в комментариях в файле ipynb, где буду выполняться следующие задания.
# %% [markdown]
# ## Решение
# Странная формулировка. Выпадения цифр - события независимые друг от друга, так что вероятность 1/9, НО, раз упоминается десятый бросок, значит скорее всего подразумевается исход, когда девять бросков событие "не 8" и на десятый "8". Тогда вероятность (8/9)^9 * 1/9 = $\approx$ 0.039, что примерно 4%
# %%
((8 / 9) ** 9) * (1 / 9)
# %% [markdown]
# # Задание 1
# Подготовка отчета по конкурентам. Три индивидуальных предпринимателя (Иванов, Петров и Сидоров) продают чехлы и другие аксессуары для смартфонов на Wildberries. В файле «Данные для задания Python.xlsx»., на листе «Задание1» представлена выборка, включающая номенклатуры товаров трех индивидуальных предпринимателей. Пользуясь отчетами о продажах, представленными на других листах, для списка номенклатур с листа «Задание1», выполните следующие задания:
# %% [markdown]
# ## 1.0. Импорт всех необходимых данных.
# %%
%matplotlib inline
import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations
# %%
data_folder = 'data'
datafile_name= r'Данные для задания Python.xlsx'
filepath = Path.cwd() / data_folder / datafile_name
xls = pd.ExcelFile(filepath)
display(xls.sheet_names)
# %%
task_sheet_name = 'Задание1'
items = pd.read_excel(xls, sheet_name=task_sheet_name)
# %%
# Отчеты о продажах в dict
proprietor_sheet_names = [
    'Отчет о продажах ИП Иванов',
    'Отчет о продажах ИП Петров',
    'Отчет о продажах ИП Сидоров'
]
proprietors = {p: pd.read_excel(xls, sheet_name=p, skiprows=[0]) for p in proprietor_sheet_names}
# %%
# Перевод столбцов
translation_map = {
    # Zadanie 1
    'Номенклатура': 'item_id',
    'ИП': 'proprietor',
    'Заказы, шт.': 'n_orders',
    'Выручка, руб.': 'revenue',
    'Прибыль, руб.': 'profit',
    'Рентабельность, %': 'profitability',
    # Таблицы ИП
    'Бренд': 'brand',
    'Предмет': 'type',
    'Сезон': 'season',
    'Коллекция': 'collection',
    'Наименование': 'description',
    'Размер': 'size',
    'Склад': 'warehouse',
    'шт': 'n_arrived',
    'себестоимость': 'prime_price_arrived',
    'шт.1': 'n_ordered',
    'себестоимость.1': 'prime_price_ordered',
    'Выкупили, шт': 'n_bought',
    'Выкупили, руб': 'price_bought',
    'Текущий остаток, шт': 'remain_bought',
    # Справочник
    'Категория': 'category',
    'Фиксированные затраты, руб./шт.': 'prime_price',
}
reversed_translation_map = {v: k for k, v in translation_map.items()}
items = (
    items
    .rename(columns=translation_map)
)
items
# %%
# Объединим все таблицы продавцв в одну
sales = pd.DataFrame()
for proprietor_name in proprietors:
    sales = pd.concat([
        sales,
        proprietors[proprietor_name].assign(proprietor=proprietor_name)
    ])
sales = (
    sales
    .rename(columns=translation_map)
    .reset_index()
)
# %% [markdown]
# ## 1.1. Определить к какому ИП относится номенклатура.
# Примечание: если номенклатура не встречается ни в одном из отчетов, в поле «ИП» поставить прочерк.
# %%
# Проверка пересечений
for first, second in combinations(proprietor_sheet_names, 2):
   display(
       np.intersect1d(
           proprietors[first]['Номенклатура'],
           proprietors[second]['Номенклатура']
       )
   )
# Есть одна номенкулатура учтенная у двух ИП
duplicate = np.intersect1d(proprietors['Отчет о продажах ИП Иванов']['Номенклатура'], proprietors['Отчет о продажах ИП Петров']['Номенклатура'])
display(items[items['item_id'].isin(duplicate)])
test_order = items[items['item_id'].isin(duplicate)]['item_id']
display(sales.loc[lambda x: x['item_id'].isin(test_order)])
# %% [markdown]
# Было обнаружено, что одна из номенклатур присутствует сразу у двух ИП. Ситуация является неордиарной, поскольку наблюдается лишь у одного номера. Алгоритм действий для такого случая в задании не описан и нет возможности уточнить. Было принято решение продублировать проблемный номер номенклатуры, потому что таким образом делается меньше допущений и проще внесение исправлений.
# %%
prefix = 'Отчет о продажах'
fill_strat = {'proprietor': '_'}
items = (
    items
    .drop(columns='proprietor')
    .merge(sales[['item_id', 'proprietor']], how='left', on='item_id')
    .drop_duplicates()
    .assign(
        proprietor=lambda x: x['proprietor'].str.removeprefix(prefix)
    )
    .fillna(fill_strat)
)
items
# %%
# Проверка проблемной номенклатуры
items[items['item_id'].isin(duplicate)]
# %%
# Индекс - номенклатура для удобства
items = items.set_index('item_id')
# Только релевантные номенклатуры
sales = (
    sales
    .loc[
        lambda x: x['item_id'].isin(items.index.values)
    ]
)
# %% [markdown]
# ## 1.2. Посчитать количество заказов по каждой номенклатуре.
# Дополнительные сведения для выполнения задания:
# - данные по заказам представлены в Отчетах о Продажах по трем ИП в столбцах «Заказано, шт.»;
# - если ни в одном отчете о продажах нет информации по номенклатуре, то количество заказов по такой номенклатуре равняется нулю;
# - так как отчет о продажах может содержать несколько строк по одной номенклатуре, важно считать сумму заказов по всем строкам, в которых указана номенклатура .
# %%
fill_strat={'n_orders': 0}
n_orders = (
    sales
    .groupby('item_id')
    .agg({'n_ordered': ['sum']})
)
items['n_orders'] = n_orders
items = items.fillna(fill_strat)
items
# %% [markdown]
# ## 1.3. Посчитать выручку по каждой номенклатуре.
# Дополнительные сведения для выполнения задания:
# - в Отчете о Продажах по трем ИП нет информации о выручке, но есть столбцы «Заказано, себестоимость», которые в контексте отчетов по продажам представляют собой выручку за вычетом комиссии WB (17% от выручки), т.е. «Заказано, себестоимость» составляет 83% от выручки.
# %%
fill_strat={'revenue': 0.0}
revenue = (
    sales
    .groupby('item_id')
    .agg({'prime_price_ordered': ['sum']})
    # полная выручка без комиссии
    .apply(lambda x: x/0.83)
    .fillna(fill_strat)
)
items['revenue'] = revenue
items = items.fillna(fill_strat)
items
# %% [markdown]
# ## 1.4. Посчитать прибыль по каждой номенклатуре.
# Дополнительные сведения для выполнения задания:
# - исходные данные: выручка, полученная в предыдущем пункте, таблица себестоимости и справочник;
# - Прибыль=Выручка-Затраты;
# - Затраты включают:
# А) фиксированные затраты (зависят не от цены товара, а от количества),
# Б) налог (ИП Иванов – 1%, ИП Петров – 3%, ИП Сидоров – 5%),
# В) комиссию (17%).
# Примечание: налог и комиссия вычисляются как процент от выручки; если фиксированные затраты не указаны для какой-то из категорий, то задаем их равными минимальным фикс. затратам из таблицы с себестоимостями.
# %%
prime_price_sheet_name = 'Себестоимость'
prime_price_list = (
    pd.read_excel(xls, sheet_name=prime_price_sheet_name)
    .rename(columns=translation_map)
)

reference_sheet_name = 'Справочник'
reference = (
    pd.read_excel(xls, sheet_name=reference_sheet_name)
    .rename(columns=translation_map)
)

# %%
fill_strat={'profit': 0.0}
prefix = 'Отчет о продажах '
tax_ref = {
    'ИП Иванов': 0.01,
    'ИП Петров': 0.03,
    'ИП Сидоров': 0.05
}       
profit = (
    sales
    .merge(reference, on='item_id', how='left')
    .merge(prime_price_list, on='category', how='left')
    .assign(
        tax=lambda x: x['proprietor'].apply(lambda x: tax_ref[x.removeprefix(prefix)]),
        # 17% уже учтены в "Заказано, себестоимость"
        revenue=lambda x: x['prime_price_ordered'] - (x['prime_price'] * x['n_ordered']) - (x['prime_price_ordered'] * x['tax'])
    )
    .groupby('item_id')
    .agg({'revenue': ['sum']})
)
items['profit'] = profit
items = items.fillna(fill_strat)
items
# %% [markdown]
# ## 1.5. Посчитать рентабельность продаж по каждой номенклатуре. (Рентабельность – соотношение прибыли к выручке; в процентах).
# %%
fill_strat={'profitability': 0.0}
items = (
    items
    .assign(
        profitability=lambda x: x['profit']/x['revenue']
    )
)
items = items.fillna(fill_strat)
items
# %% [markdown]
# ## 1.6. Выполнить экспорт получившейся таблицы в формате xlsx, название файла «Задание 1», название листа «Таблица».
out_filename = 'Задание 1.xlsx'
out_sheet_name = 'Таблица'
(
    items
    .reset_index()
    .rename(columns=reversed_translation_map)
    .to_excel(out_filename, sheet_name=out_sheet_name, index=False)
)
# %% [markdown]
# ## 1.7. Построить сводную таблицу (в Python, не в Excel): по строкам – индивидуальные предприниматели, по столбцам сумма заказов, выручки и прибыли.
items.pivot_table(index='proprietor', values=['n_orders', 'revenue', 'profit'], aggfunc='sum')