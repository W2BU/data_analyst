# В архиве во вложении данные по выдачам кредитов и платежам: плановым и фактическим. Данные актуальны на 08.12.2022. Проанализируйте характер поведения клиентов с точки зрения просрочки: какая динамика просрочки, наблюдается ли рост или снижение?

# %% [markdown]
# # Столбцы
# order_id – номер заявки<br>
# created_at - дата создания заявки<br>
# put_at - дата выдачи<br>
# closed_at - дата закрытия<br>
# issued_sum - сумма выдачи<br>
# plan_at - дата планового платежа<br>
# plan_sum_total - сумма планового платежа (накопленным итогом)<br>
# paid_at - дата фактического платежа<br>
# paid_sum - сумма фактического платежа<br>

# %% [markdown]
# # Определения
#
# **Просрочка**— это нарушение должником сроков и/или объёмов исполнения обязательств, предусмотренных договором (графиком платежей).
#
# Уточним определение, применительно к данному исследованию
#
# **Просрочка по плажету**(далее Просрочка)<br>
# Просрочкой по платежу будем называть *недостаток средств* по счету заявки после даты планового платежа.
#
# **Недостаток средств**<br>
# В день плановой даты накопленный итог больше, чем сумма всех платежей. То есть сумма всех платежей не соответствует предъявленным обязательствам на дату.

# %% [markdown]
# # Уточнения
# * Условия расчета суммы планового платежа не предоставлены, поэтому будем считать, что если заявка закрыта до следующей плановой даты платежом меньше планового, то обязательства по ней считаются исполненными в полной мере. Иначе говоря, для закрытых до планового срока заявок проценты расчитаны корректно и выплачены в полной мере.
#
# * Столбцы с денежными единицами имеют тип данных float, что может вести к ошибкам при вычислениях(знаменитое 0.1 + 0.2 != 0.3). Типы данных библиотеки numpy не предоставляют подходящих вариантов для выражения денежных единиц. Есть два способа решения этой проблемы:
#     1. Считать все числа меньше 0.01 за 0
#     2. Округлить все числа до двух знаков после запятой, умножить на 100 и перевести в целочиленный тип. В таком случае все незначительные числа(около e-13) будут выражены как 1 или 2. Погрешность составит менее 10 копеек.
#
#     Задача не уточняет допустимую погрешность в денежных суммах, поэтому во избежание лишних допущений выбран первый способ. Для второго просто представлен код конвертации

# %% [markdown]
# # Обработка таблиц и данных

# %% [markdown]
# ## Библиотеки
# %%
%matplotlib inline
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import hmean
# %%
plt.rcParams['figure.figsize'] = (8, 4)
sns.set_style('white')
# %% [markdown]
# ## Обзор таблиц
# %%
data_dir = Path.cwd() / 'task_2_data'
dfs = {
    str(data_file.stem): pd.read_csv(data_file)
    for data_file in data_dir.iterdir()
}
# %%
for name in dfs:
    print('\n' + '*' * 10 + name.upper() + '*' * 10)
    print(dfs[name].head())
    print()
    print(dfs[name].info())
# %% [markdown]
# В таблице orders лишь уникальные order_id
# %%
dfs['orders']['order_id'].nunique() == dfs['orders'].shape[0]
# %% [markdown]
# Для полей с временем установим тип данных datetime
# %%
orders = dfs['orders']
payments = dfs['payments']
plan = dfs['plan']
orders[['created_at', 'put_at', 'closed_at']] = orders[
    ['created_at', 'put_at', 'closed_at']
].apply(pd.to_datetime)
payments[['paid_at']] = payments[['paid_at']].apply(pd.to_datetime)
plan[['plan_at']] = plan[['plan_at']].apply(pd.to_datetime)
# %% [markdown]
# Отсечем заявки выданные после релевантной даты (2022-08-12)
# %%
relevancy_date = pd.Timestamp('2022-08-12')
orders = (
    orders
    .loc[lambda x: x['put_at'] <= relevancy_date]
)
# %% [markdown]
# Для полей с денежными значениями избавимся от ошибок плавающей точки, следующим образом:
# * округлим до 2го числа после точки
# * умножим на 100
# * переведем в целочисленный тип
# %%
# def to_money_type(x):
#     return round(x, 2) * 100

# orders[['issued_sum']] = orders[['issued_sum']].apply(to_money_type).astype(int)
# %% [markdown]
# ## Примеры данных
# %%
# Закрыт заранее одним платежом
order_id = 400005838
# order_id = 400014289

# Закрыт полностью досрочно
# order_id = 400001732
# order_id = 400007915

# Ошибка плавающей точки
# order_id = 400564695

# Много просрочек
# order_id = 400039450

# Источники резкого скачка
# order_id = 414262167
# order_id = 413853839
# order_id = 414201755
# order_id = 413911250
# order_id = 414305554
# order_id = 414288881
# order_id = 429430737

display(orders[orders['order_id'] == order_id])
display(plan[plan['order_id'] == order_id])
display(payments[payments['order_id'] == order_id])
# %% [markdown]
# ## Исправление ошибок в данных
# %% [markdown]
# В ходе исследования в данных были найдены неточности в данных, выраженные несоответствием порядков значений выданной и запланированной сумм. Несоответсвие имеет закономерный характер и характеризуется 100-кратным различием. Подобное может быть вызвано намеренным изменением данных с целью отметки их источника, либо ошибками при выгрузке данных денежных значений из базы.
# %%
invalid_idx = (
    plan
    .merge(orders, on='order_id')
    .loc[lambda x: (x.plan_sum_total / x.issued_sum) > 10]
    .index
)

plan.loc[invalid_idx, ['plan_sum_total']] = (
    plan.loc[invalid_idx, ['plan_sum_total']] / 100
)

# %% [markdown]
# # Анализ
# %% [markdown]
# ## Анализ таблицы orders
# %%
rus_names = {True: 'Закрытый', False: 'Незакрытый'}
data = (
    orders
    .assign(
        is_closed=lambda x: ~x['closed_at'].isna(),
        put_at_norm=lambda x: x['put_at'].dt.normalize(),
    )
    .groupby([pd.Grouper(key='put_at_norm', freq='D'), 'is_closed'])
    .agg({'order_id': 'nunique'})
    .reset_index()
    .pivot(index='put_at_norm', columns='is_closed', values='order_id')
    .rename(columns=rus_names)
)
ax = data.plot(y=['Закрытый', 'Незакрытый'])

plt.ylabel('Количество выданных заявок')
plt.xlabel('Дата выдачи')
plt.legend(loc='upper left')
plt.suptitle('Динамика новых выданных заявок')
# %%
rus_names = {True: 'Закрытый', False: 'Незакрытый', 'total': 'Общее'}
group_frequency = '15D'
data = (
    orders
    .assign(
        is_closed=lambda x: ~x['closed_at'].isna(),
        put_at_norm=lambda x: x['put_at'].dt.normalize(),
    )
    .groupby([pd.Grouper(key='put_at_norm', freq=group_frequency), 'is_closed'])
    .agg({'order_id': 'nunique'})
    .reset_index()
    .pivot(index='put_at_norm', columns='is_closed', values='order_id')
    .rename(columns=rus_names)
    .assign(total=lambda x: x['Закрытый'] + x['Незакрытый'])
    .rename(columns=rus_names)
    .sort_values(by='Общее', ascending=False)
)
ax = sns.barplot(data, x='Общее', y='put_at_norm', label='Общее')
ax = sns.barplot(data, x='Незакрытый', y='put_at_norm', label='Незакрытый')

plt.suptitle('Количество незакрытых заявок от общего числа за период')
plt.ylabel('')
# %%
data = orders['issued_sum'].rename('Выданная сумма')
ax = data.plot(kind='box')
plt.suptitle('Распределение выданной суммы')
# %% [markdown]
# Выбросы предыдущего графика
# %%
def bound(x):
    iqr = x.quantile(0.75) - x.quantile(0.25)
    return x.quantile(0.75) + 1.5 * iqr
data = orders.loc[lambda x: x['issued_sum'] > bound(x['issued_sum'])]
# %% [markdown]
# Количество выбросов
# %%
display(data.shape[0])
# %% [markdown]
# Выбросы начинаются с суммы выдачи
# %%
display(data['issued_sum'].min())
# %%
data = (
    orders
    .assign(
        is_closed=lambda x: ~x['closed_at'].isna(),
        put_at_norm=lambda x: x['put_at'].dt.normalize(),
    )
    .groupby([pd.Grouper(key='put_at_norm', freq='D'), 'is_closed'])
    .agg({'order_id': 'nunique'})
    .reset_index()
    .assign(
        is_closed=lambda x: x['is_closed'].map(
            {True: 'Закрытый', False: 'Незакрытый'}
        )
    )
    .pivot(index='put_at_norm', columns='is_closed', values='order_id')
    .cumsum()
)
ax = data.plot()

for _, value in data.iloc[-1].items():
    ax.annotate(
        text=f'{value} заявок',
        xy=(relevancy_date + pd.Timedelta(-1, 'd'), value),
        xycoords='data',
        xytext=(10, -30),
        textcoords='offset points',
        arrowprops={'color': 'black', 'arrowstyle': '->'},
    )

plt.ylabel('Общее количество выданных заявок к дате')
plt.xlabel('Дата подсчета')
plt.legend()
plt.suptitle('Общее количество выданных заявок')
# %% [markdown]
# Исследование сроков закрытия
# %%
data = (
    orders
    .loc[lambda x: ~x['closed_at'].isna()]
    .assign(
        time_to_close=lambda x: (x['closed_at'] - x['put_at']).dt.days
    )
    ['time_to_close']
)
data[data < 0] = 0
ax = data.hist(bins=15, grid=False)
ax.bar_label(ax.containers[0])

plt.suptitle('Распределение заявок по количеству дней c выдачи до закрытия')
plt.xlabel('Дней с выдачи до закрытия')
plt.ylabel('Количество заявок')
# %%
data = (
    orders
    .loc[lambda x: ~x['closed_at'].isna()]
    .assign(
        time_to_close=lambda x: (x['closed_at'] - x['put_at']).dt.days
    )
    ['time_to_close']
)
data[data < 0] = 0
bins = [0, 1, 2, 3, 4, 7, 15, 22, 29, 50, data.max()]
tick_labels = [f'{bins[i]}' for i in range(4)]
tick_labels.extend([f'{bins[i]}-{bins[i+1] - 1}' for i in range(4, len(bins)-1)])
tick_labels[-1] = f'{bins[-2]} - {bins[-1]}'
hist, bin_edges = np.histogram(data, bins)
fig, ax = plt.subplots()
ax.bar(
    range(len(hist)),
    hist,
    width=1,
    tick_label=tick_labels
)
ax.bar_label(ax.containers[0])

plt.suptitle('Распределение заявок по количеству дней c выдачи до закрытия')
plt.xlabel('Дней с выдачи до закрытия')
plt.ylabel('Количество заявок')
# %%
print(tick_labels)
# %%
data.describe()
# %% [markdown]
# 90ый персентиль сроков закрытия
# %%
data.quantile(0.90)
# %% [markdown]
# ## **Заключение по разделу**
# * Можно вывести, что на пять закрытых заявок приходится одна с продолжительной задолженностью
# * Рассматриваемый период характеризуется линейным ростом заявок
# * Суммы начиная с 21550 руб являются нетипичными для выдачи
# * Половина от общего числа закрытых заявок погашаются не более чем через 17 дней после выдачи 
# * Треть закрытых заявок погашается не более чем за 42 дня
# * 90% закрытых заявок погашаются не более чем за 85 дней, что соответствует приблизительно 5 плановым платежам
# * В целом прослеживается склонность к погашению не ранее чем через неделю после выдачи
# %% [markdown]
# ## Подсчет итогов к каждому запланированному платежу
# %%
closed_orders = (
    orders
    .loc[lambda x: ~x['closed_at'].isna()]['order_id']
    .values
)

fill_strategy = dict(
    n_payments_made=0,
    paid_sum=0,
)

planned_payments = (
    plan
    .assign(
        n_plan_payment=lambda x: x.groupby('order_id')['plan_at'].transform( 'cumcount') + 1
    )
    .merge(orders, how='right', on='order_id')
    .merge(
        (
            payments.assign(
                n_payments_made=lambda x: x.groupby('order_id')['paid_at'].transform('cumcount') + 1
            )
        ),
        how='left',
        on='order_id',
    )
    .fillna(value=fill_strategy)
    # Необходимо учесть заявки по которым вообще нет платежей
    .loc[
        lambda x: (x['paid_at'].dt.date <= x['plan_at'].dt.date) | (x['paid_at'].isna())
    ]
    .assign(
        paid_to_date=lambda x: x.groupby(['order_id', 'plan_at'])[
            'paid_sum'
        ].transform('sum'),
        plan_to_paid_diff=lambda x: x['plan_sum_total'] - x['paid_to_date'],
        issued_to_paid_diff=lambda x: (x['issued_sum'] - x['paid_to_date']),
        is_closed=lambda x: x['order_id'].isin(closed_orders),
        is_overdue=lambda x: x['plan_to_paid_diff'] > 0.01,
    )
    .astype({'n_payments_made': 'int64'})
)
planned_payments
# %% [markdown]
# Столбцы новой таблицы planned_payments:<br>
# **n_plan_payment** - порядковый номер планового платежа<br>
# **n_payments_made** - количество платежей до планового<br>
# **paid_to_date** - сумма платежей до планового<br>
# **plan_to_paid_diff** - разница между суммой совершенных к дате платежей и плановым. Положительная разница означает наличие задолженности<br>
# **issued_to_paid_diff** - разница выданной суммой и суммой совершенных к дате платежей. Положительное значение - банк недополучил денег, отрицательное - банк в плюсе<br>
# **is_closed** - является ли заявка закрытой<br>
# **is_overdue** - является ли плановый платеж просроченным<br>
# %%
# Каждому плановому платежу соответствует последний совершенный
last_payment_to_plan = (
    planned_payments
    .groupby(by=['order_id', 'plan_at'])
    .last()
    .reset_index()
)
last_payment_to_plan
# %% [markdown]
# ## Заявки без платежей
# %%
orders_with_no_payments = (
    planned_payments
    .loc[lambda x: x['paid_at'].isna()]
)
orders_with_no_payments
# %% [markdown]
# Количество заявок без платежей
# %%
len(orders_with_no_payments['order_id'].unique())
# %% [markdown]
# Доля заявок без платежей от общего количества
# %%
len(orders_with_no_payments['order_id'].unique()) / len(orders)
# %% [markdown]
# Выданная сумма на заявках без платежей
# %%
data = (
    orders_with_no_payments
    .groupby(by='order_id')
    .agg('first')['issued_sum']
)
data2 = orders['issued_sum']
ax = pd.DataFrame({'Заявки без платежей': data, 'Все заявки': data2}).plot(
    kind='box'
)
plt.ylabel('Выданная сумма')
# %% [markdown]
# ## Заявки погашенные одним платежом
# %% [markdown]
# Среди записей о заявках особенно выделяется группа, характеризуемая погашением единственной оплатой. Стоит дать характиристку этой группе с целью формирования стратегии по обращению с такими заявками, а именно: является ли такое поведение допустимым для банка и возможно ли его поощрять.
# %%
one_payment_and_in_advance = (
    last_payment_to_plan
    .groupby('order_id')
    .last()
    .loc[
        lambda x: (x['n_plan_payment'] == 1)
        & (x['issued_to_paid_diff'] < 0)
        & (x['is_closed'])
    ]
)
one_payment_and_in_advance
# %%
data = (
    one_payment_and_in_advance
    .assign(time_to_close=lambda x: (x['closed_at'] - x['put_at']).dt.days)
    ['time_to_close']
    .value_counts()
    .sort_index()
)
ax = data.plot(kind='bar')
ax.bar_label(ax.containers[0])
plt.suptitle('Через сколько дней после выдачи был совершен единственный платеж по заявке')
plt.xlabel('Дней после выдачи')
plt.ylabel('Количество заявок')
# %% [markdown]
# Количество заявок погашенных одним платежом
# %%
len(one_payment_and_in_advance)
# %% [markdown]
# Доля заявок погашенных одним платежом среди всех
# %%
len(one_payment_and_in_advance) / len(orders)
# %%
one_payment_and_in_advance_pct_values = (
    one_payment_and_in_advance
    .assign(
        pct_isp_diff=lambda x: np.abs(x['issued_to_paid_diff']) / x['issued_sum'],
        pct_ptp_diff=lambda x: round( np.abs(x['paid_sum']) / x['plan_sum_total'], ndigits=3),
    )
    .loc[:, ['pct_isp_diff', 'pct_ptp_diff']] 
)
one_payment_and_in_advance_pct_values
# %%
rus_names = {
    'pct_isp_diff': 'Прибыль от выданной суммы',
    'pct_ptp_diff': 'Доля от планового платежа',
}
# %%
data = (
    one_payment_and_in_advance_pct_values
    .rename(columns=rus_names)
)
ax = data.plot(kind='box')
plt.suptitle('Специфика заявок погашенных досрочно одним платежом')
# %% [markdown]
# Выбросы boxplot
# %%
# ??? Либо метки в данных, либо как-то неправильно оформленные заявки
(
    one_payment_and_in_advance_pct_values
    .loc[lambda x: (x['pct_isp_diff'] > 0.2) | (x['pct_ptp_diff'] < 0.8)]
)
# %%
data = (
    one_payment_and_in_advance_pct_values
    .loc[lambda x: x['pct_isp_diff'] < 0.2]
    .rename(columns=rus_names)
    .iloc[:, 0]
)
sns.histplot(data, kde=True, binrange=(0, 0.2), bins=8)
plt.suptitle('Распределение прибылей от выданной суммы')
plt.xlabel('Прибыль от выданной суммы(%)')
plt.ylabel('Количество заявок')
# %%
data = (
    one_payment_and_in_advance_pct_values
    .loc[lambda x: x['pct_ptp_diff'] > 0.8]
    .rename(columns=rus_names)
    .iloc[:, 1]
)
sns.histplot(data, kde=True, binrange=(0.8, 1), bins=8)
plt.suptitle('Распределение долей от предстоящего планового платежа')
plt.xlabel('Доля от планового платежа(%)')
plt.ylabel('Количество заявок')
# %% [markdown]
# Среднее гармоническое
# %%
(
    one_payment_and_in_advance_pct_values
    .rename(columns=rus_names)
    .agg(hmean)
)
# %% [markdown]
# Среднее арифметическое. Выбросы исключены.
# %%
(
    one_payment_and_in_advance_pct_values
    .loc[lambda x: (x['pct_isp_diff'] < 0.2) | (x['pct_ptp_diff'] > 0.8)]
    .rename(columns=rus_names)
    .agg('mean')
)
# %%
(
    one_payment_and_in_advance_pct_values
    .rename(columns=rus_names)
    .describe()
)
# %% [markdown]
# ## **Заключение по разделу**
# * Заявки погашенные одним досрочным платежом составляют 32 процента от всех оформленных заявок, что является значительной долей.
# * Абсолютное большинство выделенных заявок прибыльные не более чем 15% от суммы выдачи, и выплачиваются на сумму не менее чем 85% от запланированной к первому платежу.
# * Несмотря на совпадающие медиану и среднее, распределения не являются нормальными
# %% [markdown]
# ## Исследование незакрытых заявок
# %%
unclosed_overdue_last_payment = (
    last_payment_to_plan
    .loc[lambda x: x['is_overdue'] & ~x['is_closed']]
    .sort_values(['order_id', 'plan_at'])
    .groupby('order_id')
    .last()
)
unclosed_overdue_last_payment
# %%
ax = (
    unclosed_overdue_last_payment
    ['n_plan_payment']
    .value_counts()
    .sort_index()
    .plot(kind='bar')
)
ax.bar_label(ax.containers[0])
plt.suptitle('Номер последнего запланированного платежа на незакрытых заявках')
# %% [markdown]
# Выбросы предыдущего графика
# %%
(
    unclosed_overdue_last_payment
    .loc[lambda x: x['n_plan_payment'].isin([14, 16, 25])]
)
# %%
ax = (
    unclosed_overdue_last_payment
    ['n_payments_made']
    .value_counts()
    .sort_index()
    .plot(kind='bar')
)
ax.bar_label(ax.containers[0])
plt.suptitle('Количество платежей на незакрытых заявках')
# %%
data = (
    unclosed_overdue_last_payment
    .assign(
        pct_of_issued=lambda x: x['paid_sum'] / x['issued_sum']
    )
    ['pct_of_issued']
)
ax = data.plot(kind='hist', bins=np.arange(0, 1.1, 0.1))
plt.suptitle('Доля выплаченной суммы от выданной')
# %% [markdown]
# Сумма невыплаченных средств на незакрытых заявках к последнему запланированному платежу
# %%
rus_names = {
    'issued_to_paid_diff': 'Сумма невыплаченных средств',
    'plan_to_paid_diff': 'Сумма невыплаченных средств с учетом процентов',
}

(
    unclosed_overdue_last_payment.agg(
        {'issued_to_paid_diff': 'sum', 'plan_to_paid_diff': 'sum'}
    ).rename(rus_names)
)
# %% [markdown]
# ## **Заключения по разделу**
# * Незакрытые заявки распланированы не более чем на 13 периодов
# * На незакрытых заявках было потеряно 14 млн
# * Незакрытые заявки выплачиваются не более чем на половину от выданной суммы
# %% [markdown]
# ## Просроченные платежи
# %%
# Открытые заявки и заявки погашенные заранее одним платежом рассмотрены в отдельных разделах
overdue_payments = (
    planned_payments
    .loc[
        lambda x: x['is_closed'] &
         x['is_overdue'] &
         ~x['order_id'].isin(one_payment_and_in_advance.index.values)
    ]
    # Оставим только уникальные плановые платежи
    .groupby(['order_id', 'plan_at'])
    .last()
    .reset_index()
)
overdue_payments
# %% [markdown]
# Количество просроченных плановых платежей
# %%
overdue_payments.shape[0]
# %% [markdown]
# Доля просроченных плановых платежей от всех запланированных
# %%
round(overdue_payments.shape[0] / plan.shape[0], 4)
# %%
data_monthly = (
    overdue_payments
    .groupby([pd.Grouper(key='plan_at', freq='ME')])
    .agg({'order_id': 'count'})
)
data_daily = (
    overdue_payments
    .groupby([pd.Grouper(key='plan_at', freq='D')])
    .agg({'order_id': 'count'})
)
fig, axes = plt.subplots(2, 1, figsize=(8, 6))
data_monthly.plot(ax=axes[0], sharex=True)
data_daily.plot(ax=axes[1], sharex=True)
axes[0].set_title('Месячная динамика')
data_monthly.reset_index()
xmax, ymax = data_monthly.idxmax().values[0], data_monthly.max().values[0], 
axes[0].annotate(
    text=f'{ymax} платежей просрочено',
    xy=(xmax, ymax),
    xycoords='data',
    xytext=(-20, -60),
    textcoords='offset points',
    arrowprops={'color': 'black', 'arrowstyle': '->'}
)
axes[1].set_title('Ежедневная динамика')
axes[1].set_xlabel('')
for ax in axes:
    ax.legend().set_visible(False)
fig.suptitle('Динамика количества просроченных платежей')
fig.supxlabel('Дата подсчета')
fig.supylabel('Количество просроченных платежей')
# %%
data = (
    overdue_payments
    .groupby(by='n_plan_payment')
    .agg({'order_id': 'nunique'})
)
ax = data.plot(kind='bar')
ax.bar_label(ax.containers[0])

plt.suptitle('Какой из плановых платежей был просрочен')
plt.xlabel('Номер платежа')
plt.ylabel('Количество просроченых платежей')
# %%
data = overdue_payments['plan_to_paid_diff']
fig, ax = plt.subplots(figsize=(3,6))
sns.violinplot(data, ax=ax)
plt.suptitle('Распределение недоплаченной суммы')
plt.ylabel('Сумма задолженности')
plt.xlabel('Платежи с задолженностью')
# %% [markdown]
# Статистики суммы задолженности
# %%
data.describe()
# %% [markdown]
# 90ый персентиль
# %%
data.quantile(0.90)
# %%
data = (
    overdue_payments
    .assign(
        pct_of_plan=lambda x: x['plan_to_paid_diff'] / x['plan_sum_total']
    )
    ['pct_of_plan']
)
fig, ax = plt.subplots(figsize=(3,6))
sns.violinplot(data, ax=ax)
plt.suptitle('Какую долю от запланированной суммы составляет задолженность')
plt.ylabel('Доля от запланированной суммы')
plt.xlabel('Платежи с задолженностью')
# %% [markdown]
# Статистики доли от запланированной суммы
# %%
data.describe()
# %% [markdown]
# 90ый персентиль
# %%
data.quantile(0.90)
# %% [markdown]
# ## **Заключения по разделу**
# * Просроченные платежи составляют около 5 процентов от всех запланированных
# * Больше всего запланированных платежей было просрочено в августе. Итог составил 6596 платежей
# * Сумма задолженности половины запланированных платежей не превышает 1500 руб, а 90% - 4800 руб
# * В долях от запланированной суммы указанные цифры составляют 33, и 64 процента соответственно
# * Есть явная тенденция к неуплате примерно трети от запланированной суммы