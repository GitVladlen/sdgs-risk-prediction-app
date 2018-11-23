# -*- coding: utf-8 -*-
import os
import json

from flask import Flask, render_template, g

app = Flask(__name__)

class DataManager(object):
    s_computed_values = None

    @staticmethod
    def setComputedValues(values):
        DataManager.s_computed_values = values

    @staticmethod
    def getComputedValues():
        return DataManager.s_computed_values

# = prognose ==========================================================
def give_forcast(forecast_prev, value_prev, alpha):
    forecast_prev_error = value_prev - forecast_prev
    return forecast_prev + alpha * forecast_prev_error

def simple_exp_smoothing(real_data, labels, alpha):
    forecast_error = 0
    forecast_data = {}
    forecast_prev = None
    value_prev = None

    forecast_prev_error = None

    for label in labels:
        value = real_data.get(label)

        if forecast_prev is None and value_prev is None:
            forecast_prev = value
            value_prev = value
            continue

        forecast_cur = give_forcast(forecast_prev, value_prev, alpha)
        forecast_data[label] = forecast_cur

        forecast_prev = forecast_cur
        value_prev = value

    print("""
 SES:
  DATA = {}
  LABELS = {}
  FORECAST = {}""".format(
        json.dumps(real_data, indent=4),
        labels,
        json.dumps(forecast_data, indent=4)
        ))

    return forecast_data, forecast_prev, value_prev


# = service ===========================================================
def readData(filename):
    filepath = os.path.join("static", "data", filename)

    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)

    return data

def writeData(filename, data):
    filepath = os.path.join("static", "data", filename)

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def checkData(data, **filters):
    for filter_name in filters:
        filter_value = filters[filter_name]

        value = data.get(filter_name)
        if value != filter_value:
            return False
    return True

def findInData(data, **filters):
    for elem in data:
        if checkData(elem, **filters) is True:
            return elem
    return None

def selectFromData(data, **filters):
    selected = []
    for elem in data:
        if checkData(elem, **filters) is True:
            selected.append(elem)
    return selected

def calcComputedValues():
    import random

    keys = ["2015", "2020", "2025", "2030"]

    values = readData("values.json")

    computed_values = []

    for value in values:
        computed_value = dict()
        computed_value.update(value)

        vsum = 0
        for key in keys:
            vsum += value[key]

        avg = vsum / len(keys)

        dsum = 0
        for key in keys:
            dsum += abs(avg - value[key])

        davg = dsum / len(keys)

        for key in ["2015", "2020", "2025", "2030"]:
            computed_value[key] = round(computed_value[key] + random.uniform(-davg, davg), 1)

        computed_values.append(computed_value)

    return computed_values

def generateComputedValues(values, keys, gen_from_key, gen_for_keys):
    import random

    gen_values = []

    for value in values:
        get_from_value = value[gen_from_key]
        gen_value = dict()
        for key in ["GoalID", "TaskID", "IndicatorID"]:
            gen_value[key] = value[key]

        vsum = 0
        for key in keys:
            vsum += value[key]

        avg = vsum / len(keys)

        dsum = 0
        for key in keys:
            dsum += abs(avg - value[key])

        prev = None
        is_decay = False
        for key in keys:
            if prev is not None:
                diff = prev - value[key]
                if diff > 0:
                    is_decay = True
                    break
            prev = value[key]

        print ("{GoalID}.{TaskID}.{IndicatorID} is_decay = {is_decay}".format(
            is_decay=is_decay,
            **value))


        davg = dsum / len(keys)

        prev = get_from_value
        for key in gen_for_keys:
            if key == gen_from_key:
                gen_value[key] = prev
            else:
                # gen_value[key] = round(get_from_value + random.uniform(-davg, davg), 1)
                rand_value = random.uniform(0, davg)
                if is_decay:
                    rand_value = -rand_value
                gen_value[key] = round(prev + rand_value, 1)

            prev = gen_value[key]

        gen_values.append(gen_value)

    return gen_values

# = endpoints =========================================================
def goal(goal_id):
    print (" THIS IS GOAL {}.".format(goal_id))

    goals = readData('goals.json')
    goal = findInData(goals, GoalID=goal_id)

    tasks = readData('tasks.json')
    goal_tasks = selectFromData(tasks, GoalID=goal_id)

    params = dict(
        goal = goal,
        tasks = goal_tasks
    )

    return render_template('goal.html', **params)

def task(goal_id, task_id):
    print (" THIS IS TASK {}.{}.".format(goal_id, task_id))

    goals = readData('goals.json')
    goal = findInData(goals, GoalID=goal_id)

    tasks = readData('tasks.json')
    task = findInData(tasks, GoalID=goal_id, TaskID=task_id)

    indicators = readData('indicators.json')
    task_indicators = selectFromData(indicators, GoalID=goal_id, TaskID=task_id)

    params = dict(
        goal = goal,
        task = task,
        indicators = task_indicators
    )

    return render_template('task.html', **params)

def indicator(goal_id, task_id, indicator_id):
    print (" THIS IS INDICATOR {}.{}.{}.".format(goal_id, task_id, indicator_id))

    goals = readData('goals.json')
    goal = findInData(goals, GoalID=goal_id)

    tasks = readData('tasks.json')
    task = findInData(tasks, GoalID=goal_id, TaskID=task_id)

    indicators = readData('indicators.json')
    indicator = findInData(indicators, GoalID=goal_id, TaskID=task_id, IndicatorID=indicator_id)

    values = readData("values.json")
    indicator_value = findInData(values, GoalID=goal_id, TaskID=task_id, IndicatorID=indicator_id)

    # computed_values = DataManager.getComputedValues()
    # computed_indicator_value = findInData(computed_values, GoalID=goal_id, TaskID=task_id, IndicatorID=indicator_id)

    real_values = readData("real_values.json")
    real_indicator_value = findInData(real_values, GoalID=goal_id, TaskID=task_id, IndicatorID=indicator_id)

    # dummy risk evaluation
    risk = (goal_id + task_id + indicator_id) % 3 

    # indicator_labels
    def __unique_indicator_labels(_indicator_value):
        _unique_indicator_labels = []
        for _key in _indicator_value:
            if "20" in _key and _key not in _unique_indicator_labels:
                _unique_indicator_labels.append(int(_key))
        _unique_indicator_labels.sort()
        return [str(l) for l in _unique_indicator_labels]

    unique_indicator_labels = __unique_indicator_labels(indicator_value)
    unique_real_indicator_labels = __unique_indicator_labels(real_indicator_value)

    # make prognose
    alpha = 0.5
    forecast_value, forecast_prev, value_prev = simple_exp_smoothing(real_indicator_value, unique_real_indicator_labels, alpha)

    forecast_labels = [str(l) for l in range(2019, 2031)]

    for label in forecast_labels:
        # forecast_cur = give_forcast(forecast_prev, value_prev, alpha)

        forecast_cur = alpha * value_prev + (1-alpha) * forecast_prev

        forecast_value[label] = forecast_cur

        forecast_prev = forecast_cur
        # value_prev = value_prev
    
    # merge all labels
    all_indicator_labels = unique_indicator_labels + unique_real_indicator_labels + forecast_labels

    pre_labels = []
    for label in all_indicator_labels:
        int_label = int(label)
        if int_label not in pre_labels:
            pre_labels.append(int_label)
    pre_labels.sort()

    labels = [str(l) for l in pre_labels]

    print(" >> LABELS: {}".format(labels))

    def __getPlotValuesForLabels(_value, _labels):
        _plot_values = []

        for _label in _labels:
            _plot_value = _value.get(_label, "null")
            _plot_values.append(_plot_value)

        return _plot_values


    indicator_plot_values = __getPlotValuesForLabels(indicator_value, labels)
    real_indicator_plot_values = __getPlotValuesForLabels(real_indicator_value, labels)
    # computed_indicator_plot_values = __getPlotValuesForLabels(computed_indicator_value, labels)



    forecast_plot_values = __getPlotValuesForLabels(forecast_value, labels)

    params = dict(
        goal = goal,
        task = task,
        indicator = indicator,

        labels = labels,

        indicator_value = indicator_value,
        indicator_plot_values = indicator_plot_values,

        real_indicator_value = real_indicator_value,
        real_indicator_plot_values = real_indicator_plot_values,

        forecast_indicator_value = forecast_value,
        forecast_indicator_plot_values = forecast_plot_values,

        # computed_indicator_value = computed_indicator_value,
        # computed_indicator_plot_values = computed_indicator_plot_values,
        
        risk = risk
    )

    return render_template('indicator.html', **params)


@app.route('/goal/<int:goal_id>')
@app.route('/goal/<int:goal_id>/task/<int:task_id>')
@app.route('/goal/<int:goal_id>/task/<int:task_id>/indicator/<int:indicator_id>')
def job(goal_id, task_id=None, indicator_id=None):
    if task_id is None and indicator_id is None:
        return goal(goal_id)
    elif indicator_id is None:
        return task(goal_id, task_id)
    else:
        return indicator(goal_id, task_id, indicator_id)

@app.route('/data/<mode>')
@app.route('/data')
def data(mode=None):
    if mode == "gen":
        generated_values = generateComputedValues(
            readData("values.json"),
            ["2015", "2020", "2025", "2030"],
            "2015",
            ["2015", "2016", "2017", "2018"])

        writeData("real_values.json", generated_values)
    else:
        generated_values = readData("real_values.json")

    return "<pre>{}</pre>".format(json.dumps(generated_values, indent=4))

@app.route('/')
def start():
    if DataManager.getComputedValues() is None:
        computed_values = calcComputedValues()
        DataManager.setComputedValues(computed_values)

    return render_template('goals.html', goals=readData('goals.json'))